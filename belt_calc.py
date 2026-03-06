import math
import tkinter as tk
from tkinter import ttk, messagebox
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple


# ============================================================
# Datenmodell
# ============================================================

@dataclass
class Wheel:
    wid: int
    name: str
    x: float
    y: float
    diameter: float   # Eingabe: bei Pulley gewÃ¼nschter Teilkreis, bei Rolle AuÃŸendurchmesser
    kind: str         # "Pulley" oder "Rolle"

    @property
    def radius(self) -> float:
        return self.diameter / 2.0




@dataclass
class Segment:
    a_idx: int
    b_idx: int
    p1: Tuple[float, float]
    p2: Tuple[float, float]
    length: float
    center_distance: float


@dataclass
class Arc:
    idx: int
    center: Tuple[float, float]
    radius: float
    p_in: Tuple[float, float]
    p_out: Tuple[float, float]
    start_angle: float
    extent_angle: float
    length: float
    mid_point: Tuple[float, float]


@dataclass
class BeltSolution:
    order: List[int]
    segments: List[Segment]
    arcs: List[Arc]
    total_length: float
    centroid: Tuple[float, float]


@dataclass
class DerivedProfile:
    pitch: float
    tooth_height: float
    tooth_top: float
    tooth_root: float
    pulley_teeth: Dict[int, int]
    corrected_pitch_diameters: Dict[int, float]
    max_pitch_deviation: float
    printable_min_tooth_height: float
    printable_min_tooth_root: float
    constraint_pitch_from_height: float
    constraint_pitch_from_root: float


@dataclass
class CenterDistanceCorrection:
    nominal_length: float
    target_length: float
    corrected_length: float
    nominal_belt_teeth_exact: float
    belt_teeth_used: int
    length_delta_before: float
    length_delta_after: float
    position_scale: float
    nominal_wheels: List[Wheel]
    corrected_wheels: List[Wheel]
    corrected_solution: BeltSolution


# ============================================================
# Geometrie / Profilannahmen
# ============================================================

TAU = 2.0 * math.pi

TOOTH_HEIGHT_FACTOR = 1.9 / 5.0
TOOTH_TOP_FACTOR = 1.5 / 5.0
TOOTH_ROOT_FACTOR = 2.4 / 5.0

REFERENCE_PITCH = 5.0
BASE_MIN_PITCH = 2.0
MAX_PITCH = 20.0
MIN_TEETH = 8
MAX_TEETH = 400

DEFAULT_PRINTABLE_MIN_TOOTH_HEIGHT = 3.0
DEFAULT_PRINTABLE_MIN_TOOTH_ROOT = 3.0


def clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


def dist(a: Tuple[float, float], b: Tuple[float, float]) -> float:
    return math.hypot(b[0] - a[0], b[1] - a[1])


def angle_of(a: Tuple[float, float], b: Tuple[float, float]) -> float:
    return math.atan2(b[1] - a[1], b[0] - a[0])


def norm_angle(a: float) -> float:
    while a < 0:
        a += TAU
    while a >= TAU:
        a -= TAU
    return a


def polygon_signed_area(points: List[Tuple[float, float]]) -> float:
    area = 0.0
    n = len(points)
    for i in range(n):
        x1, y1 = points[i]
        x2, y2 = points[(i + 1) % n]
        area += x1 * y2 - x2 * y1
    return area / 2.0


def line_point_distance(point: Tuple[float, float], a: Tuple[float, float], b: Tuple[float, float]) -> float:
    px, py = point
    ax, ay = a
    bx, by = b
    abx = bx - ax
    aby = by - ay
    apx = px - ax
    apy = py - ay
    ab2 = abx * abx + aby * aby
    if ab2 <= 1e-12:
        return math.hypot(px - ax, py - ay)
    t = clamp((apx * abx + apy * aby) / ab2, 0.0, 1.0)
    cx = ax + t * abx
    cy = ay + t * aby
    return math.hypot(px - cx, py - cy)


def tangent_external_both(
    c1: Tuple[float, float],
    r1: float,
    c2: Tuple[float, float],
    r2: float,
) -> List[Tuple[Tuple[float, float], Tuple[float, float]]]:
    dx = c2[0] - c1[0]
    dy = c2[1] - c1[1]
    d = math.hypot(dx, dy)
    if d <= 1e-9:
        return []
    if d < abs(r1 - r2):
        return []

    base = math.atan2(dy, dx)
    val = clamp((r1 - r2) / d, -1.0, 1.0)
    alpha = math.acos(val)

    results = []
    for side in (-1, 1):
        a = base + side * alpha
        p1 = (c1[0] + r1 * math.cos(a), c1[1] + r1 * math.sin(a))
        p2 = (c2[0] + r2 * math.cos(a), c2[1] + r2 * math.sin(a))
        results.append((p1, p2))
    return results


def tangent_internal_both(
    c1: Tuple[float, float],
    r1: float,
    c2: Tuple[float, float],
    r2: float,
) -> List[Tuple[Tuple[float, float], Tuple[float, float]]]:
    dx = c2[0] - c1[0]
    dy = c2[1] - c1[1]
    d = math.hypot(dx, dy)
    if d <= 1e-9:
        return []
    if d <= (r1 + r2):
        return []

    base = math.atan2(dy, dx)
    val = clamp((r1 + r2) / d, -1.0, 1.0)
    alpha = math.acos(val)

    results = []
    for side in (-1, 1):
        a = base + side * alpha
        p1 = (c1[0] + r1 * math.cos(a), c1[1] + r1 * math.sin(a))
        p2 = (c2[0] - r2 * math.cos(a), c2[1] - r2 * math.sin(a))
        results.append((p1, p2))
    return results


def choose_outer_tangent(
    c1: Tuple[float, float],
    r1: float,
    c2: Tuple[float, float],
    r2: float,
    centroid: Tuple[float, float],
) -> Optional[Tuple[Tuple[float, float], Tuple[float, float]]]:
    candidates = tangent_external_both(c1, r1, c2, r2)
    if not candidates:
        return None

    best = None
    best_score = -1e18
    for p1, p2 in candidates:
        mx = (p1[0] + p2[0]) / 2.0
        my = (p1[1] + p2[1]) / 2.0
        score = math.hypot(mx - centroid[0], my - centroid[1])
        if score > best_score:
            best_score = score
            best = (p1, p2)
    return best


def arc_point(center: Tuple[float, float], radius: float, angle: float) -> Tuple[float, float]:
    return center[0] + radius * math.cos(angle), center[1] + radius * math.sin(angle)


def choose_outer_arc(
    center: Tuple[float, float],
    radius: float,
    p_in: Tuple[float, float],
    p_out: Tuple[float, float],
    centroid: Tuple[float, float],
) -> Tuple[float, float, float, Tuple[float, float]]:
    a1 = norm_angle(angle_of(center, p_in))
    a2 = norm_angle(angle_of(center, p_out))

    ccw = (a2 - a1) % TAU
    cw = (a1 - a2) % TAU

    mid_ccw = norm_angle(a1 + ccw / 2.0)
    mid_cw = norm_angle(a1 - cw / 2.0)

    p_mid_ccw = arc_point(center, radius, mid_ccw)
    p_mid_cw = arc_point(center, radius, mid_cw)

    d_ccw = dist(p_mid_ccw, centroid)
    d_cw = dist(p_mid_cw, centroid)

    if d_ccw >= d_cw:
        return a1, ccw, radius * ccw, p_mid_ccw
    return a1, -cw, radius * cw, p_mid_cw



def unit_vec(v: Tuple[float, float]) -> Optional[Tuple[float, float]]:
    n = math.hypot(v[0], v[1])
    if n <= 1e-12:
        return None
    return (v[0] / n, v[1] / n)


def dot(a: Tuple[float, float], b: Tuple[float, float]) -> float:
    return a[0] * b[0] + a[1] * b[1]


