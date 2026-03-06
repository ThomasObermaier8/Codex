# win_keyboard_overlay_de_bootcamp.py
# Windows DE (Deutschland) Keyboard Visual + Apple/MacBook Boot Camp overlay
# Hover any key (physical or special-character virtual key) -> show Apple equivalent + how to type.
#
# Assumptions:
# - Windows layout: Deutsch (Deutschland) - ISO (typical German keyboard)
# - MacBook keyboard under Windows with Boot Camp drivers
# - Right Option (⌥) exists and acts as AltGr

import tkinter as tk
from tkinter import ttk

APP_TITLE = "Windows (DE) Tastatur → MacBook (Boot Camp) Overlay (Hover für Infos)"

# -----------------------------
# Helpers / canonical concepts
# -----------------------------
ALTGR_NOTE = "AltGr (DE)\nBoot Camp: i.d.R. die rechte ⌥ Option-Taste.\nFallback (Windows-üblich): Ctrl + Alt kann AltGr ersetzen."

def info_for_physical(label: str) -> str:
    # default fallback
    if len(label) == 1:
        return (
            f"Taste: {label}\n"
            "Apple-Äquivalent: abhängig vom Layout (meist identisch als Zeichen).\n"
            "Hinweis: Sonderzeichen hängen vom Windows-Tastaturlayout ab."
        )
    return (
        f"Taste: {label}\n"
        "Kein spezifisches Mapping hinterlegt.\n"
        "Erweitere KEY_INFO, wenn du dafür eine Erklärung möchtest."
    )

# -----------------------------
# Physical keyboard layout (DE ISO-ish, simplified)
# -----------------------------
# Each row is a list of:
# - string label (default width 1.0)
# - tuple(label, width_multiplier)
LAYOUT = [
    ["Esc", "F1", "F2", "F3", "F4", "F5", "F6", "F7", "F8", "F9", "F10", "F11", "F12", "PrtSc"],
    ["^", "1", "2", "3", "4", "5", "6", "7", "8", "9", "0", "ß", "´", ("Backspace", 2.2)],
    [("Tab", 1.6), "Q", "W", "E", "R", "T", "Z", "U", "I", "O", "P", "Ü", "+", "#"],
    [("Caps", 1.9), "A", "S", "D", "F", "G", "H", "J", "K", "L", "Ö", "Ä", ("Enter", 2.1)],
    [("Shift", 2.4), "<", "Y", "X", "C", "V", "B", "N", "M", ",", ".", "-", ("Shift", 2.7)],
    # Bottom row: show right Option explicitly as AltGr
    [("Ctrl", 1.5), ("Win", 1.5), ("Alt", 1.5), ("Space", 6.5), ("AltGr", 1.8), ("Win", 1.5), ("Menu", 1.5), ("Ctrl", 1.5)],
    # Arrows cluster (simple)
    ["", "", "", "↑", "", "", "←", "↓", "→"],
]

# -----------------------------
# Special characters as separate "virtual keys"
# -----------------------------
# Each item: (display_char, how_to_type)
# Use DE Windows conventions:
SPECIAL_KEYS = [
    # Number row base
    ("^",  "Taste ^ (Dead Key): erst ^ drücken, dann z.B. a → â; oder Space → ^"),
    ("´",  "Taste ´ (Dead Key): erst ´ drücken, dann z.B. e → é; oder Space → ´"),
    ("ß",  "ß (direkt)"),

    # Shift layer on number row
    ("°",  "Shift + ^"),
    ("!",  "Shift + 1"),
    ("\"", "Shift + 2"),
    ("§",  "Shift + 3"),
    ("$",  "Shift + 4"),
    ("%",  "Shift + 5"),
    ("&",  "Shift + 6"),
    ("/",  "Shift + 7"),
    ("(",  "Shift + 8"),
    (")",  "Shift + 9"),
    ("=",  "Shift + 0"),
    ("?",  "Shift + ß"),
    ("`",  "Shift + ´ (Dead Key: ` dann z.B. e → è; oder Space → `)"),

    # Other physical keys / shift variants
    ("<",  "< (direkt)"),
    (">",  "Shift + <"),
    ("|",  "AltGr + <"),
    ("+",  "+ (direkt)"),
    ("*",  "Shift + +"),
    ("~",  "AltGr + +"),
    ("#",  "# (direkt)"),
    ("'",  "Shift + #"),

    (",",  ", (direkt)"),
    (";",  "Shift + ,"),
    (".",  ". (direkt)"),
    (":",  "Shift + ."),
    ("-",  "- (direkt)"),
    ("_",  "Shift + -"),

    # AltGr layer core (DE)
    ("@",  "AltGr + Q"),
    ("€",  "AltGr + E"),
    ("{",  "AltGr + 7"),
    ("[",  "AltGr + 8"),
    ("]",  "AltGr + 9"),
    ("}",  "AltGr + 0"),
    ("\\", "AltGr + ß"),
    ("µ",  "AltGr + M"),

    # Umlauts / letters as separate characters too (user asked: every key & every special char as own key)
    ("ä",  "ä (direkt)"),
    ("ö",  "ö (direkt)"),
    ("ü",  "ü (direkt)"),
    ("Ä",  "Shift + ä (Taste Ä)"),
    ("Ö",  "Shift + ö (Taste Ö)"),
    ("Ü",  "Shift + ü (Taste Ü)"),
]

