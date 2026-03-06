import math
import tkinter as tk
from tkinter import ttk, messagebox
from dataclasses import dataclass
from typing import List, Optional, Tuple


# ============================================================
# Datenmodell
# ============================================================

@dataclass
class Wheel:
    wid: int
    name: str
    x: float
    y: float
    diameter: float   # Teilkreisdurchmesser bei Pulley, Außendurchmesser bei Rolle
    kind: str         # "Pulley" oder "Rolle"

    @property
    def radius(self) -> float:
        return self.diameter / 2.0

    def derived_teeth_exact(self, pitch: float) -> float:
        if self.kind != "Pulley":
            return 0.0
        return (math.pi * self.diameter) / pitch

    def derived_teeth_rounded(self, pitch: float) -> int:
        if self.kind != "Pulley":
            return 0
        return max(1, int(round(self.derived_teeth_exact(pitch))))

    def corrected_pitch_diameter(self, pitch: float) -> float:
        if self.kind != "Pulley":
            return self.diameter
        z = self.derived_teeth_rounded(pitch)
        return (z * pitch) / math.pi


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


# ============================================================
# Geometrie
# ============================================================

TAU = 2.0 * math.pi


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


def choose_tangent_by_centroid(
    c1: Tuple[float, float],
    r1: float,
    c2: Tuple[float, float],
    r2: float,
    centroid: Tuple[float, float],
    prefer_outer: bool,
) -> Optional[Tuple[Tuple[float, float], Tuple[float, float]]]:
    candidates = tangent_external_both(c1, r1, c2, r2)
    if not candidates:
        return None

    best = None
    best_score = -1e18 if prefer_outer else 1e18
    for p1, p2 in candidates:
        mx = (p1[0] + p2[0]) / 2.0
        my = (p1[1] + p2[1]) / 2.0
        score = math.hypot(mx - centroid[0], my - centroid[1])
        if prefer_outer:
            if score > best_score:
                best_score = score
                best = (p1, p2)
        else:
            if score < best_score:
                best_score = score
                best = (p1, p2)
    return best


def arc_point(center: Tuple[float, float], radius: float, angle: float) -> Tuple[float, float]:
    return center[0] + radius * math.cos(angle), center[1] + radius * math.sin(angle)