def choose_physically_plausible_arc(
    center: Tuple[float, float],
    radius: float,
    p_in: Tuple[float, float],
    p_out: Tuple[float, float],
    centroid: Tuple[float, float],
    incoming_dir: Tuple[float, float],
    outgoing_dir: Tuple[float, float],
) -> Optional[Tuple[float, float, float, Tuple[float, float]]]:
    u_in = unit_vec(incoming_dir)
    u_out = unit_vec(outgoing_dir)
    if u_in is None or u_out is None:
        return None

    a1 = norm_angle(angle_of(center, p_in))
    a2 = norm_angle(angle_of(center, p_out))

    ccw = (a2 - a1) % TAU
    cw = (a1 - a2) % TAU
    mid_ccw = norm_angle(a1 + ccw / 2.0)
    mid_cw = norm_angle(a1 - cw / 2.0)

    p_mid_ccw = arc_point(center, radius, mid_ccw)
    p_mid_cw = arc_point(center, radius, mid_cw)

    t_ccw_in = (-math.sin(a1), math.cos(a1))
    t_ccw_out = (-math.sin(a2), math.cos(a2))
    t_cw_in = (math.sin(a1), -math.cos(a1))
    t_cw_out = (math.sin(a2), -math.cos(a2))

    candidates: List[Tuple[float, Tuple[float, float, float, Tuple[float, float]]]] = []

    align_ccw_in = dot(u_in, t_ccw_in)
    align_ccw_out = dot(u_out, t_ccw_out)
    if align_ccw_in > 0.5 and align_ccw_out > 0.5:
        score_ccw = math.hypot(p_mid_ccw[0] - centroid[0], p_mid_ccw[1] - centroid[1]) + 0.05 * (align_ccw_in + align_ccw_out)
        candidates.append((score_ccw, (a1, ccw, radius * ccw, p_mid_ccw)))

    align_cw_in = dot(u_in, t_cw_in)
    align_cw_out = dot(u_out, t_cw_out)
    if align_cw_in > 0.5 and align_cw_out > 0.5:
        score_cw = math.hypot(p_mid_cw[0] - centroid[0], p_mid_cw[1] - centroid[1]) + 0.05 * (align_cw_in + align_cw_out)
        candidates.append((score_cw, (a1, -cw, radius * cw, p_mid_cw)))

    if not candidates:
        return None
    candidates.sort(key=lambda x: x[0], reverse=True)
    return candidates[0][1]

def sensible_order(wheels: List[Wheel]) -> List[int]:
    if len(wheels) < 2:
        return list(range(len(wheels)))

    cx = sum(w.x for w in wheels) / len(wheels)
    cy = sum(w.y for w in wheels) / len(wheels)

    indexed = list(range(len(wheels)))
    indexed.sort(key=lambda i: math.atan2(wheels[i].y - cy, wheels[i].x - cx))

    points = [(wheels[i].x, wheels[i].y) for i in indexed]
    if polygon_signed_area(points) < 0:
        indexed.reverse()

    return indexed


def points_close(a: Tuple[float, float], b: Tuple[float, float], tol: float = 1e-7) -> bool:
    return abs(a[0] - b[0]) <= tol and abs(a[1] - b[1]) <= tol


def orientation(a: Tuple[float, float], b: Tuple[float, float], c: Tuple[float, float]) -> float:
    return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])


def point_on_segment(a: Tuple[float, float], b: Tuple[float, float], p: Tuple[float, float], tol: float = 1e-9) -> bool:
    if abs(orientation(a, b, p)) > tol:
        return False
    return (
        min(a[0], b[0]) - tol <= p[0] <= max(a[0], b[0]) + tol
        and min(a[1], b[1]) - tol <= p[1] <= max(a[1], b[1]) + tol
    )


def segments_intersect(
    a1: Tuple[float, float],
    a2: Tuple[float, float],
    b1: Tuple[float, float],
    b2: Tuple[float, float],
    tol: float = 1e-9,
) -> bool:
    o1 = orientation(a1, a2, b1)
    o2 = orientation(a1, a2, b2)
    o3 = orientation(b1, b2, a1)
    o4 = orientation(b1, b2, a2)

    if ((o1 > tol and o2 < -tol) or (o1 < -tol and o2 > tol)) and ((o3 > tol and o4 < -tol) or (o3 < -tol and o4 > tol)):
        return True

    if abs(o1) <= tol and point_on_segment(a1, a2, b1, tol):
        return True
    if abs(o2) <= tol and point_on_segment(a1, a2, b2, tol):
        return True
    if abs(o3) <= tol and point_on_segment(b1, b2, a1, tol):
        return True
    if abs(o4) <= tol and point_on_segment(b1, b2, a2, tol):
        return True
    return False


def segments_cross_invalid(a1: Tuple[float, float], a2: Tuple[float, float], b1: Tuple[float, float], b2: Tuple[float, float]) -> bool:
    if not segments_intersect(a1, a2, b1, b2):
        return False
    shared_endpoint = points_close(a1, b1) or points_close(a1, b2) or points_close(a2, b1) or points_close(a2, b2)
    return not shared_endpoint


def segment_clear_of_other_wheels(
    seg_a_idx: int,
    seg_b_idx: int,
    p1: Tuple[float, float],
    p2: Tuple[float, float],
    wheels: List[Wheel],
) -> bool:
    for idx, w in enumerate(wheels):
        if idx in (seg_a_idx, seg_b_idx):
            continue
        d = line_point_distance((w.x, w.y), p1, p2)
        if d < w.radius * 0.98:
            return False
    return True


def build_solution_from_tangents(
    wheels: List[Wheel],
    order: List[int],
    centroid: Tuple[float, float],
    tangent_choices: List[Tuple[Tuple[float, float], Tuple[float, float]]],
) -> Optional[BeltSolution]:
    n = len(order)
    tangents_out: List[Optional[Tuple[float, float]]] = [None] * n
    tangents_in: List[Optional[Tuple[float, float]]] = [None] * n
    segments: List[Segment] = []

    for pos in range(n):
        i = order[pos]
        j = order[(pos + 1) % n]
        p1, p2 = tangent_choices[pos]

        tangents_out[pos] = p1
        tangents_in[(pos + 1) % n] = p2

        if not segment_clear_of_other_wheels(i, j, p1, p2, wheels):
            return None

        segments.append(
            Segment(
                a_idx=i,
                b_idx=j,
                p1=p1,
                p2=p2,
                length=dist(p1, p2),
                center_distance=dist((wheels[i].x, wheels[i].y), (wheels[j].x, wheels[j].y)),
            )
        )

    for i in range(n):
        for j in range(i + 1, n):
            sa = segments[i]
            sb = segments[j]
            if segments_cross_invalid(sa.p1, sa.p2, sb.p1, sb.p2):
                return None

    arcs: List[Arc] = []
    total_length = 0.0
    for pos in range(n):
        idx = order[pos]
        w = wheels[idx]
        p_in = tangents_in[pos]
        p_out = tangents_out[pos]
        if p_in is None or p_out is None:
            return None

        prev_seg = segments[(pos - 1) % n]
        next_seg = segments[pos]
        incoming_dir = (p_in[0] - prev_seg.p1[0], p_in[1] - prev_seg.p1[1])
        outgoing_dir = (next_seg.p2[0] - p_out[0], next_seg.p2[1] - p_out[1])

        arc_data = choose_physically_plausible_arc(
            (w.x, w.y),
            w.radius,
            p_in,
            p_out,
            centroid,
            incoming_dir,
            outgoing_dir,
        )
        if arc_data is None:
            return None
        start_angle, extent_angle, arc_len, mid_point = arc_data

        arcs.append(
            Arc(
                idx=idx,
                center=(w.x, w.y),
                radius=w.radius,
                p_in=p_in,
                p_out=p_out,
                start_angle=start_angle,
                extent_angle=extent_angle,
                length=arc_len,
                mid_point=mid_point,
            )
        )
        total_length += arc_len

    total_length += sum(s.length for s in segments)
    return BeltSolution(
        order=order,
        segments=segments,
        arcs=arcs,
        total_length=total_length,
        centroid=centroid,
    )


def compute_belt_solution(wheels: List[Wheel]) -> BeltSolution:
    if len(wheels) < 2:
        raise ValueError("Mindestens 2 Elemente erforderlich.")

    order = sensible_order(wheels)
    ordered_centers = [(wheels[i].x, wheels[i].y) for i in order]
    centroid = (
        sum(p[0] for p in ordered_centers) / len(ordered_centers),
        sum(p[1] for p in ordered_centers) / len(ordered_centers),
    )

    n = len(order)
    tangent_candidates_per_segment: List[List[Tuple[Tuple[float, float], Tuple[float, float]]]] = []

    for pos in range(n):
        i = order[pos]
        j = order[(pos + 1) % n]
        wi = wheels[i]
        wj = wheels[j]

        candidates = tangent_external_both(
            (wi.x, wi.y), wi.radius,
            (wj.x, wj.y), wj.radius,
        )
        candidates.extend(
            tangent_internal_both(
                (wi.x, wi.y), wi.radius,
                (wj.x, wj.y), wj.radius,
            )
        )
        if not candidates:
            raise ValueError(
                f"Zwischen '{wi.name}' und '{wj.name}' konnte keine gültige Tangente gebildet werden. "
                f"Prüfe Durchmesser und Positionen."
            )

        candidates.sort(
            key=lambda t: math.hypot(((t[0][0] + t[1][0]) / 2.0) - centroid[0], ((t[0][1] + t[1][1]) / 2.0) - centroid[1]),
            reverse=True,
        )
        tangent_candidates_per_segment.append(candidates)

    choices: List[Tuple[Tuple[float, float], Tuple[float, float]]] = []
    best_solution: Optional[BeltSolution] = None
    best_score = -1e18

    def dfs_choose_tangents(pos: int) -> None:
        nonlocal best_solution, best_score
        if pos == n:
            candidate_solution = build_solution_from_tangents(
                wheels=wheels,
                order=order,
                centroid=centroid,
                tangent_choices=choices,
            )
            if candidate_solution is None:
                return

            score = 0.0
            for p1, p2 in choices:
                mx = (p1[0] + p2[0]) / 2.0
                my = (p1[1] + p2[1]) / 2.0
                score += math.hypot(mx - centroid[0], my - centroid[1])

            if (score > best_score + 1e-9) or (
                abs(score - best_score) <= 1e-9
                and (best_solution is None or candidate_solution.total_length < best_solution.total_length)
            ):
                best_score = score
                best_solution = candidate_solution
            return

        for tang in tangent_candidates_per_segment[pos]:
            choices.append(tang)
            dfs_choose_tangents(pos + 1)
            choices.pop()

    dfs_choose_tangents(0)

    if best_solution is None:
        raise ValueError(
            "Es wurde keine physikalisch legbare Riemenführung gefunden. "
            "Bitte Positionen oder Durchmesser anpassen."
        )

    return best_solution