# -----------------------------
# Core mapping: hover label -> info text
# -----------------------------
KEY_INFO = {
    # Modifiers & system keys
    "Win": "Windows-Taste\nApple-Äquivalent: ⌘ Command (Mac)\nBoot Camp unter Windows: ⌘ entspricht i.d.R. der Windows-Taste (Win).\nBeispiele: Win+L (Sperren), Win+E (Explorer), Win+R (Ausführen).",
    "Alt": "Alt (links)\nApple-Äquivalent: ⌥ Option (Mac)\nUnter Windows: Alt bleibt Alt.\nHinweis: AltGr ist NICHT Alt links, sondern Alt rechts (= rechte ⌥).",
    "AltGr": ALTGR_NOTE + "\n\nBeispiele:\n@ = AltGr+Q\n€ = AltGr+E\n{[ ]} = AltGr+7/8/9/0\n\\ = AltGr+ß\n| = AltGr+<\n~ = AltGr++\nµ = AltGr+M",
    "Ctrl": "Strg/Ctrl\nApple-Äquivalent: ⌃ Control (Mac)\nUnter Windows: Strg = Ctrl (unverändert).\nTypisch: Ctrl+C/V/X/Z etc.",
    "Shift": "Shift\nApple-Äquivalent: ⇧ Shift (Mac)\nUnter Windows: Shift = Shift (unverändert).",
    "Fn": "Fn\nMacBook: Fn bleibt Fn.\nHinweis: Fn-Logik (Medientasten vs F-Tasten) hängt von Boot-Camp/Windows-Einstellungen ab.",
    "Esc": "Esc\nApple-Äquivalent: Esc\nUnter Windows: Esc = Esc.",
    "Tab": "Tab\nApple-Äquivalent: ⇥ Tab\nUnter Windows: Tab = Tab.\nShortcut: Alt+Tab (Fenster wechseln).",
    "Caps": "Caps Lock\nApple-Äquivalent: ⇪ Caps Lock\nUnter Windows: Caps = Caps Lock.",
    "Enter": "Enter\nApple-Äquivalent: ⏎ Return/Enter\nUnter Windows: Enter = Enter.",
    "Backspace": "Backspace\nApple-Äquivalent: ⌫ Delete (Mac)\nWichtig: Auf dem Mac heißt Rückschritt-Löschen 'Delete' (⌫).",
    "Del": "Entf/Del\nApple-Äquivalent: ⌦ Forward Delete (Mac)\nMacBook ohne eigene Del-Taste: Fn + Backspace = Forward Delete (⌦).",
    "Home": "Home\nMacBook oft: Fn + ← = Home",
    "End": "End\nMacBook oft: Fn + → = End",
    "PgUp": "Bild↑ / Page Up\nMacBook oft: Fn + ↑ = Page Up",
    "PgDn": "Bild↓ / Page Down\nMacBook oft: Fn + ↓ = Page Down",
    "PrtSc": "Druck / Print Screen\nWindows: PrtSc oder Win+Shift+S.\nMacBook unter Windows: je nach Boot-Camp-Treiber ggf. Fn-Kombinationen möglich.",
    "Menu": "Kontextmenü-Taste\nAm MacBook meist nicht vorhanden.\nErsatz: Shift+F10 oder Rechtsklick/Trackpad-Klick.",
    "Space": "Leertaste\nApple-Äquivalent: Space\nUnter Windows: Space = Space.",
    "↑": "Pfeil ↑",
    "↓": "Pfeil ↓",
    "←": "Pfeil ←",
    "→": "Pfeil →",
}

# Add special-character keys into KEY_INFO so they hover like normal keys
for ch, how in SPECIAL_KEYS:
    # explain Apple equivalence conceptually: same glyph; typing method is what matters
    extra = ""
    if "AltGr" in how:
        extra = "\n\n" + ALTGR_NOTE
    KEY_INFO[ch] = f"Sonderzeichen: {ch}\nEingabe (Windows DE): {how}{extra}"

DEFAULT_INFO = (
    "Hover über eine Taste → rechts siehst du:\n"
    "• Apple-Äquivalent (Mac-Taste)\n"
    "• Windows-DE Eingabe (inkl. AltGr)\n\n"
    "DE + Boot Camp Merker:\n"
    "• rechte ⌥ Option = AltGr\n"
    "• Forward Delete: Fn + Backspace\n"
    "• Home/End/PgUp/PgDn: oft Fn + Pfeile\n"
)