def choose_arc_by_centroid(
    center: Tuple[float, float],
    radius: float,
    p_in: Tuple[float, float],
    p_out: Tuple[float, float],
    centroid: Tuple[float, float],
    prefer_outer: bool,
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

    if prefer_outer:
        if d_ccw >= d_cw:
            return a1, ccw, radius * ccw, p_mid_ccw
        else:
            return a1, -cw, radius * cw, p_mid_cw
    else:
        if d_ccw <= d_cw:
            return a1, ccw, radius * ccw, p_mid_ccw
        else:
            return a1, -cw, radius * cw, p_mid_cw


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


def compute_belt_solution(
    wheels: List[Wheel],
    prefer_outer: bool = True,
    order: Optional[List[int]] = None,
) -> BeltSolution:
    if len(wheels) < 2:
        raise ValueError("Mindestens 2 Elemente erforderlich.")

    if order is None:
        order = sensible_order(wheels)
    else:
        if len(order) != len(wheels) or set(order) != set(range(len(wheels))):
            raise ValueError("Ungültige Reihenfolge für die Riemenberechnung.")

    ordered_centers = [(wheels[i].x, wheels[i].y) for i in order]
    centroid = (
        sum(p[0] for p in ordered_centers) / len(ordered_centers),
        sum(p[1] for p in ordered_centers) / len(ordered_centers),
    )

    n = len(order)
    tangents_out = [None] * n
    tangents_in = [None] * n
    segments: List[Segment] = []

    for pos in range(n):
        i = order[pos]
        j = order[(pos + 1) % n]
        wi = wheels[i]
        wj = wheels[j]

        tang = choose_tangent_by_centroid(
            (wi.x, wi.y), wi.radius,
            (wj.x, wj.y), wj.radius,
            centroid,
            prefer_outer,
        )
        if tang is None:
            raise ValueError(
                f"Zwischen '{wi.name}' und '{wj.name}' konnte keine passende Tangente gebildet werden. "
                f"Prüfe Durchmesser und Positionen."
            )

        p1, p2 = tang
        tangents_out[pos] = p1
        tangents_in[(pos + 1) % n] = p2

        seg_len = dist(p1, p2)
        center_d = dist((wi.x, wi.y), (wj.x, wj.y))

        segments.append(
            Segment(
                a_idx=i,
                b_idx=j,
                p1=p1,
                p2=p2,
                length=seg_len,
                center_distance=center_d,
            )
        )

    # Plausibilitätsprüfung: Segmente sollen nicht durch andere Rollen schneiden
    for seg in segments:
        for idx, w in enumerate(wheels):
            if idx in (seg.a_idx, seg.b_idx):
                continue
            d = line_point_distance((w.x, w.y), seg.p1, seg.p2)
            if d < w.radius * 0.98:
                raise ValueError(
                    "Die aktuelle Geometrie ist nicht sinnvoll legbar, da mindestens ein Riemensegment "
                    "durch ein anderes Element laufen würde. Bitte Positionen anpassen."
                )

    arcs: List[Arc] = []
    total_length = 0.0

    for pos in range(n):
        idx = order[pos]
        w = wheels[idx]
        p_in = tangents_in[pos]
        p_out = tangents_out[pos]
        if p_in is None or p_out is None:
            raise ValueError("Interner Geometriefehler bei der Bogenberechnung.")

        start_angle, extent_angle, arc_len, mid_point = choose_arc_by_centroid(
            (w.x, w.y), w.radius, p_in, p_out, centroid, prefer_outer
        )

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


# ============================================================
# GUI
# ============================================================

class BeltDesignerApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Riementrieb Konstruktion 2D")
        self.root.geometry("1500x900")
        self.root.minsize(1250, 760)

        self.wheels: List[Wheel] = []
        self.next_id = 1
        self.selected_index: Optional[int] = None
        self.dragging = False
        self.drag_offset = (0.0, 0.0)
        self.solution: Optional[BeltSolution] = None

        self._build_ui()
        self._add_demo_data()
        self.refresh_list()
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

        right = ttk.Frame(self.root, padding=(0, 8, 8, 8))
        right.grid(row=0, column=1, sticky="ns")
        right.columnconfigure(0, weight=1)
        right.rowconfigure(4, weight=1)

        ttk.Label(right, text="Parameter", font=("Segoe UI", 11, "bold")).grid(
            row=0, column=0, sticky="w", pady=(0, 8)
        )

        profile_box = ttk.LabelFrame(right, text="Riemen / Zahnprofil", padding=8)
        profile_box.grid(row=1, column=0, sticky="ew", pady=(0, 8))
        profile_box.columnconfigure(1, weight=1)

        self.pitch_var = tk.StringVar(value="5.0")
        self.tooth_height_var = tk.StringVar(value="1.9")
        self.tooth_top_var = tk.StringVar(value="1.5")
        self.tooth_root_var = tk.StringVar(value="2.4")
        self.belt_width_var = tk.StringVar(value="10.0")

        self._entry_row(profile_box, 0, "Teilung [mm]", self.pitch_var)
        self._entry_row(profile_box, 1, "Zahnhöhe [mm]", self.tooth_height_var)
        self._entry_row(profile_box, 2, "Zahnkopfbreite [mm]", self.tooth_top_var)
        self._entry_row(profile_box, 3, "Zahnfußbreite [mm]", self.tooth_root_var)
        self._entry_row(profile_box, 4, "Riemenbreite [mm]", self.belt_width_var)

        wheels_box = ttk.LabelFrame(right, text="Pulleys / Rollen", padding=8)
        wheels_box.grid(row=2, column=0, sticky="ew", pady=(0, 8))
        wheels_box.columnconfigure(0, weight=1)

        self.wheel_list = tk.Listbox(wheels_box, height=12, exportselection=False, activestyle="none")
        self.wheel_list.grid(row=0, column=0, columnspan=3, sticky="ew")
        self.wheel_list.bind("<<ListboxSelect>>", self.on_list_select)

        btn_row1 = ttk.Frame(wheels_box)
        btn_row1.grid(row=1, column=0, columnspan=3, sticky="ew", pady=(8, 6))
        btn_row1.columnconfigure((0, 1, 2), weight=1)

        ttk.Button(btn_row1, text="Pulley hinzufügen", command=self.add_pulley).grid(row=0, column=0, padx=2, sticky="ew")
        ttk.Button(btn_row1, text="Rolle hinzufügen", command=self.add_roller).grid(row=0, column=1, padx=2, sticky="ew")
        ttk.Button(btn_row1, text="Löschen", command=self.delete_selected).grid(row=0, column=2, padx=2, sticky="ew")

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

        ttk.Button(edit, text="Änderungen übernehmen", command=self.apply_selected_edit).grid(
            row=5, column=0, columnspan=2, sticky="ew", pady=(6, 0)
        )

        action_box = ttk.LabelFrame(right, text="Berechnung", padding=8)
        action_box.grid(row=3, column=0, sticky="ew", pady=(0, 8))
        action_box.columnconfigure((0, 1), weight=1)

        self.path_mode_var = tk.StringVar(value="Außenkontur")
        self._combo_row(
            action_box,
            0,
            "Riemenführung",
            self.path_mode_var,
            ["Außenkontur", "Innenkontur"],
        )

        ttk.Button(action_box, text="Riemen berechnen", command=self.calculate).grid(row=1, column=0, padx=2, pady=2, sticky="ew")
        ttk.Button(action_box, text="Ansicht aktualisieren", command=self.redraw).grid(row=1, column=1, padx=2, pady=2, sticky="ew")

        result_box = ttk.LabelFrame(right, text="Ergebnis", padding=8)
        result_box.grid(row=4, column=0, sticky="nsew")
        result_box.rowconfigure(0, weight=1)
        result_box.columnconfigure(0, weight=1)

        self.result_text = tk.Text(result_box, wrap="word", font=("Consolas", 10), state="disabled")
        self.result_text.grid(row=0, column=0, sticky="nsew")

    def _entry_row(self, parent, row: int, label: str, variable: tk.StringVar) -> None:
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w", pady=2, padx=(0, 8))
        ttk.Entry(parent, textvariable=variable, width=18).grid(row=row, column=1, sticky="ew", pady=2)

    def _combo_row(self, parent, row: int, label: str, variable: tk.StringVar, values: List[str]) -> None:
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w", pady=2, padx=(0, 8))
        cb = ttk.Combobox(parent, textvariable=variable, values=values, state="readonly")
        cb.grid(row=row, column=1, sticky="ew", pady=2)

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
            raise ValueError(f"{name}: ungültiger Wert.")
        if positive and v <= 0:
            raise ValueError(f"{name} muss > 0 sein.")
        return v

    def get_pitch(self) -> float:
        return self.parse_float(self.pitch_var.get(), "Teilung", positive=True)

    def get_tooth_height(self) -> float:
        return self.parse_float(self.tooth_height_var.get(), "Zahnhöhe", positive=True)

    def get_tooth_top(self) -> float:
        return self.parse_float(self.tooth_top_var.get(), "Zahnkopfbreite", positive=True)

    def get_tooth_root(self) -> float:
        return self.parse_float(self.tooth_root_var.get(), "Zahnfußbreite", positive=True)

    def get_belt_width(self) -> float:
        return self.parse_float(self.belt_width_var.get(), "Riemenbreite", positive=True)

    # --------------------------------------------------------
    # Listen / Auswahl
    # --------------------------------------------------------

    def refresh_list(self) -> None:
        self.wheel_list.delete(0, tk.END)
        pitch_ok = True
        try:
            pitch = self.get_pitch()
        except Exception:
            pitch_ok = False
            pitch = 5.0

        for idx, w in enumerate(self.wheels):
            if w.kind == "Pulley" and pitch_ok:
                z_exact = w.derived_teeth_exact(pitch)
                z_round = w.derived_teeth_rounded(pitch)
                text = (
                    f"{idx+1:02d}. {w.name} | {w.kind} | D={w.diameter:.3f} mm | "
                    f"Z≈{z_exact:.3f} -> {z_round:d} | ({w.x:.1f}, {w.y:.1f})"
                )
            else:
                text = (
                    f"{idx+1:02d}. {w.name} | {w.kind} | D={w.diameter:.3f} mm | "
                    f"({w.x:.1f}, {w.y:.1f})"
                )
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
        self.wheels.append(
            Wheel(self.next_id, f"Pulley {idx}", 350 + 40 * (idx % 4), 260 + 40 * (idx % 3), 40.0, "Pulley")
        )
        self.next_id += 1
        self.selected_index = len(self.wheels) - 1
        self.solution = None
        self.refresh_list()
        self.redraw()

    def add_roller(self) -> None:
        idx = len(self.wheels) + 1
        self.wheels.append(
            Wheel(self.next_id, f"Rolle {idx}", 380 + 40 * (idx % 4), 290 + 40 * (idx % 3), 30.0, "Rolle")
        )
        self.next_id += 1
        self.selected_index = len(self.wheels) - 1
        self.solution = None
        self.refresh_list()
        self.redraw()

    def delete_selected(self) -> None:
        if self.selected_index is None:
            return
        if not (0 <= self.selected_index < len(self.wheels)):
            return
        del self.wheels[self.selected_index]
        if not self.wheels:
            self.selected_index = None
        else:
            self.selected_index = min(self.selected_index, len(self.wheels) - 1)
        self.solution = None
        self.refresh_list()
        self.redraw()

    def duplicate_selected(self) -> None:
        if self.selected_index is None:
            return
        w = self.wheels[self.selected_index]
        copy = Wheel(self.next_id, f"{w.name} Kopie", w.x + 40, w.y + 40, w.diameter, w.kind)
        self.next_id += 1
        self.wheels.insert(self.selected_index + 1, copy)
        self.selected_index += 1
        self.solution = None
        self.refresh_list()
        self.redraw()

    def move_up(self) -> None:
        if self.selected_index is None or self.selected_index <= 0:
            return
        i = self.selected_index
        self.wheels[i - 1], self.wheels[i] = self.wheels[i], self.wheels[i - 1]
        self.selected_index -= 1
        self.solution = None
        self.refresh_list()
        self.redraw()

    def move_down(self) -> None:
        if self.selected_index is None or self.selected_index >= len(self.wheels) - 1:
            return
        i = self.selected_index
        self.wheels[i + 1], self.wheels[i] = self.wheels[i], self.wheels[i + 1]
        self.selected_index += 1
        self.solution = None
        self.refresh_list()
        self.redraw()

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
            messagebox.showerror("Ungültige Eingabe", str(e))
            return

        w = self.wheels[self.selected_index]
        w.name = name
        w.kind = kind
        w.diameter = diameter
        w.x = x
        w.y = y

        self.solution = None
        self.refresh_list()
        self.redraw()

    # --------------------------------------------------------
    # Drag & Drop
    # --------------------------------------------------------

    def hit_test(self, x: float, y: float) -> Optional[int]:
        best = None
        best_d = float("inf")
        for i, w in enumerate(self.wheels):
            d = math.hypot(x - w.x, y - w.y)
            if d <= max(8.0, w.radius + 8.0) and d < best_d:
                best = i
                best_d = d
        return best

    def on_canvas_down(self, event) -> None:
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        idx = self.hit_test(x, y)
        if idx is None:
            self.dragging = False
            return

        self.selected_index = idx
        self.dragging = True
        w = self.wheels[idx]
        self.drag_offset = (x - w.x, y - w.y)
        self.refresh_list()
        self.redraw()

    def on_canvas_drag(self, event) -> None:
        if not self.dragging or self.selected_index is None:
            return
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        w = self.wheels[self.selected_index]
        w.x = x - self.drag_offset[0]
        w.y = y - self.drag_offset[1]
        self.solution = None
        self.refresh_list()
        self.redraw()

    def on_canvas_up(self, _event) -> None:
        self.dragging = False

    # --------------------------------------------------------
    # Berechnung
    # --------------------------------------------------------

    def calculate(self) -> None:
        try:
            pitch = self.get_pitch()
            tooth_height = self.get_tooth_height()
            tooth_top = self.get_tooth_top()
            tooth_root = self.get_tooth_root()
            belt_width = self.get_belt_width()

            if len(self.wheels) < 2:
                raise ValueError("Mindestens 2 Elemente erforderlich.")

            for w in self.wheels:
                if w.diameter <= 0:
                    raise ValueError(f"{w.name}: Durchmesser muss > 0 sein.")

            prefer_outer = self.path_mode_var.get() != "Innenkontur"
            mode_name = "Außenkontur" if prefer_outer else "Innenkontur"

            order_auto = sensible_order(self.wheels)
            order_manual = list(range(len(self.wheels)))
            order_candidates: List[Tuple[str, List[int]]] = []
            seen_orders = set()

            def add_order(name: str, order_choice: List[int]) -> None:
                key = tuple(order_choice)
                if key in seen_orders:
                    return
                seen_orders.add(key)
                order_candidates.append((name, order_choice))

            add_order("Automatisch", order_auto)
            add_order("Automatisch (umgekehrt)", list(reversed(order_auto)))
            add_order("Listenreihenfolge", order_manual)
            add_order("Listenreihenfolge (umgekehrt)", list(reversed(order_manual)))

            mode_candidates = [
                (prefer_outer, mode_name, False),
                (not prefer_outer, "Innenkontur" if prefer_outer else "Außenkontur", True),
            ]

            self.solution = None
            fallback_used = False
            used_mode_name = mode_name
            used_order_name = "Automatisch"
            last_error: Optional[Exception] = None

            for mode_pref, candidate_mode_name, is_mode_fallback in mode_candidates:
                for order_name, order_choice in order_candidates:
                    try:
                        self.solution = compute_belt_solution(
                            self.wheels,
                            prefer_outer=mode_pref,
                            order=order_choice,
                        )
                        fallback_used = is_mode_fallback
                        used_mode_name = candidate_mode_name
                        used_order_name = order_name
                        break
                    except ValueError as e:
                        last_error = e
                if self.solution is not None:
                    break

            if self.solution is None:
                if last_error is not None:
                    raise last_error
                raise ValueError("Keine legbare Riemengeometrie gefunden.")

            length_exact = self.solution.total_length
            belt_teeth_exact = length_exact / pitch
            belt_teeth_rounded = max(1, int(round(belt_teeth_exact)))
            length_corrected = belt_teeth_rounded * pitch
            length_delta = length_corrected - length_exact
            equivalent_diameter_exact = length_exact / math.pi
            equivalent_diameter_corrected = length_corrected / math.pi

            lines = []
            lines.append("RIEMENTRIEB BERECHNUNG")
            lines.append("=" * 80)
            lines.append("")
            lines.append("Riemen / Zahnprofil")
            lines.append(f"  Teilung                           : {pitch:.4f} mm")
            lines.append(f"  Zahnhöhe                          : {tooth_height:.4f} mm")
            lines.append(f"  Zahnkopfbreite                    : {tooth_top:.4f} mm")
            lines.append(f"  Zahnfußbreite                     : {tooth_root:.4f} mm")
            lines.append(f"  Riemenbreite                      : {belt_width:.4f} mm")
            lines.append("")

            lines.append("Riemen")
            lines.append(f"  Gewählte Führung                 : {mode_name}")
            if fallback_used:
                lines.append(f"  Verwendete Führung               : {used_mode_name} (Fallback)")
            else:
                lines.append(f"  Verwendete Führung               : {used_mode_name}")
            lines.append(f"  Verwendete Reihenfolge           : {used_order_name}")
            lines.append(f"  Exakte Riemenlänge                : {length_exact:.4f} mm")
            lines.append(f"  Exakte Zahnzahl                   : {belt_teeth_exact:.4f}")
            lines.append(f"  Gerundete Zahnzahl                : {belt_teeth_rounded:d}")
            lines.append(f"  Korrigierte Riemenlänge           : {length_corrected:.4f} mm")
            lines.append(f"  Längenabweichung                  : {length_delta:+.4f} mm")
            lines.append("")

            lines.append("Ersatz-Kreis für runde Konstruktion")
            lines.append(f"  Durchmesser aus exakter Länge     : {equivalent_diameter_exact:.4f} mm")
            lines.append(f"  Durchmesser aus korrigierter Länge: {equivalent_diameter_corrected:.4f} mm")
            lines.append("")

            lines.append("Elemente")
            ordered_names = []
            for pos, idx in enumerate(self.solution.order, start=1):
                w = self.wheels[idx]
                ordered_names.append(w.name)
                if w.kind == "Pulley":
                    z_exact = w.derived_teeth_exact(pitch)
                    z_round = w.derived_teeth_rounded(pitch)
                    d_corr = w.corrected_pitch_diameter(pitch)
                    diff = d_corr - w.diameter
                    lines.append(
                        f"  {pos:02d}. {w.name:<20} Typ=Pulley  "
                        f"D_eingegeben={w.diameter:>9.4f} mm  "
                        f"Z_exakt={z_exact:>8.4f}  "
                        f"Z_verwendet={z_round:>4d}  "
                        f"D_korrigiert={d_corr:>9.4f} mm  "
                        f"Abweichung={diff:+.4f} mm  "
                        f"Pos=({w.x:>8.3f}, {w.y:>8.3f})"
                    )
                else:
                    lines.append(
                        f"  {pos:02d}. {w.name:<20} Typ=Rolle   "
                        f"D={w.diameter:>9.4f} mm  "
                        f"Pos=({w.x:>8.3f}, {w.y:>8.3f})"
                    )
            lines.append("")

            lines.append("Automatisch gewählte sinnvolle Riemenreihenfolge")
            lines.append("  " + "  ->  ".join(ordered_names))
            lines.append("")

            lines.append("Achsabstände")
            for seg in self.solution.segments:
                wa = self.wheels[seg.a_idx]
                wb = self.wheels[seg.b_idx]
                lines.append(
                    f"  {wa.name:<20} -> {wb.name:<20} : {seg.center_distance:>10.4f} mm"
                )
            lines.append("")

            lines.append("Geradensegmente des Riemens")
            for seg in self.solution.segments:
                wa = self.wheels[seg.a_idx]
                wb = self.wheels[seg.b_idx]
                lines.append(
                    f"  {wa.name:<20} -> {wb.name:<20} : {seg.length:>10.4f} mm"
                )
            lines.append("")

            lines.append("Bogenanteile am Riemen")
            for arc in self.solution.arcs:
                w = self.wheels[arc.idx]
                wrap_deg = abs(math.degrees(arc.extent_angle))
                lines.append(
                    f"  {w.name:<20} : Bogenlänge={arc.length:>10.4f} mm   Umschlingung={wrap_deg:>9.4f}°"
                )
            lines.append("")

            lines.append("Zahnmaße für schnelle Konstruktion")
            lines.append(f"  Teilung                           : {pitch:.4f} mm")
            lines.append(f"  Zahnhöhe                          : {tooth_height:.4f} mm")
            lines.append(f"  Zahnkopfbreite                    : {tooth_top:.4f} mm")
            lines.append(f"  Zahnfußbreite                     : {tooth_root:.4f} mm")
            lines.append("")

            lines.append("Hinweise")
            lines.append("  - Bei Pulleys ist der eingegebene Durchmesser als Teilkreisdurchmesser zu verstehen.")
            lines.append("  - Die Pulley-Zahnzahl wird aus Teilung und Teilkreisdurchmesser bestimmt.")
            lines.append("  - Der Riemen wird auf die nächstliegende ganze Zahnzahl gerundet.")
            lines.append("  - Stimmen eingegebener Pulley-Durchmesser und ganzzahlige Zahnzahl nicht exakt zusammen,")
            lines.append("    wird der korrigierte Teilkreisdurchmesser zusätzlich angezeigt.")
            lines.append("  - Riemenführung kann als Außen- oder Innenkontur gewählt werden.")
            if fallback_used:
                lines.append("  - Hinweis: Die gewünschte Führung war geometrisch nicht legbar, daher wurde automatisch die Alternative verwendet.")
            if used_order_name != "Automatisch":
                lines.append("  - Hinweis: Für eine legbare Geometrie wurde statt der automatischen Reihenfolge die Listenreihenfolge verwendet.")

            self.set_result_text("\n".join(lines))
            self.redraw()

        except Exception as e:
            self.solution = None
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

        for i, w in enumerate(self.wheels):
            self.draw_wheel(w, selected=(i == self.selected_index))

        self.draw_legend()

    def draw_grid(self) -> None:
        w = max(1200, self.canvas.winfo_width())
        h = max(800, self.canvas.winfo_height())

        minor = 25
        major = 100

        for x in range(0, w + 1, minor):
            color = "#eef2f6" if x % major else "#d7dee7"
            self.canvas.create_line(x, 0, x, h, fill=color)

        for y in range(0, h + 1, minor):
            color = "#eef2f6" if y % major else "#d7dee7"
            self.canvas.create_line(0, y, w, y, fill=color)

        self.canvas.create_text(10, 10, anchor="nw", text="2D-Koordinatensystem [mm]", fill="#4d5b6a")

    def draw_wheel(self, wheel: Wheel, selected: bool) -> None:
        r = wheel.radius
        x1 = wheel.x - r
        y1 = wheel.y - r
        x2 = wheel.x + r
        y2 = wheel.y + r

        if wheel.kind == "Pulley":
            fill = "#d9eefb"
            outline = "#1d5f8c"
        else:
            fill = "#efe5fb"
            outline = "#6a4c93"

        if selected:
            outline = "#d00000"

        self.canvas.create_oval(x1, y1, x2, y2, fill=fill, outline=outline, width=2)
        self.canvas.create_line(wheel.x - r, wheel.y, wheel.x + r, wheel.y, fill="#8aa5bf", dash=(3, 2))
        self.canvas.create_line(wheel.x, wheel.y - r, wheel.x, wheel.y + r, fill="#8aa5bf", dash=(3, 2))
        self.canvas.create_oval(wheel.x - 3, wheel.y - 3, wheel.x + 3, wheel.y + 3, fill=outline, outline="")

        label = f"{wheel.name}\nD={wheel.diameter:.2f} mm"
        self.canvas.create_text(
            wheel.x,
            wheel.y - r - 14,
            text=label,
            fill="#1b263b",
            font=("Segoe UI", 9, "bold"),
        )

    def draw_solution(self, solution: BeltSolution) -> None:
        # Geraden
        for seg in solution.segments:
            self.canvas.create_line(
                seg.p1[0], seg.p1[1], seg.p2[0], seg.p2[1],
                fill="#0a9396",
                width=3,
            )

        # Bögen
        for arc in solution.arcs:
            cx, cy = arc.center
            r = arc.radius
            bbox = (cx - r, cy - r, cx + r, cy + r)

            start_deg = -math.degrees(arc.start_angle)
            extent_deg = -math.degrees(arc.extent_angle)

            self.canvas.create_arc(
                bbox,
                start=start_deg,
                extent=extent_deg,
                style="arc",
                outline="#0a9396",
                width=3,
            )

            self.canvas.create_oval(
                arc.p_in[0] - 3, arc.p_in[1] - 3, arc.p_in[0] + 3, arc.p_in[1] + 3,
                fill="#ee9b00", outline=""
            )
            self.canvas.create_oval(
                arc.p_out[0] - 3, arc.p_out[1] - 3, arc.p_out[0] + 3, arc.p_out[1] + 3,
                fill="#ca6702", outline=""
            )

        # Schwerpunkt der automatisch ermittelten Außenkontur
        cx, cy = solution.centroid
        self.canvas.create_oval(cx - 4, cy - 4, cx + 4, cy + 4, fill="#444", outline="")
        self.canvas.create_text(cx + 8, cy - 8, anchor="nw", text="Schwerpunkt", fill="#444", font=("Segoe UI", 8))

    def draw_legend(self) -> None:
        w = max(1200, self.canvas.winfo_width())
        x = w - 320
        y = 14
        self.canvas.create_rectangle(x, y, x + 305, y + 128, fill="white", outline="#ccd6dd")
        self.canvas.create_text(x + 10, y + 10, anchor="nw", text="Legende", font=("Segoe UI", 10, "bold"))
        self.canvas.create_line(x + 12, y + 34, x + 54, y + 34, fill="#0a9396", width=3)
        self.canvas.create_text(x + 62, y + 34, anchor="w", text="berechnete geschlossene Riemenführung")
        self.canvas.create_oval(x + 12, y + 50, x + 24, y + 62, fill="#ee9b00", outline="")
        self.canvas.create_text(x + 32, y + 56, anchor="w", text="Tangenzpunkt Eintritt")
        self.canvas.create_oval(x + 12, y + 70, x + 24, y + 82, fill="#ca6702", outline="")
        self.canvas.create_text(x + 32, y + 76, anchor="w", text="Tangenzpunkt Austritt")
        self.canvas.create_oval(x + 12, y + 92, x + 24, y + 104, fill="#444", outline="")
        self.canvas.create_text(x + 32, y + 98, anchor="w", text="Schwerpunkt für Konturauswahl")
        self.canvas.create_text(
            x + 10,
            y + 116,
            anchor="nw",
            text="Pulley: eingegebener D = Teilkreisdurchmesser",
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