def pulley_pitch_for_teeth(diameter: float, teeth: int) -> float:
    return (math.pi * diameter) / teeth


def corrected_diameter_for_pitch(teeth: int, pitch: float) -> float:
    return (teeth * pitch) / math.pi


def derive_tooth_geometry_from_pitch(pitch: float) -> Tuple[float, float, float]:
    tooth_height = pitch * TOOTH_HEIGHT_FACTOR
    tooth_top = pitch * TOOTH_TOP_FACTOR
    tooth_root = pitch * TOOTH_ROOT_FACTOR
    return tooth_height, tooth_top, tooth_root


def exact_minimum_pitch_from_constraints(min_tooth_height: float, min_tooth_root: float) -> Tuple[float, float, float]:
    pitch_from_height = min_tooth_height / TOOTH_HEIGHT_FACTOR
    pitch_from_root = min_tooth_root / TOOTH_ROOT_FACTOR
    exact_required_pitch = max(BASE_MIN_PITCH, pitch_from_height, pitch_from_root)
    return pitch_from_height, pitch_from_root, exact_required_pitch


def choose_exact_common_pitch_and_teeth(
    wheels: List[Wheel],
    min_tooth_height: float,
    min_tooth_root: float,
) -> DerivedProfile:
    pulleys = [(idx, w) for idx, w in enumerate(wheels) if w.kind == "Pulley"]
    if not pulleys:
        raise ValueError("Es ist mindestens ein Pulley erforderlich, damit eine exakte Teilung berechnet werden kann.")

    if any(w.diameter <= 0 for _, w in pulleys):
        raise ValueError("Alle Pulley-Durchmesser mÃ¼ssen > 0 sein.")

    pitch_from_height, pitch_from_root, exact_required_pitch = exact_minimum_pitch_from_constraints(
        min_tooth_height=min_tooth_height,
        min_tooth_root=min_tooth_root,
    )

    if exact_required_pitch > MAX_PITCH:
        raise ValueError(
            "Die Mindestvorgaben fÃ¼r die Zahngeometrie erzwingen eine Teilung oberhalb des zulÃ¤ssigen Bereichs."
        )

    best = None

    candidate_reference_pitches = set()
    for _, w in pulleys:
        z_min = max(MIN_TEETH, int(math.floor(math.pi * w.diameter / MAX_PITCH)))
        z_max = min(MAX_TEETH, int(math.floor(math.pi * w.diameter / exact_required_pitch)))
        for z in range(z_min, z_max + 1):
            p = pulley_pitch_for_teeth(w.diameter, z)
            if exact_required_pitch <= p <= MAX_PITCH:
                candidate_reference_pitches.add(round(p, 6))

    if not candidate_reference_pitches:
        raise ValueError(
            "Aus den Pulley-Durchmessern konnte keine exakte gemeinsame Teilung gefunden werden, "
            "die die Mindest-Zahngeometrie einhÃ¤lt."
        )

    for p_ref in sorted(candidate_reference_pitches):
        teeth_map: Dict[int, int] = {}
        valid = True

        for idx, w in pulleys:
            z = int(round((math.pi * w.diameter) / p_ref))
            if z < MIN_TEETH or z > MAX_TEETH:
                valid = False
                break
            implied_pitch = pulley_pitch_for_teeth(w.diameter, z)
            if implied_pitch < exact_required_pitch - 1e-9:
                valid = False
                break
            teeth_map[idx] = z

        if not valid:
            continue

        exact_pitch = sum((math.pi * w.diameter) / teeth_map[idx] for idx, w in pulleys) / len(pulleys)

        if exact_pitch < exact_required_pitch - 1e-9 or exact_pitch > MAX_PITCH + 1e-9:
            continue

        corrected = {
            idx: corrected_diameter_for_pitch(teeth_map[idx], exact_pitch)
            for idx, _ in pulleys
        }

        individual_pitches = [
            pulley_pitch_for_teeth(w.diameter, teeth_map[idx])
            for idx, w in pulleys
        ]
        max_dev = max(abs(p - exact_pitch) for p in individual_pitches)
        mean_diam_err = sum(abs(corrected[idx] - w.diameter) for idx, w in pulleys) / len(pulleys)
        ref_bias = abs(exact_pitch - REFERENCE_PITCH)

        score = (max_dev * 10.0) + mean_diam_err + (ref_bias * 0.05)

        if best is None or score < best["score"]:
            best = {
                "score": score,
                "pitch": exact_pitch,
                "max_dev": max_dev,
                "teeth": teeth_map,
                "corrected": corrected,
            }

    if best is None:
        raise ValueError(
            "Es konnte keine exakte gemeinsame Teilung bestimmt werden. "
            "Mit den aktuellen Pulley-Durchmessern und Zahn-MindestmaÃŸen ist die Konstruktion so nicht mÃ¶glich."
        )

    pitch = best["pitch"]
    tooth_height, tooth_top, tooth_root = derive_tooth_geometry_from_pitch(pitch)

    if tooth_height + 1e-9 < min_tooth_height or tooth_root + 1e-9 < min_tooth_root:
        raise ValueError(
            "Die ermittelte exakte Teilung erfÃ¼llt die Mindest-Zahngeometrie nicht. "
            "Bitte Pulley-Durchmesser oder Mindestvorgaben anpassen."
        )

    return DerivedProfile(
        pitch=pitch,
        tooth_height=tooth_height,
        tooth_top=tooth_top,
        tooth_root=tooth_root,
        pulley_teeth=best["teeth"],
        corrected_pitch_diameters=best["corrected"],
        max_pitch_deviation=best["max_dev"],
        printable_min_tooth_height=min_tooth_height,
        printable_min_tooth_root=min_tooth_root,
        constraint_pitch_from_height=pitch_from_height,
        constraint_pitch_from_root=pitch_from_root,
    )


def build_effective_geometry_wheels(wheels: List[Wheel], profile: DerivedProfile) -> List[Wheel]:
    effective: List[Wheel] = []
    for idx, w in enumerate(wheels):
        d_eff = profile.corrected_pitch_diameters[idx] if (w.kind == "Pulley" and idx in profile.corrected_pitch_diameters) else w.diameter
        effective.append(Wheel(w.wid, w.name, w.x, w.y, d_eff, w.kind))
    return effective


# ============================================================
# Achsabstands-Korrektur statt RiemenlÃ¤ngen-Korrektur
# ============================================================

def centroid_of_wheels(wheels: List[Wheel]) -> Tuple[float, float]:
    return (
        sum(w.x for w in wheels) / len(wheels),
        sum(w.y for w in wheels) / len(wheels),
    )


def scale_wheel_positions_about_centroid(
    wheels: List[Wheel],
    scale: float,
    fixed_diameters: bool = True,
) -> List[Wheel]:
    if not wheels:
        return []

    cx, cy = centroid_of_wheels(wheels)
    out: List[Wheel] = []
    for w in wheels:
        nx = cx + (w.x - cx) * scale
        ny = cy + (w.y - cy) * scale
        nd = w.diameter if fixed_diameters else w.diameter * scale
        out.append(Wheel(w.wid, w.name, nx, ny, nd, w.kind))
    return out