# -----------------------------
# UI
# -----------------------------
class KeyboardOverlayApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_TITLE)
        self.geometry("1180x720")
        self.minsize(1040, 640)
        self._build_ui()

    def _build_ui(self):
        root = ttk.Frame(self, padding=12)
        root.pack(fill="both", expand=True)

        # Left column: physical keyboard + special palette
        left = ttk.Frame(root)
        left.pack(side="left", fill="both", expand=True)

        # Right column: info panel
        right = ttk.Frame(root)
        right.pack(side="right", fill="both", expand=False, padx=(12, 0))

        # Titles
        ttk.Label(left, text="Windows Tastatur (Deutsch – Deutschland) – physische Tasten", font=("Segoe UI", 12, "bold")).pack(anchor="w")
        ttk.Label(left, text="(Hover auf Taste zeigt Apple/AltGr-Overlay rechts)", font=("Segoe UI", 9)).pack(anchor="w", pady=(2, 0))

        # Physical keyboard area
        kb = ttk.Frame(left)
        kb.pack(fill="x", pady=(10, 8))

        # Info panel
        self.info_title = ttk.Label(right, text="Info", font=("Segoe UI", 12, "bold"))
        self.info_title.pack(anchor="w")

        self.info_text = tk.Text(
            right,
            width=44,
            height=32,
            wrap="word",
            font=("Segoe UI", 10),
            borderwidth=1,
            relief="solid"
        )
        self.info_text.pack(fill="both", expand=True)
        self._set_info("—", DEFAULT_INFO)

        # Button style
        style = ttk.Style(self)
        style.configure("Key.TButton", padding=(8, 10), font=("Segoe UI", 10))
        style.configure("KeySmall.TButton", padding=(6, 8), font=("Segoe UI", 9))

        # Build physical keyboard rows
        for row in LAYOUT:
            row_frame = ttk.Frame(kb)
            row_frame.pack(anchor="w", pady=3, fill="x")
            col = 0
            for item in row:
                if item == "":
                    spacer = ttk.Frame(row_frame, width=24)
                    spacer.grid(row=0, column=col, padx=2)
                    col += 1
                    continue

                if isinstance(item, tuple):
                    label, w = item
                else:
                    label, w = item, 1.0

                btn_style = "Key.TButton" if len(label) <= 4 else "KeySmall.TButton"
                b = ttk.Button(row_frame, text=label, style=btn_style)
                b.grid(row=0, column=col, padx=2, sticky="nsew")
                row_frame.grid_columnconfigure(col, weight=int(w * 10))
                b.configure(width=max(3, int(w * 6)))

                b.bind("<Enter>", lambda e, k=label: self._on_hover(k))
                b.bind("<Leave>", lambda e: self._on_leave())
                col += 1

        # Separator
        ttk.Separator(left).pack(fill="x", pady=10)

        # Special character palette title
        ttk.Label(left, text="Sonderzeichen-Palette (jedes Sonderzeichen als eigene Taste)", font=("Segoe UI", 12, "bold")).pack(anchor="w")

        # Scrollable palette (in case you want to add more later)
        palette_container = ttk.Frame(left)
        palette_container.pack(fill="both", expand=True, pady=(8, 0))

        canvas = tk.Canvas(palette_container, borderwidth=0, highlightthickness=0)
        vsb = ttk.Scrollbar(palette_container, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=vsb.set)

        vsb.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        palette_frame = ttk.Frame(canvas)
        canvas.create_window((0, 0), window=palette_frame, anchor="nw")

        def _on_frame_configure(event):
            canvas.configure(scrollregion=canvas.bbox("all"))

        palette_frame.bind("<Configure>", _on_frame_configure)

        # Build special keys grid
        # We group them in a predictable order; each as its own hoverable button.
        cols = 12
        r = 0
        c = 0

        for ch, how in SPECIAL_KEYS:
            # Wider buttons for whitespace-like or multi-char displays (not used here)
            text = ch

            # Make readable labels for quote/backslash
            display = text
            if ch == "\\":
                display = "⧵"  # nicer glyph on button; hover still mapped by original "\"
            elif ch == "\"":
                display = "\""

            b = ttk.Button(palette_frame, text=display, style="Key.TButton", width=4)
            b.grid(row=r, column=c, padx=3, pady=3, sticky="nsew")

            # Bind hover with the actual character key
            b.bind("<Enter>", lambda e, k=ch: self._on_hover(k))
            b.bind("<Leave>", lambda e: self._on_leave())

            c += 1
            if c >= cols:
                c = 0
                r += 1

        ttk.Label(
            left,
            text="Hinweis: Dead Keys (^, ´, `) erzeugen erst mit Folgetaste ein Zeichen (z.B. ´ + e = é) oder mit Space das Symbol.",
            font=("Segoe UI", 9)
        ).pack(anchor="w", pady=(10, 0))

    def _set_info(self, key: str, info: str):
        self.info_title.configure(text=f"Info: {key}")
        self.info_text.configure(state="normal")
        self.info_text.delete("1.0", "end")
        self.info_text.insert("1.0", info)
        self.info_text.configure(state="disabled")

    def _on_hover(self, key: str):
        info = KEY_INFO.get(key)
        if info is None:
            info = info_for_physical(key)
        self._set_info(key, info)

    def _on_leave(self):
        self._set_info("—", DEFAULT_INFO)

if __name__ == "__main__":
    app = KeyboardOverlayApp()
    app.mainloop()