def solve_center_distance_correction(
    nominal_wheels: List[Wheel],
    pitch: float,
) -> CenterDistanceCorrection:
    if len(nominal_wheels) < 2:
        raise ValueError("Mindestens 2 Elemente erforderlich.")

    nominal_solution = compute_belt_solution(nominal_wheels)
    nominal_length = nominal_solution.total_length

    belt_teeth_exact = nominal_length / pitch
    belt_teeth_used = max(1, int(round(belt_teeth_exact)))
    target_length = belt_teeth_used * pitch
    length_delta_before = target_length - nominal_length

    if abs(length_delta_before) <= 1e-9:
        return CenterDistanceCorrection(
            nominal_length=nominal_length,
            target_length=target_length,
            corrected_length=nominal_length,
            nominal_belt_teeth_exact=belt_teeth_exact,
            belt_teeth_used=belt_teeth_used,
            length_delta_before=length_delta_before,
            length_delta_after=0.0,
            position_scale=1.0,
            nominal_wheels=nominal_wheels,
            corrected_wheels=nominal_wheels,
            corrected_solution=nominal_solution,
        )

    def length_for_scale(scale: float) -> Tuple[float, List[Wheel], BeltSolution]:
        ws = scale_wheel_positions_about_centroid(nominal_wheels, scale)
        sol = compute_belt_solution(ws)
        return sol.total_length, ws, sol

    base_length = nominal_length

    if target_length > base_length:
        lo = 1.0
        hi = 1.05
        hi_length, _, _ = length_for_scale(hi)
        attempts = 0
        while hi_length < target_length and attempts < 80:
            hi *= 1.15
            hi_length, _, _ = length_for_scale(hi)
            attempts += 1
        if hi_length < target_length:
            raise ValueError("Achsabstands-Korrektur nach auÃŸen konnte nicht bestimmt werden.")
    else:
        hi = 1.0
        lo = 0.95
        lo_length, _, _ = length_for_scale(lo)
        attempts = 0
        while lo_length > target_length and attempts < 80:
            lo *= 0.90
            lo_length, _, _ = length_for_scale(lo)
            attempts += 1
            if lo <= 1e-4:
                break
        if lo_length > target_length:
            raise ValueError("Achsabstands-Korrektur nach innen konnte nicht bestimmt werden.")

    best_scale = 1.0
    best_wheels = nominal_wheels
    best_solution = nominal_solution
    best_err = abs(base_length - target_length)

    for _ in range(90):
        mid = (lo + hi) / 2.0
        mid_length, mid_wheels, mid_solution = length_for_scale(mid)
        err = abs(mid_length - target_length)

        if err < best_err:
            best_err = err
            best_scale = mid
            best_wheels = mid_wheels
            best_solution = mid_solution

        if mid_length < target_length:
            lo = mid
        else:
            hi = mid

    corrected_length = best_solution.total_length

    return CenterDistanceCorrection(
        nominal_length=nominal_length,
        target_length=target_length,
        corrected_length=corrected_length,
        nominal_belt_teeth_exact=belt_teeth_exact,
        belt_teeth_used=belt_teeth_used,
        length_delta_before=length_delta_before,
        length_delta_after=target_length - corrected_length,
        position_scale=best_scale,
        nominal_wheels=nominal_wheels,
        corrected_wheels=best_wheels,
        corrected_solution=best_solution,
    )


# ============================================================
# GUI
# ============================================================

class BeltDesignerApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Riementrieb Konstruktion 2D")
        self.root.geometry("1560x940")
        self.root.minsize(1280, 800)

        self.wheels: List[Wheel] = []
        self.next_id = 1
        self.selected_index: Optional[int] = None
        self.dragging = False
        self.drag_offset = (0.0, 0.0)

        self.solution: Optional[BeltSolution] = None
        self.profile: Optional[DerivedProfile] = None
        self.effective_wheels: Optional[List[Wheel]] = None
        self.center_correction: Optional[CenterDistanceCorrection] = None

        self.view_scale = 1.0
        self.view_offset_x = 40.0
        self.view_offset_y = 40.0

        self._build_ui()
        self._add_demo_data()
        self.root.after(50, self.initial_fit)
        self.refresh_list()
        self.update_profile_preview()
        self.redraw()

    # --------------------------------------------------------
    # UI
    # --------------------------------------------------------

    def _build_ui(self) -> None:
        self.root.columnconfigure(0, weight=4)
        self.root.columnconfigure(1, weight=0)
        self.root.rowconfigure(0, weight=1)

        left = ttk.Frame(self.root, padding=8)
        left.grid(row=0, column=0, sticky="nsew")
        left.rowconfigure(0, weight=1)
        left.columnconfigure(0, weight=1)

        self.canvas = tk.Canvas(left, bg="white", highlightthickness=1, highlightbackground="#bfc7cf")
        self.canvas.grid(row=0, column=0, sticky="nsew")

        self.canvas.bind("<Button-1>", self.on_canvas_down)
        self.canvas.bind("<B1-Motion>", self.on_canvas_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_canvas_up)
        self.canvas.bind("<Configure>", self.on_canvas_configure)

        right = ttk.Frame(self.root, padding=(0, 8, 8, 8))
        right.grid(row=0, column=1, sticky="ns")
        right.columnconfigure(0, weight=1)
        right.rowconfigure(4, weight=1)

        ttk.Label(right, text="Parameter", font=("Segoe UI", 11, "bold")).grid(
            row=0, column=0, sticky="w", pady=(0, 8)
        )

        profile_box = ttk.LabelFrame(right, text="Exakt berechnetes Zahnprofil", padding=8)
        profile_box.grid(row=1, column=0, sticky="ew", pady=(0, 8))
        profile_box.columnconfigure(1, weight=1)

        self.min_tooth_height_var = tk.StringVar(value=f"{DEFAULT_PRINTABLE_MIN_TOOTH_HEIGHT:.1f}")
        self.min_tooth_root_var = tk.StringVar(value=f"{DEFAULT_PRINTABLE_MIN_TOOTH_ROOT:.1f}")
        self.belt_width_var = tk.StringVar(value="10.0")

        self.pitch_auto_var = tk.StringVar(value="â€”")
        self.tooth_distance_var = tk.StringVar(value="â€”")
        self.tooth_height_auto_var = tk.StringVar(value="â€”")
        self.tooth_top_auto_var = tk.StringVar(value="â€”")
        self.tooth_root_auto_var = tk.StringVar(value="â€”")
        self.pitch_dev_var = tk.StringVar(value="â€”")

        self._entry_row(profile_box, 0, "Mindest-ZahnhÃ¶he [mm]", self.min_tooth_height_var)
        self._entry_row(profile_box, 1, "Mindest-ZahnfuÃŸbreite [mm]", self.min_tooth_root_var)
        self._readonly_row(profile_box, 2, "Exakte Teilung [mm]", self.pitch_auto_var)
        self._readonly_row(profile_box, 3, "Zahnabstand am Riemen [mm]", self.tooth_distance_var)
        self._readonly_row(profile_box, 4, "Berechnete ZahnhÃ¶he [mm]", self.tooth_height_auto_var)
        self._readonly_row(profile_box, 5, "Berechnete Zahnkopfbreite [mm]", self.tooth_top_auto_var)
        self._readonly_row(profile_box, 6, "Berechnete ZahnfuÃŸbreite [mm]", self.tooth_root_auto_var)
        self._readonly_row(profile_box, 7, "Abw. Einzel-Pitches [mm]", self.pitch_dev_var)
        self._entry_row(profile_box, 8, "Riemenbreite [mm]", self.belt_width_var)

        wheels_box = ttk.LabelFrame(right, text="Pulleys / Rollen", padding=8)
        wheels_box.grid(row=2, column=0, sticky="ew", pady=(0, 8))
        wheels_box.columnconfigure(0, weight=1)

        self.wheel_list = tk.Listbox(wheels_box, height=12, exportselection=False, activestyle="none")
        self.wheel_list.grid(row=0, column=0, columnspan=3, sticky="ew")
        self.wheel_list.bind("<<ListboxSelect>>", self.on_list_select)

        btn_row1 = ttk.Frame(wheels_box)
        btn_row1.grid(row=1, column=0, columnspan=3, sticky="ew", pady=(8, 6))
        btn_row1.columnconfigure((0, 1, 2), weight=1)

        ttk.Button(btn_row1, text="Pulley hinzufÃ¼gen", command=self.add_pulley).grid(row=0, column=0, padx=2, sticky="ew")
        ttk.Button(btn_row1, text="Rolle hinzufÃ¼gen", command=self.add_roller).grid(row=0, column=1, padx=2, sticky="ew")
        ttk.Button(btn_row1, text="LÃ¶schen", command=self.delete_selected).grid(row=0, column=2, padx=2, sticky="ew")

        btn_row2 = ttk.Frame(wheels_box)
        btn_row2.grid(row=2, column=0, columnspan=3, sticky="ew", pady=(0, 6))
        btn_row2.columnconfigure((0, 1, 2), weight=1)

        ttk.Button(btn_row2, text="Duplizieren", command=self.duplicate_selected).grid(row=0, column=0, padx=2, sticky="ew")
        ttk.Button(btn_row2, text="Nach oben", command=self.move_up).grid(row=0, column=1, padx=2, sticky="ew")
        ttk.Button(btn_row2, text="Nach unten", command=self.move_down).grid(row=0, column=2, padx=2, sticky="ew")

        edit = ttk.Frame(wheels_box)
        edit.grid(row=3, column=0, columnspan=3, sticky="ew")
        edit.columnconfigure(1, weight=1)

        self.sel_name_var = tk.StringVar()
        self.sel_kind_var = tk.StringVar(value="Pulley")
        self.sel_diameter_var = tk.StringVar()
        self.sel_x_var = tk.StringVar()
        self.sel_y_var = tk.StringVar()

        self._entry_row(edit, 0, "Name", self.sel_name_var)
        self._combo_row(edit, 1, "Typ", self.sel_kind_var, ["Pulley", "Rolle"])
        self._entry_row(edit, 2, "Durchmesser [mm]", self.sel_diameter_var)
        self._entry_row(edit, 3, "X [mm]", self.sel_x_var)
        self._entry_row(edit, 4, "Y [mm]", self.sel_y_var)

        ttk.Button(edit, text="Ã„nderungen Ã¼bernehmen", command=self.apply_selected_edit).grid(
            row=5, column=0, columnspan=2, sticky="ew", pady=(6, 0)
        )

        action_box = ttk.LabelFrame(right, text="Berechnung", padding=8)
        action_box.grid(row=3, column=0, sticky="ew", pady=(0, 8))
        action_box.columnconfigure((0, 1, 2), weight=1)

        ttk.Button(action_box, text="Riemen berechnen", command=self.calculate).grid(row=0, column=0, padx=2, pady=2, sticky="ew")
        ttk.Button(action_box, text="Einpassen", command=self.fit_view_to_scene).grid(row=0, column=1, padx=2, pady=2, sticky="ew")
        ttk.Button(action_box, text="Vorschau aktualisieren", command=self.refresh_everything).grid(row=0, column=2, padx=2, pady=2, sticky="ew")

        result_box = ttk.LabelFrame(right, text="Ergebnis", padding=8)
        result_box.grid(row=4, column=0, sticky="nsew")
        result_box.rowconfigure(0, weight=1)
        result_box.columnconfigure(0, weight=1)

        self.result_text = tk.Text(result_box, wrap="word", font=("Consolas", 10), state="disabled")
        self.result_text.grid(row=0, column=0, sticky="nsew")

    def _entry_row(self, parent, row: int, label: str, variable: tk.StringVar) -> None:
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w", pady=2, padx=(0, 8))
        ttk.Entry(parent, textvariable=variable, width=22).grid(row=row, column=1, sticky="ew", pady=2)

    def _readonly_row(self, parent, row: int, label: str, variable: tk.StringVar) -> None:
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w", pady=2, padx=(0, 8))
        ttk.Entry(parent, textvariable=variable, width=22, state="readonly").grid(row=row, column=1, sticky="ew", pady=2)

    def _combo_row(self, parent, row: int, label: str, variable: tk.StringVar, values: List[str]) -> None:
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w", pady=2, padx=(0, 8))
        ttk.Combobox(parent, textvariable=variable, values=values, state="readonly").grid(row=row, column=1, sticky="ew", pady=2)

    # --------------------------------------------------------
    # Demo
    # --------------------------------------------------------

    def _add_demo_data(self) -> None:
        self.wheels = [
            Wheel(self.next_id, "Motor", 250, 250, 32.0, "Pulley"),
            Wheel(self.next_id + 1, "Umlenkrolle 1", 520, 150, 28.0, "Rolle"),
            Wheel(self.next_id + 2, "Abtrieb", 820, 300, 64.0, "Pulley"),
            Wheel(self.next_id + 3, "Umlenkrolle 2", 520, 560, 36.0, "Rolle"),
        ]
        self.next_id += 4

    # --------------------------------------------------------
    # Parsing
    # --------------------------------------------------------

    def parse_float(self, text: str, name: str, positive: bool = False) -> float:
        try:
            v = float(text.replace(",", "."))
        except ValueError:
            raise ValueError(f"{name}: ungÃ¼ltiger Wert.")
        if positive and v <= 0:
            raise ValueError(f"{name} muss > 0 sein.")
        return v

    def get_belt_width(self) -> float:
        return self.parse_float(self.belt_width_var.get(), "Riemenbreite", positive=True)

    def get_min_tooth_height(self) -> float:
        return self.parse_float(self.min_tooth_height_var.get(), "Mindest-ZahnhÃ¶he", positive=True)

    def get_min_tooth_root(self) -> float:
        return self.parse_float(self.min_tooth_root_var.get(), "Mindest-ZahnfuÃŸbreite", positive=True)

    def get_preview_profile(self) -> DerivedProfile:
        return choose_exact_common_pitch_and_teeth(
            self.wheels,
            min_tooth_height=self.get_min_tooth_height(),
            min_tooth_root=self.get_min_tooth_root(),
        )

    # --------------------------------------------------------
    # Zustandsaktualisierung
    # --------------------------------------------------------

    def invalidate_solution(self) -> None:
        self.solution = None
        self.profile = None
        self.effective_wheels = None
        self.center_correction = None

    def refresh_everything(self) -> None:
        self.refresh_list()
        self.update_profile_preview()
        self.redraw()

    def update_profile_preview(self) -> None:
        try:
            profile = self.get_preview_profile()
            self.pitch_auto_var.set(f"{profile.pitch:.6f}")
            self.tooth_distance_var.set(f"{profile.pitch:.6f}")
            self.tooth_height_auto_var.set(f"{profile.tooth_height:.6f}")
            self.tooth_top_auto_var.set(f"{profile.tooth_top:.6f}")
            self.tooth_root_auto_var.set(f"{profile.tooth_root:.6f}")
            self.pitch_dev_var.set(f"{profile.max_pitch_deviation:.6f}")
        except Exception:
            self.pitch_auto_var.set("â€”")
            self.tooth_distance_var.set("â€”")
            self.tooth_height_auto_var.set("â€”")
            self.tooth_top_auto_var.set("â€”")
            self.tooth_root_auto_var.set("â€”")
            self.pitch_dev_var.set("â€”")

    # --------------------------------------------------------
    # View / Zoom
    # --------------------------------------------------------

    def initial_fit(self) -> None:
        self.fit_view_to_scene()

    def on_canvas_configure(self, _event=None) -> None:
        self.redraw()

    def world_to_screen(self, x: float, y: float) -> Tuple[float, float]:
        return x * self.view_scale + self.view_offset_x, y * self.view_scale + self.view_offset_y

    def screen_to_world(self, x: float, y: float) -> Tuple[float, float]:
        s = self.view_scale if abs(self.view_scale) > 1e-12 else 1.0
        return (x - self.view_offset_x) / s, (y - self.view_offset_y) / s

    def get_canvas_size(self) -> Tuple[float, float]:
        self.root.update_idletasks()
        return float(max(200, self.canvas.winfo_width())), float(max(200, self.canvas.winfo_height()))

    def get_scene_wheels_for_view(self) -> List[Wheel]:
        if self.center_correction is not None:
            return self.center_correction.corrected_wheels
        if self.effective_wheels is not None:
            return self.effective_wheels
        return self.wheels

    def get_scene_bounds(self) -> Tuple[float, float, float, float]:
        geom_wheels = self.get_scene_wheels_for_view()
        if not geom_wheels:
            return 0.0, 0.0, 100.0, 100.0

        min_x = float("inf")
        min_y = float("inf")
        max_x = float("-inf")
        max_y = float("-inf")

        for w in geom_wheels:
            min_x = min(min_x, w.x - w.radius)
            min_y = min(min_y, w.y - w.radius)
            max_x = max(max_x, w.x + w.radius)
            max_y = max(max_y, w.y + w.radius)

        if self.solution is not None:
            for seg in self.solution.segments:
                min_x = min(min_x, seg.p1[0], seg.p2[0])
                min_y = min(min_y, seg.p1[1], seg.p2[1])
                max_x = max(max_x, seg.p1[0], seg.p2[0])
                max_y = max(max_y, seg.p1[1], seg.p2[1])

            for arc in self.solution.arcs:
                min_x = min(min_x, arc.center[0] - arc.radius)
                min_y = min(min_y, arc.center[1] - arc.radius)
                max_x = max(max_x, arc.center[0] + arc.radius)
                max_y = max(max_y, arc.center[1] + arc.radius)

            cx, cy = self.solution.centroid
            min_x = min(min_x, cx)
            min_y = min(min_y, cy)
            max_x = max(max_x, cx)
            max_y = max(max_y, cy)

        if max_x - min_x < 1e-6:
            max_x = min_x + 100.0
        if max_y - min_y < 1e-6:
            max_y = min_y + 100.0

        return min_x, min_y, max_x, max_y

    def fit_view_to_scene(self) -> None:
        cw, ch = self.get_canvas_size()
        min_x, min_y, max_x, max_y = self.get_scene_bounds()

        margin_px = max(50.0, min(cw, ch) * 0.08)

        legend_x, _legend_y, _legend_w, _legend_h = self.get_legend_box()
        legend_clearance = 16.0
        reserved_right = max(0.0, cw - max(0.0, legend_x - legend_clearance))

        avail_w = max(50.0, cw - 2.0 * margin_px - reserved_right)
        avail_h = max(50.0, ch - 2.0 * margin_px)

        scene_w = max(1e-6, max_x - min_x)
        scene_h = max(1e-6, max_y - min_y)

        scale = min(avail_w / scene_w, avail_h / scene_h)
        self.view_scale = max(0.05, scale)

        viewport_left = margin_px
        viewport_right = max(viewport_left + 50.0, cw - margin_px - reserved_right)
        viewport_top = margin_px
        viewport_bottom = max(viewport_top + 50.0, ch - margin_px)

        viewport_cx = (viewport_left + viewport_right) / 2.0
        viewport_cy = (viewport_top + viewport_bottom) / 2.0

        scene_cx = (min_x + max_x) / 2.0
        scene_cy = (min_y + max_y) / 2.0
        self.view_offset_x = viewport_cx - scene_cx * self.view_scale
        self.view_offset_y = viewport_cy - scene_cy * self.view_scale

        self.redraw()

    def choose_grid_step(self) -> float:
        candidates = [5, 10, 20, 25, 50, 100, 200, 250, 500, 1000, 2000]
        target_px = 90.0
        best_step = 100.0
        best_diff = float("inf")
        for step in candidates:
            diff = abs(step * self.view_scale - target_px)
            if diff < best_diff:
                best_diff = diff
                best_step = float(step)
        return best_step


    def get_legend_box(self) -> Tuple[float, float, float, float]:
        cw, _ = self.get_canvas_size()
        legend_w = 365.0
        legend_h = 194.0
        right_margin = 15.0
        top_margin = 14.0
        x = cw - (legend_w + right_margin)
        y = top_margin
        return x, y, legend_w, legend_h

    # --------------------------------------------------------
    # Listen / Auswahl
    # --------------------------------------------------------

    def refresh_list(self) -> None:
        self.wheel_list.delete(0, tk.END)

        preview_profile: Optional[DerivedProfile] = None
        try:
            preview_profile = self.get_preview_profile()
        except Exception:
            preview_profile = None

        for idx, w in enumerate(self.wheels):
            if w.kind == "Pulley" and preview_profile is not None and idx in preview_profile.pulley_teeth:
                z = preview_profile.pulley_teeth[idx]
                d_corr = preview_profile.corrected_pitch_diameters[idx]
                text = (
                    f"{idx+1:02d}. {w.name} | {w.kind} | D_eing={w.diameter:.3f} mm | "
                    f"Z={z:d} | D_korr={d_corr:.3f} mm | ({w.x:.1f}, {w.y:.1f})"
                )
            else:
                text = f"{idx+1:02d}. {w.name} | {w.kind} | D={w.diameter:.3f} mm | ({w.x:.1f}, {w.y:.1f})"
            self.wheel_list.insert(tk.END, text)

        if self.selected_index is not None and 0 <= self.selected_index < len(self.wheels):
            self.wheel_list.selection_set(self.selected_index)
            self.load_selected_to_editor()
        else:
            self.clear_editor()

    def on_list_select(self, _event=None) -> None:
        sel = self.wheel_list.curselection()
        if not sel:
            self.selected_index = None
            self.clear_editor()
            self.redraw()
            return
        self.selected_index = sel[0]
        self.load_selected_to_editor()
        self.redraw()

    def load_selected_to_editor(self) -> None:
        if self.selected_index is None or not (0 <= self.selected_index < len(self.wheels)):
            self.clear_editor()
            return

        w = self.wheels[self.selected_index]
        self.sel_name_var.set(w.name)
        self.sel_kind_var.set(w.kind)
        self.sel_diameter_var.set(f"{w.diameter:.4f}")
        self.sel_x_var.set(f"{w.x:.4f}")
        self.sel_y_var.set(f"{w.y:.4f}")

    def clear_editor(self) -> None:
        self.sel_name_var.set("")
        self.sel_kind_var.set("Pulley")
        self.sel_diameter_var.set("")
        self.sel_x_var.set("")
        self.sel_y_var.set("")

    # --------------------------------------------------------
    # Element-Aktionen
    # --------------------------------------------------------

    def add_pulley(self) -> None:
        idx = len(self.wheels) + 1
        self.wheels.append(Wheel(self.next_id, f"Pulley {idx}", 350 + 40 * (idx % 4), 260 + 40 * (idx % 3), 40.0, "Pulley"))
        self.next_id += 1
        self.selected_index = len(self.wheels) - 1
        self.invalidate_solution()
        self.refresh_everything()

    def add_roller(self) -> None:
        idx = len(self.wheels) + 1
        self.wheels.append(Wheel(self.next_id, f"Rolle {idx}", 380 + 40 * (idx % 4), 290 + 40 * (idx % 3), 30.0, "Rolle"))
        self.next_id += 1
        self.selected_index = len(self.wheels) - 1
        self.invalidate_solution()
        self.refresh_everything()

    def delete_selected(self) -> None:
        if self.selected_index is None or not (0 <= self.selected_index < len(self.wheels)):
            return
        del self.wheels[self.selected_index]
        self.selected_index = None if not self.wheels else min(self.selected_index, len(self.wheels) - 1)
        self.invalidate_solution()
        self.refresh_everything()

    def duplicate_selected(self) -> None:
        if self.selected_index is None:
            return
        w = self.wheels[self.selected_index]
        copy = Wheel(self.next_id, f"{w.name} Kopie", w.x + 40, w.y + 40, w.diameter, w.kind)
        self.next_id += 1
        self.wheels.insert(self.selected_index + 1, copy)
        self.selected_index += 1
        self.invalidate_solution()
        self.refresh_everything()

    def move_up(self) -> None:
        if self.selected_index is None or self.selected_index <= 0:
            return
        i = self.selected_index
        self.wheels[i - 1], self.wheels[i] = self.wheels[i], self.wheels[i - 1]
        self.selected_index -= 1
        self.invalidate_solution()
        self.refresh_everything()

    def move_down(self) -> None:
        if self.selected_index is None or self.selected_index >= len(self.wheels) - 1:
            return
        i = self.selected_index
        self.wheels[i + 1], self.wheels[i] = self.wheels[i], self.wheels[i + 1]
        self.selected_index += 1
        self.invalidate_solution()
        self.refresh_everything()

    def apply_selected_edit(self) -> None:
        if self.selected_index is None:
            return
        try:
            name = self.sel_name_var.get().strip() or f"Element {self.selected_index + 1}"
            kind = self.sel_kind_var.get().strip() or "Pulley"
            diameter = self.parse_float(self.sel_diameter_var.get(), "Durchmesser", positive=True)
            x = self.parse_float(self.sel_x_var.get(), "X")
            y = self.parse_float(self.sel_y_var.get(), "Y")
        except Exception as e:
            messagebox.showerror("UngÃ¼ltige Eingabe", str(e))
            return

        w = self.wheels[self.selected_index]
        w.name = name
        w.kind = kind
        w.diameter = diameter
        w.x = x
        w.y = y

        self.invalidate_solution()
        self.refresh_everything()

    # --------------------------------------------------------
    # Drag & Drop
    # --------------------------------------------------------

    def hit_test(self, screen_x: float, screen_y: float) -> Optional[int]:
        world_x, world_y = self.screen_to_world(screen_x, screen_y)
        best = None
        best_d = float("inf")
        for i, w in enumerate(self.wheels):
            d = math.hypot(world_x - w.x, world_y - w.y)
            hit_r = max(8.0 / max(self.view_scale, 1e-6), w.radius + 8.0 / max(self.view_scale, 1e-6))
            if d <= hit_r and d < best_d:
                best = i
                best_d = d
        return best

    def on_canvas_down(self, event) -> None:
        idx = self.hit_test(event.x, event.y)
        if idx is None:
            self.dragging = False
            return

        world_x, world_y = self.screen_to_world(event.x, event.y)
        self.selected_index = idx
        self.dragging = True
        w = self.wheels[idx]
        self.drag_offset = (world_x - w.x, world_y - w.y)
        self.refresh_list()
        self.redraw()

    def on_canvas_drag(self, event) -> None:
        if not self.dragging or self.selected_index is None:
            return
        world_x, world_y = self.screen_to_world(event.x, event.y)
        w = self.wheels[self.selected_index]
        w.x = world_x - self.drag_offset[0]
        w.y = world_y - self.drag_offset[1]
        self.invalidate_solution()
        self.refresh_everything()

    def on_canvas_up(self, _event) -> None:
        self.dragging = False

    # --------------------------------------------------------
    # Berechnung
    # --------------------------------------------------------

    def calculate(self) -> None:
        try:
            belt_width = self.get_belt_width()
            min_tooth_height = self.get_min_tooth_height()
            min_tooth_root = self.get_min_tooth_root()

            if len(self.wheels) < 2:
                raise ValueError("Mindestens 2 Elemente erforderlich.")

            for w in self.wheels:
                if w.diameter <= 0:
                    raise ValueError(f"{w.name}: Durchmesser muss > 0 sein.")

            self.profile = choose_exact_common_pitch_and_teeth(
                self.wheels,
                min_tooth_height=min_tooth_height,
                min_tooth_root=min_tooth_root,
            )

            nominal_effective_wheels = build_effective_geometry_wheels(self.wheels, self.profile)
            self.center_correction = solve_center_distance_correction(
                nominal_wheels=nominal_effective_wheels,
                pitch=self.profile.pitch,
            )

            self.effective_wheels = self.center_correction.corrected_wheels
            self.solution = self.center_correction.corrected_solution
            self.update_profile_preview()

            pitch = self.profile.pitch
            tooth_height = self.profile.tooth_height
            tooth_top = self.profile.tooth_top
            tooth_root = self.profile.tooth_root

            length_nominal = self.center_correction.nominal_length
            length_exact = self.center_correction.corrected_length
            belt_teeth_exact_nominal = self.center_correction.nominal_belt_teeth_exact
            belt_teeth_used = self.center_correction.belt_teeth_used
            target_length = self.center_correction.target_length
            equivalent_diameter_exact = length_exact / math.pi
            equivalent_diameter_target = target_length / math.pi

            lines = []
            lines.append("RIEMENTRIEB BERECHNUNG")
            lines.append("=" * 102)
            lines.append("")
            lines.append("Exakte Zahnvorgaben / exakte Teilung")
            lines.append(f"  Mindest-ZahnhÃ¶he                          : {min_tooth_height:.6f} mm")
            lines.append(f"  Mindest-ZahnfuÃŸbreite                     : {min_tooth_root:.6f} mm")
            lines.append(f"  Exakt berechnete Teilung                  : {pitch:.6f} mm")
            lines.append(f"  Exakter Zahnabstand am Riemen             : {pitch:.6f} mm")
            lines.append(f"  Berechnete ZahnhÃ¶he                       : {tooth_height:.6f} mm")
            lines.append(f"  Berechnete Zahnkopfbreite                 : {tooth_top:.6f} mm")
            lines.append(f"  Berechnete ZahnfuÃŸbreite                  : {tooth_root:.6f} mm")
            lines.append(f"  Abw. Einzel-Pitches zur Exakt-Teilung     : {self.profile.max_pitch_deviation:.6f} mm")
            lines.append(f"  Riemenbreite                              : {belt_width:.4f} mm")
            lines.append("")
            lines.append("Wichtig")
            lines.append("  - Die Teilung ist der exakte Zahnabstand von Zahn zu Zahn auf dem Riemen.")
            lines.append("  - Diese Teilung bleibt fest.")
            lines.append("  - Nicht die RiemenlÃ¤nge wird korrigiert, sondern die AchsabstÃ¤nde / Positionen werden angepasst,")
            lines.append("    damit die feste Teilung und eine ganzzahlige Riemenzahnzahl gleichzeitig stimmen.")
            lines.append("")

            lines.append("Riemen / Achsabstands-Korrektur")
            lines.append(f"  Nominale RiemenlÃ¤nge                      : {length_nominal:.6f} mm")
            lines.append(f"  Exakte nominale Zahnzahl                  : {belt_teeth_exact_nominal:.6f}")
            lines.append(f"  Verwendete ganze Zahnzahl                 : {belt_teeth_used:d}")
            lines.append(f"  Ziel-RiemenlÃ¤nge aus Teilung*Zahnzahl     : {target_length:.6f} mm")
            lines.append(f"  LÃ¤ngendifferenz vor Achsabstands-Korr.    : {self.center_correction.length_delta_before:+.6f} mm")
            lines.append(f"  Positions-Skalierungsfaktor               : {self.center_correction.position_scale:.9f}")
            lines.append(f"  Resultierende korrigierte RiemenlÃ¤nge     : {length_exact:.6f} mm")
            lines.append(f"  Restfehler nach Achsabstands-Korr.        : {self.center_correction.length_delta_after:+.9f} mm")
            lines.append("")

            lines.append("Ersatz-Kreis fÃ¼r runde Konstruktion")
            lines.append(f"  Durchmesser aus korrigierter Geometrie    : {equivalent_diameter_exact:.6f} mm")
            lines.append(f"  Durchmesser aus Ziel-LÃ¤nge                : {equivalent_diameter_target:.6f} mm")
            lines.append("")

            lines.append("Elemente / korrigierte Achspositionen")
            ordered_names = []
            nominal_map = {w.wid: w for w in nominal_effective_wheels}
            corrected_map = {w.wid: w for w in self.center_correction.corrected_wheels}

            for pos, idx in enumerate(self.solution.order, start=1):
                w_input = self.wheels[idx]
                w_nom = nominal_map[w_input.wid]
                w_corr = corrected_map[w_input.wid]
                ordered_names.append(w_input.name)

                dx = w_corr.x - w_nom.x
                dy = w_corr.y - w_nom.y

                if w_input.kind == "Pulley":
                    z = self.profile.pulley_teeth[idx]
                    d_corr = self.profile.corrected_pitch_diameters[idx]
                    dd = d_corr - w_input.diameter
                    lines.append(
                        f"  {pos:02d}. {w_input.name:<20} Typ=Pulley  "
                        f"D_eing={w_input.diameter:>10.4f} mm  "
                        f"Z={z:>4d}  "
                        f"D_korr={d_corr:>10.4f} mm  "
                        f"D_Abw={dd:+.4f} mm  "
                        f"Pos_nom=({w_nom.x:>8.3f}, {w_nom.y:>8.3f})  "
                        f"Pos_korr=({w_corr.x:>8.3f}, {w_corr.y:>8.3f})  "
                        f"Î”=({dx:+.3f}, {dy:+.3f})"
                    )
                else:
                    lines.append(
                        f"  {pos:02d}. {w_input.name:<20} Typ=Rolle   "
                        f"D={w_input.diameter:>10.4f} mm  "
                        f"Pos_nom=({w_nom.x:>8.3f}, {w_nom.y:>8.3f})  "
                        f"Pos_korr=({w_corr.x:>8.3f}, {w_corr.y:>8.3f})  "
                        f"Î”=({dx:+.3f}, {dy:+.3f})"
                    )
            lines.append("")

            lines.append("Automatisch gewÃ¤hlte sinnvolle Riemenreihenfolge")
            lines.append("  " + "  ->  ".join(ordered_names))
            lines.append("")

            lines.append("Korrigierte AchsabstÃ¤nde")
            for seg in self.solution.segments:
                wa = self.effective_wheels[seg.a_idx]
                wb = self.effective_wheels[seg.b_idx]
                lines.append(f"  {wa.name:<20} -> {wb.name:<20} : {seg.center_distance:>10.4f} mm")
            lines.append("")

            lines.append("Geradensegmente des Riemens")
            for seg in self.solution.segments:
                wa = self.effective_wheels[seg.a_idx]
                wb = self.effective_wheels[seg.b_idx]
                lines.append(f"  {wa.name:<20} -> {wb.name:<20} : {seg.length:>10.4f} mm")
            lines.append("")

            lines.append("Bogenanteile am Riemen")
            for arc in self.solution.arcs:
                w = self.effective_wheels[arc.idx]
                wrap_deg = abs(math.degrees(arc.extent_angle))
                lines.append(f"  {w.name:<20} : BogenlÃ¤nge={arc.length:>10.4f} mm   Umschlingung={wrap_deg:>9.4f}Â°")
            lines.append("")
            lines.append("Hinweise")
            lines.append("  - Mindest-ZahnhÃ¶he und Mindest-ZahnfuÃŸbreite wirken als Randbedingungen der exakten Teilung.")
            lines.append("  - Die exakte Teilung bleibt unverÃ¤ndert fest.")
            lines.append("  - Die ganzzahlige Riemenzahnzahl bestimmt die Soll-LÃ¤nge.")
            lines.append("  - Damit Teilung und Zahnzahl stimmen, werden die AchsabstÃ¤nde skaliert.")
            lines.append("  - Rollen bleiben glatte Umlenkrollen mit ihrem eingegebenen AuÃŸendurchmesser.")
            lines.append("  - Die gestrichelte Zusatzkontur am Pulley zeigt den korrigierten Teilkreis.")
            lines.append("  - Nach der Berechnung wird die Ansicht automatisch mit freiem Rand in das Fenster eingepasst.")

            self.set_result_text("\n".join(lines))
            self.refresh_list()
            self.fit_view_to_scene()

        except Exception as e:
            self.invalidate_solution()
            self.redraw()
            messagebox.showerror("Berechnung fehlgeschlagen", str(e))

    # --------------------------------------------------------
    # Zeichnen
    # --------------------------------------------------------

    def redraw(self) -> None:
        self.canvas.delete("all")
        self.draw_grid()

        if self.solution is not None:
            self.draw_solution(self.solution)

        draw_wheels = self.get_scene_wheels_for_view()
        base_input_by_id = {w.wid: w for w in self.wheels}
        corrected_diameters_by_id: Dict[int, float] = {}
        if self.profile is not None:
            for idx, w in enumerate(self.wheels):
                if w.kind == "Pulley" and idx in self.profile.corrected_pitch_diameters:
                    corrected_diameters_by_id[w.wid] = self.profile.corrected_pitch_diameters[idx]

        selected_wid = self.wheels[self.selected_index].wid if (self.selected_index is not None and 0 <= self.selected_index < len(self.wheels)) else None

        for w in draw_wheels:
            corrected_diameter = corrected_diameters_by_id.get(w.wid)
            input_wheel = base_input_by_id.get(w.wid, w)
            self.draw_wheel(
                draw_wheel=w,
                input_wheel=input_wheel,
                selected=(w.wid == selected_wid),
                corrected_diameter=corrected_diameter,
            )

        self.draw_legend()

    def draw_grid(self) -> None:
        cw, ch = self.get_canvas_size()
        step_world = self.choose_grid_step()
        major_every = 5

        left_world, top_world = self.screen_to_world(0, 0)
        right_world, bottom_world = self.screen_to_world(cw, ch)

        start_x = math.floor(left_world / step_world) * step_world
        end_x = math.ceil(right_world / step_world) * step_world
        start_y = math.floor(top_world / step_world) * step_world
        end_y = math.ceil(bottom_world / step_world) * step_world

        x = start_x
        ix = 0
        while x <= end_x + 1e-9:
            sx, _ = self.world_to_screen(x, 0.0)
            is_major = abs(round(x / step_world) % major_every) == 0
            self.canvas.create_line(sx, 0, sx, ch, fill="#d7dee7" if is_major else "#eef2f6")
            ix += 1
            x = start_x + ix * step_world

        y = start_y
        iy = 0
        while y <= end_y + 1e-9:
            _, sy = self.world_to_screen(0.0, y)
            is_major = abs(round(y / step_world) % major_every) == 0
            self.canvas.create_line(0, sy, cw, sy, fill="#d7dee7" if is_major else "#eef2f6")
            iy += 1
            y = start_y + iy * step_world

        self.canvas.create_text(10, 10, anchor="nw", text="2D-Koordinatensystem [mm]", fill="#4d5b6a")

    def draw_wheel(self, draw_wheel: Wheel, input_wheel: Wheel, selected: bool, corrected_diameter: Optional[float] = None) -> None:
        r = draw_wheel.radius
        sx1, sy1 = self.world_to_screen(draw_wheel.x - r, draw_wheel.y - r)
        sx2, sy2 = self.world_to_screen(draw_wheel.x + r, draw_wheel.y + r)

        if draw_wheel.kind == "Pulley":
            fill = "#d9eefb"
            outline = "#1d5f8c"
        else:
            fill = "#efe5fb"
            outline = "#6a4c93"

        if selected:
            outline = "#d00000"

        self.canvas.create_oval(sx1, sy1, sx2, sy2, fill=fill, outline=outline, width=2)
        lx1, ly1 = self.world_to_screen(draw_wheel.x - r, draw_wheel.y)
        lx2, ly2 = self.world_to_screen(draw_wheel.x + r, draw_wheel.y)
        vx1, vy1 = self.world_to_screen(draw_wheel.x, draw_wheel.y - r)
        vx2, vy2 = self.world_to_screen(draw_wheel.x, draw_wheel.y + r)
        self.canvas.create_line(lx1, ly1, lx2, ly2, fill="#8aa5bf", dash=(3, 2))
        self.canvas.create_line(vx1, vy1, vx2, vy2, fill="#8aa5bf", dash=(3, 2))
        cx, cy = self.world_to_screen(draw_wheel.x, draw_wheel.y)
        self.canvas.create_oval(cx - 3, cy - 3, cx + 3, cy + 3, fill=outline, outline="")

        if draw_wheel.kind == "Pulley" and corrected_diameter is not None and abs(corrected_diameter - input_wheel.diameter) > 1e-6:
            rc = corrected_diameter / 2.0
            csx1, csy1 = self.world_to_screen(draw_wheel.x - rc, draw_wheel.y - rc)
            csx2, csy2 = self.world_to_screen(draw_wheel.x + rc, draw_wheel.y + rc)
            self.canvas.create_oval(csx1, csy1, csx2, csy2, outline="#2a9d8f", width=2, dash=(6, 3))

        dx = draw_wheel.x - input_wheel.x
        dy = draw_wheel.y - input_wheel.y

        label = f"{input_wheel.name}\nD={input_wheel.diameter:.2f} mm"
        if corrected_diameter is not None and draw_wheel.kind == "Pulley":
            label += f"\nDk={corrected_diameter:.2f} mm"
        if abs(dx) > 1e-6 or abs(dy) > 1e-6:
            label += f"\nÎ”=({dx:+.2f}, {dy:+.2f})"

        label_r = max(r, (corrected_diameter or draw_wheel.diameter) / 2.0)
        tx, ty = self.world_to_screen(draw_wheel.x, draw_wheel.y - label_r)
        self.canvas.create_text(tx, ty - 18, text=label, fill="#1b263b", font=("Segoe UI", 9, "bold"))

        if abs(dx) > 1e-6 or abs(dy) > 1e-6:
            ix, iy = self.world_to_screen(input_wheel.x, input_wheel.y)
            self.canvas.create_oval(ix - 3, iy - 3, ix + 3, iy + 3, outline="#9aa5b1", width=1)
            self.canvas.create_line(ix, iy, cx, cy, fill="#9aa5b1", dash=(2, 2))

    def draw_solution(self, solution: BeltSolution) -> None:
        for seg in solution.segments:
            x1, y1 = self.world_to_screen(seg.p1[0], seg.p1[1])
            x2, y2 = self.world_to_screen(seg.p2[0], seg.p2[1])
            self.canvas.create_line(x1, y1, x2, y2, fill="#0a9396", width=3)

        for arc in solution.arcs:
            cx, cy = arc.center
            r = arc.radius
            sx1, sy1 = self.world_to_screen(cx - r, cy - r)
            sx2, sy2 = self.world_to_screen(cx + r, cy + r)

            self.canvas.create_arc(
                (sx1, sy1, sx2, sy2),
                start=-math.degrees(arc.start_angle),
                extent=-math.degrees(arc.extent_angle),
                style="arc",
                outline="#0a9396",
                width=3,
            )

            pin_x, pin_y = self.world_to_screen(arc.p_in[0], arc.p_in[1])
            pout_x, pout_y = self.world_to_screen(arc.p_out[0], arc.p_out[1])

            self.canvas.create_oval(pin_x - 3, pin_y - 3, pin_x + 3, pin_y + 3, fill="#ee9b00", outline="")
            self.canvas.create_oval(pout_x - 3, pout_y - 3, pout_x + 3, pout_y + 3, fill="#ca6702", outline="")

        cx, cy = self.world_to_screen(solution.centroid[0], solution.centroid[1])
        self.canvas.create_oval(cx - 4, cy - 4, cx + 4, cy + 4, fill="#444", outline="")
        self.canvas.create_text(cx + 8, cy - 8, anchor="nw", text="Schwerpunkt", fill="#444", font=("Segoe UI", 8))

    def draw_legend(self) -> None:
        x, y, legend_w, legend_h = self.get_legend_box()
        self.canvas.create_rectangle(x, y, x + legend_w, y + legend_h, fill="white", outline="#ccd6dd")
        self.canvas.create_text(x + 10, y + 10, anchor="nw", text="Legende", font=("Segoe UI", 10, "bold"))
        self.canvas.create_line(x + 12, y + 34, x + 54, y + 34, fill="#0a9396", width=3)
        self.canvas.create_text(x + 62, y + 34, anchor="w", text="berechnete geschlossene RiemenfÃ¼hrung")
        self.canvas.create_oval(x + 12, y + 50, x + 24, y + 62, fill="#ee9b00", outline="")
        self.canvas.create_text(x + 32, y + 56, anchor="w", text="Tangenzpunkt Eintritt")
        self.canvas.create_oval(x + 12, y + 70, x + 24, y + 82, fill="#ca6702", outline="")
        self.canvas.create_text(x + 32, y + 76, anchor="w", text="Tangenzpunkt Austritt")
        self.canvas.create_oval(x + 12, y + 92, x + 24, y + 104, fill="#444", outline="")
        self.canvas.create_text(x + 32, y + 98, anchor="w", text="Schwerpunkt fÃ¼r AuÃŸenkontur")
        self.canvas.create_line(x + 12, y + 120, x + 54, y + 120, fill="#2a9d8f", width=2, dash=(6, 3))
        self.canvas.create_text(x + 62, y + 120, anchor="w", text="korrigierter Pulley-Teilkreis")
        self.canvas.create_line(x + 12, y + 142, x + 54, y + 142, fill="#9aa5b1", dash=(2, 2))
        self.canvas.create_text(x + 62, y + 142, anchor="w", text="Verschiebung durch Achsabstands-Korrektur")
        self.canvas.create_text(
            x + 10,
            y + 160,
            anchor="nw",
            text="Teilung bleibt exakt fest,",
            fill="#4d5b6a",
            font=("Segoe UI", 8),
        )
        self.canvas.create_text(
            x + 10,
            y + 174,
            anchor="nw",
            text="AchsabstÃ¤nde werden angepasst",
            fill="#4d5b6a",
            font=("Segoe UI", 8),
        )

    # --------------------------------------------------------
    # Ergebnisfeld
    # --------------------------------------------------------

    def set_result_text(self, text: str) -> None:
        self.result_text.config(state="normal")
        self.result_text.delete("1.0", tk.END)
        self.result_text.insert("1.0", text)
        self.result_text.config(state="disabled")


# ============================================================
# Start
# ============================================================

def main() -> None:
    root = tk.Tk()
    style = ttk.Style()
    try:
        style.theme_use("vista")
    except Exception:
        pass
    BeltDesignerApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()

