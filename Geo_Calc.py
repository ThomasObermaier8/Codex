import math
import tkinter as tk
from tkinter import ttk, messagebox


class AdvancedGeometryApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Erweiterte Geometrie- und Wissenschaftsrechner-GUI")
        self.root.geometry("1450x900")
        self.root.minsize(1200, 780)

        self.last_results = {}
        self.result_order = []

        self.shapes = {
            "2D Grundformen": {
                "Rechteck": {
                    "params": [("a", "Länge a"), ("b", "Breite b")],
                    "formulas": [
                        "Fläche: A = a · b",
                        "Umfang: U = 2(a + b)",
                        "Diagonale: d = √(a² + b²)",
                    ],
                    "calc": self.calc_rectangle,
                },
                "Quadrat": {
                    "params": [("a", "Seitenlänge a")],
                    "formulas": [
                        "Fläche: A = a²",
                        "Umfang: U = 4a",
                        "Diagonale: d = a√2",
                        "Inkreisradius: r_i = a/2",
                        "Umkreisradius: r_u = a/√2",
                    ],
                    "calc": self.calc_square,
                },
                "Kreis": {
                    "params": [("r", "Radius r")],
                    "formulas": [
                        "Fläche: A = πr²",
                        "Umfang: U = 2πr",
                        "Durchmesser: d = 2r",
                    ],
                    "calc": self.calc_circle,
                },
                "Ring / Kreisring": {
                    "params": [("R", "Außenradius R"), ("r", "Innenradius r")],
                    "formulas": [
                        "Fläche: A = π(R² - r²)",
                        "Außenumfang: U_a = 2πR",
                        "Innenumfang: U_i = 2πr",
                    ],
                    "calc": self.calc_annulus,
                },
                "Ellipse": {
                    "params": [("a", "Halbachse a"), ("b", "Halbachse b")],
                    "formulas": [
                        "Fläche: A = πab",
                        "Umfang (Ramanujan): U ≈ π[3(a+b) - √((3a+b)(a+3b))]",
                    ],
                    "calc": self.calc_ellipse,
                },
                "Sektor": {
                    "params": [("r", "Radius r"), ("alpha_deg", "Winkel α in Grad")],
                    "formulas": [
                        "Bogenlänge: s = 2πr · α/360",
                        "Fläche: A = πr² · α/360",
                        "Sehnenlänge: c = 2r·sin(α/2)",
                    ],
                    "calc": self.calc_sector,
                },
                "Kreissegment": {
                    "params": [("r", "Radius r"), ("alpha_deg", "Winkel α in Grad")],
                    "formulas": [
                        "Segmentfläche: A = (r²/2)(α - sin α), α in rad",
                        "Sehne: c = 2r·sin(α/2)",
                    ],
                    "calc": self.calc_segment,
                },
            },
            "2D Dreiecke/Vierecke": {
                "Dreieck allgemein": {
                    "params": [("a", "Seite a"), ("b", "Seite b"), ("c", "Seite c"), ("alpha_deg", "Winkel α (gegenüber a)"), ("beta_deg", "Winkel β (gegenüber b)"), ("gamma_deg", "Winkel γ (gegenüber c)"), ("h_a", "Höhe auf a (optional)")],
                    "formulas": [
                        "Umfang: U = a + b + c",
                        "Fläche: A = (a · h_a)/2",
                        "Heron: A = √(s(s-a)(s-b)(s-c)), s = U/2",
                    ],
                    "calc": self.calc_triangle_general,
                },
                "Rechtwinkliges Dreieck": {
                    "params": [("a", "Kathete a"), ("b", "Kathete b")],
                    "formulas": [
                        "Hypotenuse: c = √(a² + b²)",
                        "Fläche: A = ab/2",
                        "Umfang: U = a + b + c",
                        "Winkel: α = atan(b/a), β = atan(a/b)",
                    ],
                    "calc": self.calc_triangle_right,
                },
                "Gleichseitiges Dreieck": {
                    "params": [("a", "Seitenlänge a")],
                    "formulas": [
                        "Höhe: h = a√3/2",
                        "Fläche: A = a²√3/4",
                        "Umfang: U = 3a",
                        "Inkreisradius: r_i = a√3/6",
                        "Umkreisradius: r_u = a√3/3",
                    ],
                    "calc": self.calc_triangle_equilateral,
                },
                "Trapez": {
                    "params": [("a", "Grundseite a"), ("c", "Oberseite c"), ("h", "Höhe h"), ("b", "Seite b"), ("d", "Seite d")],
                    "formulas": [
                        "Fläche: A = ((a + c)/2) · h",
                        "Umfang: U = a + b + c + d",
                        "Mittellinie: m = (a + c)/2",
                    ],
                    "calc": self.calc_trapezoid,
                },
                "Parallelogramm": {
                    "params": [("a", "Seite a"), ("b", "Seite b"), ("h", "Höhe h"), ("alpha_deg", "Winkel α in Grad")],
                    "formulas": [
                        "Fläche: A = a · h = a·b·sin(α)",
                        "Umfang: U = 2(a+b)",
                    ],
                    "calc": self.calc_parallelogram,
                },
                "Raute": {
                    "params": [("a", "Seitenlänge a"), ("e", "Diagonale e"), ("f", "Diagonale f")],
                    "formulas": [
                        "Fläche: A = e·f/2",
                        "Umfang: U = 4a",
                    ],
                    "calc": self.calc_rhombus,
                },
                "Deltoid": {
                    "params": [("a", "Seite a"), ("b", "Seite b"), ("e", "Diagonale e"), ("f", "Diagonale f")],
                    "formulas": [
                        "Fläche: A = e·f/2",
                        "Umfang: U = 2(a+b)",
                    ],
                    "calc": self.calc_kite,
                },
            },
            "2D Regelmäßige Figuren": {
                "Regelmäßiges n-Eck": {
                    "params": [("n", "Anzahl Seiten n"), ("a", "Seitenlänge a")],
                    "formulas": [
                        "Innenwinkel: α = (n-2)·180°/n",
                        "Umfang: U = n·a",
                        "Apothem: r = a / (2 tan(π/n))",
                        "Umkreisradius: R = a / (2 sin(π/n))",
                        "Fläche: A = n·a² / (4 tan(π/n))",
                    ],
                    "calc": self.calc_regular_polygon,
                },
            },
            "3D Grundkörper": {
                "Würfel": {
                    "params": [("a", "Kantenlänge a")],
                    "formulas": [
                        "Volumen: V = a³",
                        "Oberfläche: O = 6a²",
                        "Raumdiagonale: d = a√3",
                    ],
                    "calc": self.calc_cube,
                },
                "Quader": {
                    "params": [("a", "Länge a"), ("b", "Breite b"), ("c", "Höhe c")],
                    "formulas": [
                        "Volumen: V = abc",
                        "Oberfläche: O = 2(ab + ac + bc)",
                        "Raumdiagonale: d = √(a²+b²+c²)",
                    ],
                    "calc": self.calc_cuboid,
                },
                "Kugel": {
                    "params": [("r", "Radius r")],
                    "formulas": [
                        "Volumen: V = 4/3 πr³",
                        "Oberfläche: O = 4πr²",
                    ],
                    "calc": self.calc_sphere,
                },
                "Halbkugel": {
                    "params": [("r", "Radius r")],
                    "formulas": [
                        "Volumen: V = 2/3 πr³",
                        "Mantel + Grundfläche: O = 3πr²",
                        "Nur Mantelfläche: M = 2πr²",
                    ],
                    "calc": self.calc_hemisphere,
                },
                "Zylinder": {
                    "params": [("r", "Radius r"), ("h", "Höhe h")],
                    "formulas": [
                        "Volumen: V = πr²h",
                        "Mantelfläche: M = 2πrh",
                        "Oberfläche: O = 2πr² + 2πrh",
                    ],
                    "calc": self.calc_cylinder,
                },
                "Rohr / Hohlzylinder": {
                    "params": [("R", "Außenradius R"), ("r", "Innenradius r"), ("h", "Höhe h")],
                    "formulas": [
                        "Volumen: V = π(R²-r²)h",
                        "Außenmantel: M_a = 2πRh",
                        "Innenmantel: M_i = 2πrh",
                        "Gesamtoberfläche: O = 2π(R²-r²) + 2πh(R+r)",
                    ],
                    "calc": self.calc_hollow_cylinder,
                },
                "Kegel": {
                    "params": [("r", "Radius r"), ("h", "Höhe h")],
                    "formulas": [
                        "Mantellinie: s = √(r²+h²)",
                        "Volumen: V = 1/3 πr²h",
                        "Mantelfläche: M = πrs",
                        "Oberfläche: O = πr² + πrs",
                    ],
                    "calc": self.calc_cone,
                },
                "Kegelstumpf": {
                    "params": [("R", "Großer Radius R"), ("r", "Kleiner Radius r"), ("h", "Höhe h")],
                    "formulas": [
                        "Mantellinie: s = √((R-r)² + h²)",
                        "Volumen: V = πh(R² + Rr + r²)/3",
                        "Mantelfläche: M = π(R+r)s",
                        "Oberfläche: O = M + πR² + πr²",
                    ],
                    "calc": self.calc_frustum,
                },
            },
            "3D Prismen/Pyramiden": {
                "Prisma": {
                    "params": [("G", "Grundfläche G"), ("U_G", "Grundumfang U_G"), ("h", "Höhe h")],
                    "formulas": [
                        "Volumen: V = G·h",
                        "Mantelfläche: M = U_G·h",
                        "Oberfläche: O = 2G + U_G·h",
                    ],
                    "calc": self.calc_prism,
                },
                "Pyramide": {
                    "params": [("G", "Grundfläche G"), ("h", "Höhe h"), ("M", "Mantelfläche M")],
                    "formulas": [
                        "Volumen: V = G·h/3",
                        "Oberfläche: O = G + M",
                    ],
                    "calc": self.calc_pyramid,
                },
                "Tetraeder regelmäßig": {
                    "params": [("a", "Kantenlänge a")],
                    "formulas": [
                        "Volumen: V = a³ / (6√2)",
                        "Oberfläche: O = √3 · a²",
                        "Höhe: h = a√(2/3)",
                    ],
                    "calc": self.calc_tetrahedron,
                },
            },
            "Trigonometrie / Analytik": {
                "Kreis / Winkel": {
                    "params": [("r", "Radius r"), ("alpha_deg", "Winkel α in Grad")],
                    "formulas": [
                        "Bogenmaß: α_rad = α_deg · π/180",
                        "Bogenlänge: s = r·α_rad",
                        "Sehne: c = 2r·sin(α/2)",
                    ],
                    "calc": self.calc_angle_circle,
                },
                "Kartesisch / Polar": {
                    "params": [("x", "x"), ("y", "y")],
                    "formulas": [
                        "Radius: r = √(x²+y²)",
                        "Winkel: φ = atan2(y,x)",
                    ],
                    "calc": self.calc_cartesian_polar,
                },
                "Abstand zweier Punkte 2D": {
                    "params": [("x1", "x1"), ("y1", "y1"), ("x2", "x2"), ("y2", "y2")],
                    "formulas": [
                        "Abstand: d = √((x2-x1)² + (y2-y1)²)",
                        "Mittelpunkt: M = ((x1+x2)/2, (y1+y2)/2)",
                    ],
                    "calc": self.calc_distance_2d,
                },
                "Steigung / Gerade": {
                    "params": [("x1", "x1"), ("y1", "y1"), ("x2", "x2"), ("y2", "y2")],
                    "formulas": [
                        "Steigung: m = (y2-y1)/(x2-x1)",
                        "Achsenabschnitt: b = y1 - m·x1",
                    ],
                    "calc": self.calc_line_2d,
                },
            },
        }

        self.build_ui()
        self.load_categories()

    def build_ui(self):
        title = ttk.Label(
            self.root,
            text="Erweiterte Geometrie-Formelsammlung + Wissenschaftlicher Rechner",
            font=("Segoe UI", 18, "bold"),
        )
        title.pack(pady=(10, 8))

        top = ttk.Frame(self.root)
        top.pack(fill="x", padx=10)

        ttk.Label(top, text="Kategorie:").grid(row=0, column=0, sticky="w", padx=(0, 6))
        self.category_var = tk.StringVar()
        self.category_combo = ttk.Combobox(top, textvariable=self.category_var, state="readonly", width=28)
        self.category_combo.grid(row=0, column=1, sticky="w")
        self.category_combo.bind("<<ComboboxSelected>>", lambda e: self.load_shapes())

        ttk.Label(top, text="Form / Thema:").grid(row=0, column=2, sticky="w", padx=(18, 6))
        self.shape_var = tk.StringVar()
        self.shape_combo = ttk.Combobox(top, textvariable=self.shape_var, state="readonly", width=34)
        self.shape_combo.grid(row=0, column=3, sticky="w")
        self.shape_combo.bind("<<ComboboxSelected>>", lambda e: self.load_shape())

        self.main_pane = ttk.PanedWindow(self.root, orient="horizontal")
        self.main_pane.pack(fill="both", expand=True, padx=10, pady=10)

        self.left = ttk.Frame(self.main_pane, padding=10)
        self.center = ttk.Frame(self.main_pane, padding=10)
        self.right = ttk.Frame(self.main_pane, padding=10)

        self.main_pane.add(self.left, weight=1)
        self.main_pane.add(self.center, weight=2)
        self.main_pane.add(self.right, weight=2)

        self.build_left_panel()
        self.build_center_panel()
        self.build_right_panel()

    def build_left_panel(self):
        ttk.Label(self.left, text="Eingaben", font=("Segoe UI", 13, "bold")).pack(anchor="w")
        self.input_container = ttk.Frame(self.left)
        self.input_container.pack(fill="x", pady=(10, 8))

        button_row = ttk.Frame(self.left)
        button_row.pack(fill="x", pady=(5, 8))
        ttk.Button(button_row, text="Berechnen", command=self.calculate_geometry).pack(side="left", padx=(0, 6))
        ttk.Button(button_row, text="Zurücksetzen", command=self.reset_inputs).pack(side="left", padx=(0, 6))
        ttk.Button(button_row, text="Beispielwerte", command=self.fill_examples).pack(side="left")

        hint = (
            "Hinweise:\n"
            "- Dezimalzahlen mit Punkt oder Komma\n"
            "- Alle Eingaben in derselben Einheit\n"
            "- Ergebnisse können rechts direkt in den wissenschaftlichen\n"
            "  Rechner übernommen werden"
        )
        ttk.Label(self.left, text=hint, justify="left").pack(anchor="w", pady=(8, 10))

        ttk.Separator(self.left, orient="horizontal").pack(fill="x", pady=8)

        ttk.Label(self.left, text="Schnellkonstanten", font=("Segoe UI", 12, "bold")).pack(anchor="w")
        const_frame = ttk.Frame(self.left)
        const_frame.pack(fill="x", pady=(8, 0))
        ttk.Button(const_frame, text="π", command=lambda: self.insert_into_calc("pi")).pack(side="left", padx=3)
        ttk.Button(const_frame, text="e", command=lambda: self.insert_into_calc("e")).pack(side="left", padx=3)
        ttk.Button(const_frame, text="τ", command=lambda: self.insert_into_calc("tau")).pack(side="left", padx=3)
        ttk.Button(const_frame, text="Ans", command=lambda: self.insert_into_calc("ans")).pack(side="left", padx=3)

    def build_center_panel(self):
        self.tabs = ttk.Notebook(self.center)
        self.tabs.pack(fill="both", expand=True)

        self.tab_formulas = ttk.Frame(self.tabs, padding=10)
        self.tab_results = ttk.Frame(self.tabs, padding=10)
        self.tab_overview = ttk.Frame(self.tabs, padding=10)

        self.tabs.add(self.tab_formulas, text="Formeln")
        self.tabs.add(self.tab_results, text="Geometrie-Ergebnisse")
        self.tabs.add(self.tab_overview, text="Formelübersicht")

        ttk.Label(self.tab_formulas, text="Formeln zum gewählten Thema", font=("Segoe UI", 13, "bold")).pack(anchor="w")
        self.formula_text = tk.Text(self.tab_formulas, wrap="word", font=("Consolas", 11))
        self.formula_text.pack(fill="both", expand=True, pady=(10, 0))
        self.formula_text.configure(state="disabled")

        ttk.Label(self.tab_results, text="Berechnungsergebnisse", font=("Segoe UI", 13, "bold")).pack(anchor="w")

        result_split = ttk.PanedWindow(self.tab_results, orient="vertical")
        result_split.pack(fill="both", expand=True, pady=(10, 0))

        self.result_text = tk.Text(result_split, wrap="word", font=("Consolas", 11), height=14)
        self.result_text.configure(state="disabled")
        result_split.add(self.result_text, weight=2)

        draw_frame = ttk.Frame(result_split, padding=(0, 8, 0, 0))
        ttk.Label(draw_frame, text="Skizze der Geometrie", font=("Segoe UI", 11, "bold")).pack(anchor="w")
        self.draw_canvas = tk.Canvas(draw_frame, bg="white", height=260, highlightthickness=1, highlightbackground="#aaaaaa")
        self.draw_canvas.pack(fill="both", expand=True, pady=(6, 0))
        result_split.add(draw_frame, weight=1)

        ttk.Label(self.tab_overview, text="Große Übersicht wichtiger Formeln", font=("Segoe UI", 13, "bold")).pack(anchor="w")
        self.overview_text = tk.Text(self.tab_overview, wrap="word", font=("Consolas", 10))
        self.overview_text.pack(fill="both", expand=True, pady=(10, 0))
        self.overview_text.insert("1.0", self.build_overview())
        self.overview_text.configure(state="disabled")

    def build_right_panel(self):
        ttk.Label(self.right, text="Wissenschaftlicher Rechner", font=("Segoe UI", 13, "bold")).pack(anchor="w")

        entry_frame = ttk.Frame(self.right)
        entry_frame.pack(fill="x", pady=(10, 6))

        self.calc_var = tk.StringVar()
        self.calc_entry = ttk.Entry(entry_frame, textvariable=self.calc_var, font=("Consolas", 12))
        self.calc_entry.pack(fill="x", side="left", expand=True)
        self.calc_entry.bind("<Return>", lambda e: self.evaluate_expression())

        ttk.Button(entry_frame, text="=", command=self.evaluate_expression).pack(side="left", padx=(8, 0))

        ops_frame = ttk.Frame(self.right)
        ops_frame.pack(fill="x", pady=(0, 8))
        for token in ["+", "-", "*", "/", "**", "(", ")", ","]:
            ttk.Button(ops_frame, text=token, width=4, command=lambda t=token: self.insert_into_calc(t)).pack(side="left", padx=2, pady=2)

        funcs_title = ttk.Label(self.right, text="Funktionen / Einfügen", font=("Segoe UI", 12, "bold"))
        funcs_title.pack(anchor="w", pady=(4, 4))

        buttons = [
            ("sin(", "sin("), ("cos(", "cos("), ("tan(", "tan("), ("asin(", "asin("), ("acos(", "acos("), ("atan(", "atan("),
            ("sqrt(", "sqrt("), ("log10(", "log10("), ("ln(", "ln("), ("exp(", "exp("), ("abs(", "abs("), ("pow(", "pow("),
            ("deg(", "deg("), ("rad(", "rad("), ("fact(", "fact("), ("ceil(", "ceil("), ("floor(", "floor("), ("mod", "%"),
        ]
        grid = ttk.Frame(self.right)
        grid.pack(fill="x", pady=(0, 8))
        for i, (label, token) in enumerate(buttons):
            r, c = divmod(i, 3)
            ttk.Button(grid, text=label, width=10, command=lambda t=token: self.insert_into_calc(t)).grid(row=r, column=c, padx=3, pady=3, sticky="ew")
        for c in range(3):
            grid.columnconfigure(c, weight=1)

        hist_title = ttk.Label(self.right, text="Ergebnisliste zum Einfügen", font=("Segoe UI", 12, "bold"))
        hist_title.pack(anchor="w", pady=(6, 4))

        list_frame = ttk.Frame(self.right)
        list_frame.pack(fill="both", expand=True)

        self.result_listbox = tk.Listbox(list_frame, font=("Consolas", 10), height=16)
        self.result_listbox.pack(side="left", fill="both", expand=True)
        self.result_listbox.bind("<Double-Button-1>", lambda e: self.insert_selected_result())

        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.result_listbox.yview)
        scrollbar.pack(side="right", fill="y")
        self.result_listbox.config(yscrollcommand=scrollbar.set)

        action_row = ttk.Frame(self.right)
        action_row.pack(fill="x", pady=8)
        ttk.Button(action_row, text="Ausgewähltes Ergebnis einfügen", command=self.insert_selected_result).pack(fill="x", pady=2)
        ttk.Button(action_row, text="Ans in Ausdruck einfügen", command=lambda: self.insert_into_calc("ans")).pack(fill="x", pady=2)
        ttk.Button(action_row, text="Rechner löschen", command=lambda: self.calc_var.set("")).pack(fill="x", pady=2)
        ttk.Button(action_row, text="Ergebnisliste löschen", command=self.clear_result_list).pack(fill="x", pady=2)

        ttk.Label(self.right, text="Rechner-Ausgabe", font=("Segoe UI", 12, "bold")).pack(anchor="w", pady=(6, 4))
        self.calc_output = tk.Text(self.right, wrap="word", height=10, font=("Consolas", 10))
        self.calc_output.pack(fill="both", expand=False)
        self.calc_output.configure(state="disabled")
        self.set_text(self.calc_output, "Hier erscheinen Rechenausdrücke und Ergebnisse.\n")

        help_text = (
            "Beispiele:\n"
            "  sin(rad(30))\n"
            "  sqrt(25)+3\n"
            "  pi*12**2\n"
            "  ans/2\n"
            "  pow(3,4)+log10(1000)\n"
        )
        ttk.Label(self.right, text=help_text, justify="left").pack(anchor="w", pady=(6, 0))

    def load_categories(self):
        categories = list(self.shapes.keys())
        self.category_combo["values"] = categories
        if categories:
            self.category_var.set(categories[0])
            self.load_shapes()

    def load_shapes(self):
        category = self.category_var.get()
        names = list(self.shapes[category].keys())
        self.shape_combo["values"] = names
        if names:
            self.shape_var.set(names[0])
            self.load_shape()

    def load_shape(self):
        for child in self.input_container.winfo_children():
            child.destroy()
        self.input_vars = {}

        data = self.shapes[self.category_var.get()][self.shape_var.get()]
        for i, (key, label) in enumerate(data["params"]):
            ttk.Label(self.input_container, text=label + ":").grid(row=i, column=0, sticky="w", padx=(0, 8), pady=4)
            var = tk.StringVar()
            ent = ttk.Entry(self.input_container, textvariable=var, width=20)
            ent.grid(row=i, column=1, sticky="w", pady=4)
            self.input_vars[key] = var

        formula_text = "\n".join(data["formulas"])
        self.set_text(self.formula_text, formula_text)
        self.set_text(self.result_text, "Noch keine Berechnung durchgeführt.")

    def parse_num(self, value, label, integer=False):
        value = value.strip().replace(",", ".")
        if not value:
            raise ValueError(f"Bitte Wert für '{label}' eingeben.")
        num = float(value)
        if integer:
            num = int(num)
        if num <= 0 and label not in {"x", "y", "x1", "y1", "x2", "y2"}:
            raise ValueError(f"'{label}' muss größer als 0 sein.")
        return num

    def get_values(self):
        vals = {}
        shape = self.shape_var.get()
        params = self.shapes[self.category_var.get()][shape]["params"]

        if shape == "Dreieck allgemein":
            for key, label in params:
                raw = self.input_vars[key].get().strip()
                if raw:
                    vals[key] = self.parse_num(raw, label)
            return vals

        for key, label in params:
            vals[key] = self.parse_num(self.input_vars[key].get(), label, integer=(key == "n"))
        return vals

    def calculate_geometry(self):
        try:
            vals = self.get_values()
            calc_fn = self.shapes[self.category_var.get()][self.shape_var.get()]["calc"]
            results = calc_fn(vals)

            self.last_results = results.copy()
            self.result_order = list(results.keys())
            self.refresh_result_list()

            lines = [f"Thema: {self.shape_var.get()}", "", "Eingaben:"]
            for k, v in vals.items():
                lines.append(f"  {k} = {self.fmt(v)}")
            lines.append("")
            lines.append("Ergebnisse:")
            for k, v in results.items():
                lines.append(f"  {k} = {self.fmt(v)}")
            self.set_text(self.result_text, "\n".join(lines))
            self.draw_geometry(vals, results)
            self.tabs.select(self.tab_results)

            if results:
                first_key = next(iter(results))
                self.append_calc_output(f"Geometrie berechnet: {self.shape_var.get()} | {first_key} = {self.fmt(results[first_key])}")

        except Exception as e:
            messagebox.showerror("Fehler", str(e))

    def refresh_result_list(self):
        self.result_listbox.delete(0, tk.END)
        for key in self.result_order:
            self.result_listbox.insert(tk.END, f"{key} = {self.fmt(self.last_results[key])}")

    def clear_result_list(self):
        self.last_results = {}
        self.result_order = []
        self.result_listbox.delete(0, tk.END)

    def insert_selected_result(self):
        idx = self.result_listbox.curselection()
        if not idx:
            messagebox.showinfo("Hinweis", "Bitte zuerst ein Ergebnis in der Liste auswählen.")
            return
        key = self.result_order[idx[0]]
        value = self.last_results[key]
        self.insert_into_calc(self.fmt(value))

    def insert_into_calc(self, text):
        self.calc_entry.insert(tk.INSERT, text)
        self.calc_entry.focus_set()

    def evaluate_expression(self):
        expr = self.calc_var.get().strip()
        if not expr:
            return

        try:
            safe_env = {
                "__builtins__": {},
                "pi": math.pi,
                "e": math.e,
                "tau": math.tau,
                "sin": math.sin,
                "cos": math.cos,
                "tan": math.tan,
                "asin": math.asin,
                "acos": math.acos,
                "atan": math.atan,
                "sqrt": math.sqrt,
                "log10": math.log10,
                "ln": math.log,
                "log": math.log,
                "exp": math.exp,
                "abs": abs,
                "pow": pow,
                "ceil": math.ceil,
                "floor": math.floor,
                "fact": math.factorial,
                "deg": math.degrees,
                "rad": math.radians,
                "ans": self.get_last_numeric_result(),
            }
            result = eval(expr, safe_env, {})
            self.append_calc_output(f"{expr} = {self.fmt(result)}")
            self.calc_var.set(str(result))
            self.store_calc_result(result)
        except Exception as e:
            messagebox.showerror("Rechnerfehler", f"Ausdruck konnte nicht berechnet werden:\n{e}")

    def get_last_numeric_result(self):
        if self.result_order:
            return self.last_results[self.result_order[-1]]
        return 0.0

    def store_calc_result(self, value):
        self.last_results["Ans"] = float(value)
        if "Ans" not in self.result_order:
            self.result_order.append("Ans")
        self.refresh_result_list()

    def append_calc_output(self, text):
        self.calc_output.configure(state="normal")
        self.calc_output.insert("end", text + "\n")
        self.calc_output.see("end")
        self.calc_output.configure(state="disabled")

    def reset_inputs(self):
        for var in self.input_vars.values():
            var.set("")
        self.set_text(self.result_text, "Eingaben wurden zurückgesetzt.")

    def fill_examples(self):
        examples = {
            "Rechteck": {"a": "12", "b": "7"},
            "Quadrat": {"a": "8"},
            "Kreis": {"r": "15"},
            "Ring / Kreisring": {"R": "12", "r": "8"},
            "Ellipse": {"a": "10", "b": "6"},
            "Sektor": {"r": "9", "alpha_deg": "60"},
            "Kreissegment": {"r": "9", "alpha_deg": "60"},
            "Dreieck allgemein": {"a": "5", "b": "6", "c": "7", "alpha_deg": "", "beta_deg": "", "gamma_deg": "", "h_a": ""},
            "Rechtwinkliges Dreieck": {"a": "3", "b": "4"},
            "Gleichseitiges Dreieck": {"a": "6"},
            "Trapez": {"a": "10", "c": "6", "h": "4", "b": "5", "d": "5"},
            "Parallelogramm": {"a": "8", "b": "5", "h": "4", "alpha_deg": "30"},
            "Raute": {"a": "5", "e": "8", "f": "6"},
            "Deltoid": {"a": "4", "b": "7", "e": "10", "f": "5"},
            "Regelmäßiges n-Eck": {"n": "6", "a": "4"},
            "Würfel": {"a": "5"},
            "Quader": {"a": "8", "b": "5", "c": "3"},
            "Kugel": {"r": "6"},
            "Halbkugel": {"r": "6"},
            "Zylinder": {"r": "4", "h": "10"},
            "Rohr / Hohlzylinder": {"R": "8", "r": "6", "h": "20"},
            "Kegel": {"r": "4", "h": "9"},
            "Kegelstumpf": {"R": "8", "r": "4", "h": "10"},
            "Prisma": {"G": "18", "U_G": "20", "h": "7"},
            "Pyramide": {"G": "25", "h": "9", "M": "40"},
            "Tetraeder regelmäßig": {"a": "6"},
            "Kreis / Winkel": {"r": "10", "alpha_deg": "45"},
            "Kartesisch / Polar": {"x": "3", "y": "4"},
            "Abstand zweier Punkte 2D": {"x1": "1", "y1": "2", "x2": "6", "y2": "8"},
            "Steigung / Gerade": {"x1": "1", "y1": "2", "x2": "6", "y2": "8"},
        }
        current = self.shape_var.get()
        if current in examples:
            for k, v in examples[current].items():
                if k in self.input_vars:
                    self.input_vars[k].set(v)

    def set_text(self, widget, text):
        widget.configure(state="normal")
        widget.delete("1.0", "end")
        widget.insert("1.0", text)
        widget.configure(state="disabled")

    def draw_geometry(self, vals, results):
        c = self.draw_canvas
        c.update_idletasks()
        width = max(c.winfo_width(), 300)
        height = max(c.winfo_height(), 220)
        c.delete("all")

        margin = 20
        x0, y0 = margin, margin
        x1, y1 = width - margin, height - margin
        c.create_rectangle(x0, y0, x1, y1, outline="#e6e6e6")

        shape = self.shape_var.get()

        if "Dreieck" in shape:
            a = results.get("Seite a", vals.get("a", 5.0))
            b = results.get("Seite b", vals.get("b", 6.0))
            c_len = results.get("Seite c", vals.get("c", 7.0))
            if min(a, b, c_len) <= 0:
                raise ValueError("Ungültige Seitenlängen für Zeichnung.")

            px0 = x0 + 40
            py0 = y1 - 35
            scale = min((x1 - x0 - 90) / c_len, (y1 - y0 - 70) / max(b, a, c_len))
            B = (px0 + c_len * scale, py0)
            xC = px0 + (b * b + c_len * c_len - a * a) / (2 * c_len) * scale
            yC = py0 - math.sqrt(max((b * scale) ** 2 - (xC - px0) ** 2, 0.0))
            A = (px0, py0)
            C = (xC, yC)
            c.create_polygon(A[0], A[1], B[0], B[1], C[0], C[1], outline="#1f77b4", fill="#dcecff", width=2)
            c.create_text(A[0] - 12, A[1] + 12, text="A")
            c.create_text(B[0] + 12, B[1] + 12, text="B")
            c.create_text(C[0], C[1] - 12, text="C")
        elif shape in {"Kreis", "Ring / Kreisring", "Sektor", "Kreissegment", "Kreis / Winkel"}:
            r_outer = vals.get("R", vals.get("r", 5.0))
            r_inner = vals.get("r", 0.0) if shape == "Ring / Kreisring" else 0.0
            scale = min((x1 - x0 - 40) / (2 * r_outer), (y1 - y0 - 40) / (2 * r_outer))
            cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
            Rpx = r_outer * scale
            c.create_oval(cx - Rpx, cy - Rpx, cx + Rpx, cy + Rpx, outline="#1f77b4", width=2)
            if r_inner > 0:
                rpx = r_inner * scale
                c.create_oval(cx - rpx, cy - rpx, cx + rpx, cy + rpx, outline="#ff7f0e", width=2)
        elif shape in {"Rechteck", "Quadrat", "Trapez", "Parallelogramm", "Raute", "Deltoid"}:
            c.create_polygon(x0 + 50, y1 - 40, x1 - 60, y1 - 40, x1 - 90, y0 + 50, x0 + 80, y0 + 50, outline="#1f77b4", fill="#dcecff", width=2)
        else:
            c.create_oval(x0 + 70, y0 + 40, x1 - 70, y1 - 40, outline="#1f77b4", width=2)
            c.create_text((x0 + x1) / 2, y1 - 18, text=f"Schema: {shape}", fill="#555")

        c.create_text(x0 + 8, y0 + 8, anchor="nw", text=f"{shape}", fill="#333", font=("Segoe UI", 10, "bold"))

    def fmt(self, value):
        if isinstance(value, int):
            return str(value)
        if isinstance(value, float):
            return f"{value:.10f}".rstrip("0").rstrip(".")
        return str(value)

    def build_overview(self):
        return (
            "2D-GRUNDFORMEN\n"
            "Rechteck: A=a·b | U=2(a+b) | d=√(a²+b²)\n"
            "Quadrat: A=a² | U=4a | d=a√2\n"
            "Kreis: A=πr² | U=2πr | d=2r\n"
            "Kreisring: A=π(R²-r²)\n"
            "Ellipse: A=πab\n"
            "Sektor: A=πr²·α/360 | s=2πr·α/360\n"
            "Segment: A=(r²/2)(α-sin α), α in rad\n\n"
            "DREIECKE / VIERECKE\n"
            "Allg. Dreieck: U=a+b+c | A=(a·h_a)/2 | Heron\n"
            "Rechtw. Dreieck: c=√(a²+b²) | A=ab/2\n"
            "Gleichseitig: A=a²√3/4 | h=a√3/2\n"
            "Trapez: A=((a+c)/2)·h | m=(a+c)/2\n"
            "Parallelogramm: A=a·h=a·b·sin α\n"
            "Raute / Deltoid: A=e·f/2\n\n"
            "REGELMÄSSIGE FIGUREN\n"
            "n-Eck: U=n·a | A=n·a²/(4 tan(π/n))\n"
            "Apothem: r=a/(2 tan(π/n)) | Umkreisradius: R=a/(2 sin(π/n))\n\n"
            "3D-GRUNDKÖRPER\n"
            "Würfel: V=a³ | O=6a²\n"
            "Quader: V=abc | O=2(ab+ac+bc)\n"
            "Kugel: V=4/3πr³ | O=4πr²\n"
            "Halbkugel: V=2/3πr³ | O=3πr²\n"
            "Zylinder: V=πr²h | M=2πrh | O=2πr²+2πrh\n"
            "Hohlzylinder: V=π(R²-r²)h\n"
            "Kegel: V=1/3πr²h | s=√(r²+h²) | M=πrs\n"
            "Kegelstumpf: V=πh(R²+Rr+r²)/3\n\n"
            "PRISMEN / PYRAMIDEN\n"
            "Prisma: V=G·h | M=U_G·h | O=2G+U_G·h\n"
            "Pyramide: V=G·h/3 | O=G+M\n"
            "Tetraeder: V=a³/(6√2) | O=√3·a²\n\n"
            "TRIGONOMETRIE / ANALYTIK\n"
            "Bogenmaß: α_rad = α_deg·π/180\n"
            "Punktabstand: d=√((x2-x1)²+(y2-y1)²)\n"
            "Gerade: m=(y2-y1)/(x2-x1) | b=y1-mx1\n"
            "Polar: r=√(x²+y²) | φ=atan2(y,x)\n"
        )

    # ---------- 2D ----------


class AdvancedGeometryApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Erweiterte Geometrie- und Wissenschaftsrechner-GUI")
        self.root.geometry("1450x900")
        self.root.minsize(1200, 780)

        self.last_results = {}
        self.result_order = []

        self.shapes = {
            "2D Grundformen": {
                "Rechteck": {
                    "params": [("a", "Länge a"), ("b", "Breite b")],
                    "formulas": [
                        "Fläche: A = a · b",
                        "Umfang: U = 2(a + b)",
                        "Diagonale: d = √(a² + b²)",
                    ],
                    "calc": self.calc_rectangle,
                },
                "Quadrat": {
                    "params": [("a", "Seitenlänge a")],
                    "formulas": [
                        "Fläche: A = a²",
                        "Umfang: U = 4a",
                        "Diagonale: d = a√2",
                        "Inkreisradius: r_i = a/2",
                        "Umkreisradius: r_u = a/√2",
                    ],
                    "calc": self.calc_square,
                },
                "Kreis": {
                    "params": [("r", "Radius r")],
                    "formulas": [
                        "Fläche: A = πr²",
                        "Umfang: U = 2πr",
                        "Durchmesser: d = 2r",
                    ],
                    "calc": self.calc_circle,
                },
                "Ring / Kreisring": {
                    "params": [("R", "Außenradius R"), ("r", "Innenradius r")],
                    "formulas": [
                        "Fläche: A = π(R² - r²)",
                        "Außenumfang: U_a = 2πR",
                        "Innenumfang: U_i = 2πr",
                    ],
                    "calc": self.calc_annulus,
                },
                "Ellipse": {
                    "params": [("a", "Halbachse a"), ("b", "Halbachse b")],
                    "formulas": [
                        "Fläche: A = πab",
                        "Umfang (Ramanujan): U ≈ π[3(a+b) - √((3a+b)(a+3b))]",
                    ],
                    "calc": self.calc_ellipse,
                },
                "Sektor": {
                    "params": [("r", "Radius r"), ("alpha_deg", "Winkel α in Grad")],
                    "formulas": [
                        "Bogenlänge: s = 2πr · α/360",
                        "Fläche: A = πr² · α/360",
                        "Sehnenlänge: c = 2r·sin(α/2)",
                    ],
                    "calc": self.calc_sector,
                },
                "Kreissegment": {
                    "params": [("r", "Radius r"), ("alpha_deg", "Winkel α in Grad")],
                    "formulas": [
                        "Segmentfläche: A = (r²/2)(α - sin α), α in rad",
                        "Sehne: c = 2r·sin(α/2)",
                    ],
                    "calc": self.calc_segment,
                },
            },
            "2D Dreiecke/Vierecke": {
                "Dreieck allgemein": {
                    "params": [("a", "Seite a"), ("b", "Seite b"), ("c", "Seite c"), ("h_a", "Höhe auf a")],
                    "formulas": [
                        "Umfang: U = a + b + c",
                        "Fläche: A = (a · h_a)/2",
                        "Heron: A = √(s(s-a)(s-b)(s-c)), s = U/2",
                    ],
                    "calc": self.calc_triangle_general,
                },
                "Rechtwinkliges Dreieck": {
                    "params": [("a", "Kathete a"), ("b", "Kathete b")],
                    "formulas": [
                        "Hypotenuse: c = √(a² + b²)",
                        "Fläche: A = ab/2",
                        "Umfang: U = a + b + c",
                        "Winkel: α = atan(b/a), β = atan(a/b)",
                    ],
                    "calc": self.calc_triangle_right,
                },
                "Gleichseitiges Dreieck": {
                    "params": [("a", "Seitenlänge a")],
                    "formulas": [
                        "Höhe: h = a√3/2",
                        "Fläche: A = a²√3/4",
                        "Umfang: U = 3a",
                        "Inkreisradius: r_i = a√3/6",
                        "Umkreisradius: r_u = a√3/3",
                    ],
                    "calc": self.calc_triangle_equilateral,
                },
                "Trapez": {
                    "params": [("a", "Grundseite a"), ("c", "Oberseite c"), ("h", "Höhe h"), ("b", "Seite b"), ("d", "Seite d")],
                    "formulas": [
                        "Fläche: A = ((a + c)/2) · h",
                        "Umfang: U = a + b + c + d",
                        "Mittellinie: m = (a + c)/2",
                    ],
                    "calc": self.calc_trapezoid,
                },
                "Parallelogramm": {
                    "params": [("a", "Seite a"), ("b", "Seite b"), ("h", "Höhe h"), ("alpha_deg", "Winkel α in Grad")],
                    "formulas": [
                        "Fläche: A = a · h = a·b·sin(α)",
                        "Umfang: U = 2(a+b)",
                    ],
                    "calc": self.calc_parallelogram,
                },
                "Raute": {
                    "params": [("a", "Seitenlänge a"), ("e", "Diagonale e"), ("f", "Diagonale f")],
                    "formulas": [
                        "Fläche: A = e·f/2",
                        "Umfang: U = 4a",
                    ],
                    "calc": self.calc_rhombus,
                },
                "Deltoid": {
                    "params": [("a", "Seite a"), ("b", "Seite b"), ("e", "Diagonale e"), ("f", "Diagonale f")],
                    "formulas": [
                        "Fläche: A = e·f/2",
                        "Umfang: U = 2(a+b)",
                    ],
                    "calc": self.calc_kite,
                },
            },
            "2D Regelmäßige Figuren": {
                "Regelmäßiges n-Eck": {
                    "params": [("n", "Anzahl Seiten n"), ("a", "Seitenlänge a")],
                    "formulas": [
                        "Innenwinkel: α = (n-2)·180°/n",
                        "Umfang: U = n·a",
                        "Apothem: r = a / (2 tan(π/n))",
                        "Umkreisradius: R = a / (2 sin(π/n))",
                        "Fläche: A = n·a² / (4 tan(π/n))",
                    ],
                    "calc": self.calc_regular_polygon,
                },
            },
            "3D Grundkörper": {
                "Würfel": {
                    "params": [("a", "Kantenlänge a")],
                    "formulas": [
                        "Volumen: V = a³",
                        "Oberfläche: O = 6a²",
                        "Raumdiagonale: d = a√3",
                    ],
                    "calc": self.calc_cube,
                },
                "Quader": {
                    "params": [("a", "Länge a"), ("b", "Breite b"), ("c", "Höhe c")],
                    "formulas": [
                        "Volumen: V = abc",
                        "Oberfläche: O = 2(ab + ac + bc)",
                        "Raumdiagonale: d = √(a²+b²+c²)",
                    ],
                    "calc": self.calc_cuboid,
                },
                "Kugel": {
                    "params": [("r", "Radius r")],
                    "formulas": [
                        "Volumen: V = 4/3 πr³",
                        "Oberfläche: O = 4πr²",
                    ],
                    "calc": self.calc_sphere,
                },
                "Halbkugel": {
                    "params": [("r", "Radius r")],
                    "formulas": [
                        "Volumen: V = 2/3 πr³",
                        "Mantel + Grundfläche: O = 3πr²",
                        "Nur Mantelfläche: M = 2πr²",
                    ],
                    "calc": self.calc_hemisphere,
                },
                "Zylinder": {
                    "params": [("r", "Radius r"), ("h", "Höhe h")],
                    "formulas": [
                        "Volumen: V = πr²h",
                        "Mantelfläche: M = 2πrh",
                        "Oberfläche: O = 2πr² + 2πrh",
                    ],
                    "calc": self.calc_cylinder,
                },
                "Rohr / Hohlzylinder": {
                    "params": [("R", "Außenradius R"), ("r", "Innenradius r"), ("h", "Höhe h")],
                    "formulas": [
                        "Volumen: V = π(R²-r²)h",
                        "Außenmantel: M_a = 2πRh",
                        "Innenmantel: M_i = 2πrh",
                        "Gesamtoberfläche: O = 2π(R²-r²) + 2πh(R+r)",
                    ],
                    "calc": self.calc_hollow_cylinder,
                },
                "Kegel": {
                    "params": [("r", "Radius r"), ("h", "Höhe h")],
                    "formulas": [
                        "Mantellinie: s = √(r²+h²)",
                        "Volumen: V = 1/3 πr²h",
                        "Mantelfläche: M = πrs",
                        "Oberfläche: O = πr² + πrs",
                    ],
                    "calc": self.calc_cone,
                },
                "Kegelstumpf": {
                    "params": [("R", "Großer Radius R"), ("r", "Kleiner Radius r"), ("h", "Höhe h")],
                    "formulas": [
                        "Mantellinie: s = √((R-r)² + h²)",
                        "Volumen: V = πh(R² + Rr + r²)/3",
                        "Mantelfläche: M = π(R+r)s",
                        "Oberfläche: O = M + πR² + πr²",
                    ],
                    "calc": self.calc_frustum,
                },
            },
            "3D Prismen/Pyramiden": {
                "Prisma": {
                    "params": [("G", "Grundfläche G"), ("U_G", "Grundumfang U_G"), ("h", "Höhe h")],
                    "formulas": [
                        "Volumen: V = G·h",
                        "Mantelfläche: M = U_G·h",
                        "Oberfläche: O = 2G + U_G·h",
                    ],
                    "calc": self.calc_prism,
                },
                "Pyramide": {
                    "params": [("G", "Grundfläche G"), ("h", "Höhe h"), ("M", "Mantelfläche M")],
                    "formulas": [
                        "Volumen: V = G·h/3",
                        "Oberfläche: O = G + M",
                    ],
                    "calc": self.calc_pyramid,
                },
                "Tetraeder regelmäßig": {
                    "params": [("a", "Kantenlänge a")],
                    "formulas": [
                        "Volumen: V = a³ / (6√2)",
                        "Oberfläche: O = √3 · a²",
                        "Höhe: h = a√(2/3)",
                    ],
                    "calc": self.calc_tetrahedron,
                },
            },
            "Trigonometrie / Analytik": {
                "Kreis / Winkel": {
                    "params": [("r", "Radius r"), ("alpha_deg", "Winkel α in Grad")],
                    "formulas": [
                        "Bogenmaß: α_rad = α_deg · π/180",
                        "Bogenlänge: s = r·α_rad",
                        "Sehne: c = 2r·sin(α/2)",
                    ],
                    "calc": self.calc_angle_circle,
                },
                "Kartesisch / Polar": {
                    "params": [("x", "x"), ("y", "y")],
                    "formulas": [
                        "Radius: r = √(x²+y²)",
                        "Winkel: φ = atan2(y,x)",
                    ],
                    "calc": self.calc_cartesian_polar,
                },
                "Abstand zweier Punkte 2D": {
                    "params": [("x1", "x1"), ("y1", "y1"), ("x2", "x2"), ("y2", "y2")],
                    "formulas": [
                        "Abstand: d = √((x2-x1)² + (y2-y1)²)",
                        "Mittelpunkt: M = ((x1+x2)/2, (y1+y2)/2)",
                    ],
                    "calc": self.calc_distance_2d,
                },
                "Steigung / Gerade": {
                    "params": [("x1", "x1"), ("y1", "y1"), ("x2", "x2"), ("y2", "y2")],
                    "formulas": [
                        "Steigung: m = (y2-y1)/(x2-x1)",
                        "Achsenabschnitt: b = y1 - m·x1",
                    ],
                    "calc": self.calc_line_2d,
                },
            },
        }

        self.build_ui()
        self.load_categories()

    def build_ui(self):
        title = ttk.Label(
            self.root,
            text="Erweiterte Geometrie-Formelsammlung + Wissenschaftlicher Rechner",
            font=("Segoe UI", 18, "bold"),
        )
        title.pack(pady=(10, 8))

        top = ttk.Frame(self.root)
        top.pack(fill="x", padx=10)

        ttk.Label(top, text="Kategorie:").grid(row=0, column=0, sticky="w", padx=(0, 6))
        self.category_var = tk.StringVar()
        self.category_combo = ttk.Combobox(top, textvariable=self.category_var, state="readonly", width=28)
        self.category_combo.grid(row=0, column=1, sticky="w")
        self.category_combo.bind("<<ComboboxSelected>>", lambda e: self.load_shapes())

        ttk.Label(top, text="Form / Thema:").grid(row=0, column=2, sticky="w", padx=(18, 6))
        self.shape_var = tk.StringVar()
        self.shape_combo = ttk.Combobox(top, textvariable=self.shape_var, state="readonly", width=34)
        self.shape_combo.grid(row=0, column=3, sticky="w")
        self.shape_combo.bind("<<ComboboxSelected>>", lambda e: self.load_shape())

        self.main_pane = ttk.PanedWindow(self.root, orient="horizontal")
        self.main_pane.pack(fill="both", expand=True, padx=10, pady=10)

        self.left = ttk.Frame(self.main_pane, padding=10)
        self.center = ttk.Frame(self.main_pane, padding=10)
        self.right = ttk.Frame(self.main_pane, padding=10)

        self.main_pane.add(self.left, weight=1)
        self.main_pane.add(self.center, weight=2)
        self.main_pane.add(self.right, weight=2)

        self.build_left_panel()
        self.build_center_panel()
        self.build_right_panel()

    def build_left_panel(self):
        ttk.Label(self.left, text="Eingaben", font=("Segoe UI", 13, "bold")).pack(anchor="w")
        self.input_container = ttk.Frame(self.left)
        self.input_container.pack(fill="x", pady=(10, 8))

        button_row = ttk.Frame(self.left)
        button_row.pack(fill="x", pady=(5, 8))
        ttk.Button(button_row, text="Berechnen", command=self.calculate_geometry).pack(side="left", padx=(0, 6))
        ttk.Button(button_row, text="Zurücksetzen", command=self.reset_inputs).pack(side="left", padx=(0, 6))
        ttk.Button(button_row, text="Beispielwerte", command=self.fill_examples).pack(side="left")

        hint = (
            "Hinweise:\n"
            "- Dezimalzahlen mit Punkt oder Komma\n"
            "- Alle Eingaben in derselben Einheit\n"
            "- Ergebnisse können rechts direkt in den wissenschaftlichen\n"
            "  Rechner übernommen werden"
        )
        ttk.Label(self.left, text=hint, justify="left").pack(anchor="w", pady=(8, 10))

        ttk.Separator(self.left, orient="horizontal").pack(fill="x", pady=8)

        ttk.Label(self.left, text="Schnellkonstanten", font=("Segoe UI", 12, "bold")).pack(anchor="w")
        const_frame = ttk.Frame(self.left)
        const_frame.pack(fill="x", pady=(8, 0))
        ttk.Button(const_frame, text="π", command=lambda: self.insert_into_calc("pi")).pack(side="left", padx=3)
        ttk.Button(const_frame, text="e", command=lambda: self.insert_into_calc("e")).pack(side="left", padx=3)
        ttk.Button(const_frame, text="τ", command=lambda: self.insert_into_calc("tau")).pack(side="left", padx=3)
        ttk.Button(const_frame, text="Ans", command=lambda: self.insert_into_calc("ans")).pack(side="left", padx=3)

    def build_center_panel(self):
        self.tabs = ttk.Notebook(self.center)
        self.tabs.pack(fill="both", expand=True)

        self.tab_formulas = ttk.Frame(self.tabs, padding=10)
        self.tab_results = ttk.Frame(self.tabs, padding=10)
        self.tab_overview = ttk.Frame(self.tabs, padding=10)

        self.tabs.add(self.tab_formulas, text="Formeln")
        self.tabs.add(self.tab_results, text="Geometrie-Ergebnisse")
        self.tabs.add(self.tab_overview, text="Formelübersicht")

        ttk.Label(self.tab_formulas, text="Formeln zum gewählten Thema", font=("Segoe UI", 13, "bold")).pack(anchor="w")
        self.formula_text = tk.Text(self.tab_formulas, wrap="word", font=("Consolas", 11))
        self.formula_text.pack(fill="both", expand=True, pady=(10, 0))
        self.formula_text.configure(state="disabled")

        ttk.Label(self.tab_results, text="Berechnungsergebnisse", font=("Segoe UI", 13, "bold")).pack(anchor="w")
        self.result_text = tk.Text(self.tab_results, wrap="word", font=("Consolas", 11))
        self.result_text.pack(fill="both", expand=True, pady=(10, 0))
        self.result_text.configure(state="disabled")

        ttk.Label(self.tab_overview, text="Große Übersicht wichtiger Formeln", font=("Segoe UI", 13, "bold")).pack(anchor="w")
        self.overview_text = tk.Text(self.tab_overview, wrap="word", font=("Consolas", 10))
        self.overview_text.pack(fill="both", expand=True, pady=(10, 0))
        self.overview_text.insert("1.0", self.build_overview())
        self.overview_text.configure(state="disabled")

    def build_right_panel(self):
        ttk.Label(self.right, text="Wissenschaftlicher Rechner", font=("Segoe UI", 13, "bold")).pack(anchor="w")

        entry_frame = ttk.Frame(self.right)
        entry_frame.pack(fill="x", pady=(10, 6))

        self.calc_var = tk.StringVar()
        self.calc_entry = ttk.Entry(entry_frame, textvariable=self.calc_var, font=("Consolas", 12))
        self.calc_entry.pack(fill="x", side="left", expand=True)
        self.calc_entry.bind("<Return>", lambda e: self.evaluate_expression())

        ttk.Button(entry_frame, text="=", command=self.evaluate_expression).pack(side="left", padx=(8, 0))

        ops_frame = ttk.Frame(self.right)
        ops_frame.pack(fill="x", pady=(0, 8))
        for token in ["+", "-", "*", "/", "**", "(", ")", ","]:
            ttk.Button(ops_frame, text=token, width=4, command=lambda t=token: self.insert_into_calc(t)).pack(side="left", padx=2, pady=2)

        funcs_title = ttk.Label(self.right, text="Funktionen / Einfügen", font=("Segoe UI", 12, "bold"))
        funcs_title.pack(anchor="w", pady=(4, 4))

        buttons = [
            ("sin(", "sin("), ("cos(", "cos("), ("tan(", "tan("), ("asin(", "asin("), ("acos(", "acos("), ("atan(", "atan("),
            ("sqrt(", "sqrt("), ("log10(", "log10("), ("ln(", "ln("), ("exp(", "exp("), ("abs(", "abs("), ("pow(", "pow("),
            ("deg(", "deg("), ("rad(", "rad("), ("fact(", "fact("), ("ceil(", "ceil("), ("floor(", "floor("), ("mod", "%"),
        ]
        grid = ttk.Frame(self.right)
        grid.pack(fill="x", pady=(0, 8))
        for i, (label, token) in enumerate(buttons):
            r, c = divmod(i, 3)
            ttk.Button(grid, text=label, width=10, command=lambda t=token: self.insert_into_calc(t)).grid(row=r, column=c, padx=3, pady=3, sticky="ew")
        for c in range(3):
            grid.columnconfigure(c, weight=1)

        hist_title = ttk.Label(self.right, text="Ergebnisliste zum Einfügen", font=("Segoe UI", 12, "bold"))
        hist_title.pack(anchor="w", pady=(6, 4))

        list_frame = ttk.Frame(self.right)
        list_frame.pack(fill="both", expand=True)

        self.result_listbox = tk.Listbox(list_frame, font=("Consolas", 10), height=16)
        self.result_listbox.pack(side="left", fill="both", expand=True)
        self.result_listbox.bind("<Double-Button-1>", lambda e: self.insert_selected_result())

        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.result_listbox.yview)
        scrollbar.pack(side="right", fill="y")
        self.result_listbox.config(yscrollcommand=scrollbar.set)

        action_row = ttk.Frame(self.right)
        action_row.pack(fill="x", pady=8)
        ttk.Button(action_row, text="Ausgewähltes Ergebnis einfügen", command=self.insert_selected_result).pack(fill="x", pady=2)
        ttk.Button(action_row, text="Ans in Ausdruck einfügen", command=lambda: self.insert_into_calc("ans")).pack(fill="x", pady=2)
        ttk.Button(action_row, text="Rechner löschen", command=lambda: self.calc_var.set("")).pack(fill="x", pady=2)
        ttk.Button(action_row, text="Ergebnisliste löschen", command=self.clear_result_list).pack(fill="x", pady=2)

        ttk.Label(self.right, text="Rechner-Ausgabe", font=("Segoe UI", 12, "bold")).pack(anchor="w", pady=(6, 4))
        self.calc_output = tk.Text(self.right, wrap="word", height=10, font=("Consolas", 10))
        self.calc_output.pack(fill="both", expand=False)
        self.calc_output.configure(state="disabled")
        self.set_text(self.calc_output, "Hier erscheinen Rechenausdrücke und Ergebnisse.\n")

        help_text = (
            "Beispiele:\n"
            "  sin(rad(30))\n"
            "  sqrt(25)+3\n"
            "  pi*12**2\n"
            "  ans/2\n"
            "  pow(3,4)+log10(1000)\n"
        )
        ttk.Label(self.right, text=help_text, justify="left").pack(anchor="w", pady=(6, 0))

    def load_categories(self):
        categories = list(self.shapes.keys())
        self.category_combo["values"] = categories
        if categories:
            self.category_var.set(categories[0])
            self.load_shapes()

    def load_shapes(self):
        category = self.category_var.get()
        names = list(self.shapes[category].keys())
        self.shape_combo["values"] = names
        if names:
            self.shape_var.set(names[0])
            self.load_shape()

    def load_shape(self):
        for child in self.input_container.winfo_children():
            child.destroy()
        self.input_vars = {}

        data = self.shapes[self.category_var.get()][self.shape_var.get()]
        for i, (key, label) in enumerate(data["params"]):
            ttk.Label(self.input_container, text=label + ":").grid(row=i, column=0, sticky="w", padx=(0, 8), pady=4)
            var = tk.StringVar()
            ent = ttk.Entry(self.input_container, textvariable=var, width=20)
            ent.grid(row=i, column=1, sticky="w", pady=4)
            self.input_vars[key] = var

        formula_text = "\n".join(data["formulas"])
        self.set_text(self.formula_text, formula_text)
        self.set_text(self.result_text, "Noch keine Berechnung durchgeführt.")

    def parse_num(self, value, label, integer=False):
        value = value.strip().replace(",", ".")
        if not value:
            raise ValueError(f"Bitte Wert für '{label}' eingeben.")
        num = float(value)
        if integer:
            num = int(num)
        if num <= 0 and label not in {"x", "y", "x1", "y1", "x2", "y2"}:
            raise ValueError(f"'{label}' muss größer als 0 sein.")
        return num

    def get_values(self):
        vals = {}
        params = self.shapes[self.category_var.get()][self.shape_var.get()]["params"]
        for key, label in params:
            vals[key] = self.parse_num(self.input_vars[key].get(), label, integer=(key == "n"))
        return vals

    def calculate_geometry(self):
        try:
            vals = self.get_values()
            calc_fn = self.shapes[self.category_var.get()][self.shape_var.get()]["calc"]
            results = calc_fn(vals)

            self.last_results = results.copy()
            self.result_order = list(results.keys())
            self.refresh_result_list()

            lines = [f"Thema: {self.shape_var.get()}", "", "Eingaben:"]
            for k, v in vals.items():
                lines.append(f"  {k} = {self.fmt(v)}")
            lines.append("")
            lines.append("Ergebnisse:")
            for k, v in results.items():
                lines.append(f"  {k} = {self.fmt(v)}")
            self.set_text(self.result_text, "\n".join(lines))
            self.tabs.select(self.tab_results)

            if results:
                first_key = next(iter(results))
                self.append_calc_output(f"Geometrie berechnet: {self.shape_var.get()} | {first_key} = {self.fmt(results[first_key])}")

        except Exception as e:
            messagebox.showerror("Fehler", str(e))

    def refresh_result_list(self):
        self.result_listbox.delete(0, tk.END)
        for key in self.result_order:
            self.result_listbox.insert(tk.END, f"{key} = {self.fmt(self.last_results[key])}")

    def clear_result_list(self):
        self.last_results = {}
        self.result_order = []
        self.result_listbox.delete(0, tk.END)

    def insert_selected_result(self):
        idx = self.result_listbox.curselection()
        if not idx:
            messagebox.showinfo("Hinweis", "Bitte zuerst ein Ergebnis in der Liste auswählen.")
            return
        key = self.result_order[idx[0]]
        value = self.last_results[key]
        self.insert_into_calc(self.fmt(value))

    def insert_into_calc(self, text):
        self.calc_entry.insert(tk.INSERT, text)
        self.calc_entry.focus_set()

    def evaluate_expression(self):
        expr = self.calc_var.get().strip()
        if not expr:
            return

        try:
            safe_env = {
                "__builtins__": {},
                "pi": math.pi,
                "e": math.e,
                "tau": math.tau,
                "sin": math.sin,
                "cos": math.cos,
                "tan": math.tan,
                "asin": math.asin,
                "acos": math.acos,
                "atan": math.atan,
                "sqrt": math.sqrt,
                "log10": math.log10,
                "ln": math.log,
                "log": math.log,
                "exp": math.exp,
                "abs": abs,
                "pow": pow,
                "ceil": math.ceil,
                "floor": math.floor,
                "fact": math.factorial,
                "deg": math.degrees,
                "rad": math.radians,
                "ans": self.get_last_numeric_result(),
            }
            result = eval(expr, safe_env, {})
            self.append_calc_output(f"{expr} = {self.fmt(result)}")
            self.calc_var.set(str(result))
            self.store_calc_result(result)
        except Exception as e:
            messagebox.showerror("Rechnerfehler", f"Ausdruck konnte nicht berechnet werden:\n{e}")

    def get_last_numeric_result(self):
        if self.result_order:
            return self.last_results[self.result_order[-1]]
        return 0.0

    def store_calc_result(self, value):
        self.last_results["Ans"] = float(value)
        if "Ans" not in self.result_order:
            self.result_order.append("Ans")
        self.refresh_result_list()

    def append_calc_output(self, text):
        self.calc_output.configure(state="normal")
        self.calc_output.insert("end", text + "\n")
        self.calc_output.see("end")
        self.calc_output.configure(state="disabled")

    def reset_inputs(self):
        for var in self.input_vars.values():
            var.set("")
        self.set_text(self.result_text, "Eingaben wurden zurückgesetzt.")

    def fill_examples(self):
        examples = {
            "Rechteck": {"a": "12", "b": "7"},
            "Quadrat": {"a": "8"},
            "Kreis": {"r": "15"},
            "Ring / Kreisring": {"R": "12", "r": "8"},
            "Ellipse": {"a": "10", "b": "6"},
            "Sektor": {"r": "9", "alpha_deg": "60"},
            "Kreissegment": {"r": "9", "alpha_deg": "60"},
            "Dreieck allgemein": {"a": "5", "b": "6", "c": "7", "h_a": "4.8"},
            "Rechtwinkliges Dreieck": {"a": "3", "b": "4"},
            "Gleichseitiges Dreieck": {"a": "6"},
            "Trapez": {"a": "10", "c": "6", "h": "4", "b": "5", "d": "5"},
            "Parallelogramm": {"a": "8", "b": "5", "h": "4", "alpha_deg": "30"},
            "Raute": {"a": "5", "e": "8", "f": "6"},
            "Deltoid": {"a": "4", "b": "7", "e": "10", "f": "5"},
            "Regelmäßiges n-Eck": {"n": "6", "a": "4"},
            "Würfel": {"a": "5"},
            "Quader": {"a": "8", "b": "5", "c": "3"},
            "Kugel": {"r": "6"},
            "Halbkugel": {"r": "6"},
            "Zylinder": {"r": "4", "h": "10"},
            "Rohr / Hohlzylinder": {"R": "8", "r": "6", "h": "20"},
            "Kegel": {"r": "4", "h": "9"},
            "Kegelstumpf": {"R": "8", "r": "4", "h": "10"},
            "Prisma": {"G": "18", "U_G": "20", "h": "7"},
            "Pyramide": {"G": "25", "h": "9", "M": "40"},
            "Tetraeder regelmäßig": {"a": "6"},
            "Kreis / Winkel": {"r": "10", "alpha_deg": "45"},
            "Kartesisch / Polar": {"x": "3", "y": "4"},
            "Abstand zweier Punkte 2D": {"x1": "1", "y1": "2", "x2": "6", "y2": "8"},
            "Steigung / Gerade": {"x1": "1", "y1": "2", "x2": "6", "y2": "8"},
        }
        current = self.shape_var.get()
        if current in examples:
            for k, v in examples[current].items():
                if k in self.input_vars:
                    self.input_vars[k].set(v)

    def set_text(self, widget, text):
        widget.configure(state="normal")
        widget.delete("1.0", "end")
        widget.insert("1.0", text)
        widget.configure(state="disabled")

    def fmt(self, value):
        if isinstance(value, int):
            return str(value)
        if isinstance(value, float):
            return f"{value:.10f}".rstrip("0").rstrip(".")
        return str(value)

    def build_overview(self):
        return (
            "2D-GRUNDFORMEN\n"
            "Rechteck: A=a·b | U=2(a+b) | d=√(a²+b²)\n"
            "Quadrat: A=a² | U=4a | d=a√2\n"
            "Kreis: A=πr² | U=2πr | d=2r\n"
            "Kreisring: A=π(R²-r²)\n"
            "Ellipse: A=πab\n"
            "Sektor: A=πr²·α/360 | s=2πr·α/360\n"
            "Segment: A=(r²/2)(α-sin α), α in rad\n\n"
            "DREIECKE / VIERECKE\n"
            "Allg. Dreieck: U=a+b+c | A=(a·h_a)/2 | Heron\n"
            "Rechtw. Dreieck: c=√(a²+b²) | A=ab/2\n"
            "Gleichseitig: A=a²√3/4 | h=a√3/2\n"
            "Trapez: A=((a+c)/2)·h | m=(a+c)/2\n"
            "Parallelogramm: A=a·h=a·b·sin α\n"
            "Raute / Deltoid: A=e·f/2\n\n"
            "REGELMÄSSIGE FIGUREN\n"
            "n-Eck: U=n·a | A=n·a²/(4 tan(π/n))\n"
            "Apothem: r=a/(2 tan(π/n)) | Umkreisradius: R=a/(2 sin(π/n))\n\n"
            "3D-GRUNDKÖRPER\n"
            "Würfel: V=a³ | O=6a²\n"
            "Quader: V=abc | O=2(ab+ac+bc)\n"
            "Kugel: V=4/3πr³ | O=4πr²\n"
            "Halbkugel: V=2/3πr³ | O=3πr²\n"
            "Zylinder: V=πr²h | M=2πrh | O=2πr²+2πrh\n"
            "Hohlzylinder: V=π(R²-r²)h\n"
            "Kegel: V=1/3πr²h | s=√(r²+h²) | M=πrs\n"
            "Kegelstumpf: V=πh(R²+Rr+r²)/3\n\n"
            "PRISMEN / PYRAMIDEN\n"
            "Prisma: V=G·h | M=U_G·h | O=2G+U_G·h\n"
            "Pyramide: V=G·h/3 | O=G+M\n"
            "Tetraeder: V=a³/(6√2) | O=√3·a²\n\n"
            "TRIGONOMETRIE / ANALYTIK\n"
            "Bogenmaß: α_rad = α_deg·π/180\n"
            "Punktabstand: d=√((x2-x1)²+(y2-y1)²)\n"
            "Gerade: m=(y2-y1)/(x2-x1) | b=y1-mx1\n"
            "Polar: r=√(x²+y²) | φ=atan2(y,x)\n"
        )

    # ---------- 2D ----------
    def calc_rectangle(self, v):
        a, b = v["a"], v["b"]
        area = a * b
        perimeter = 2 * (a + b)
        diagonal = math.sqrt(a * a + b * b)
        return {
            "Fläche A": area,
            "Umfang U": perimeter,
            "Diagonale d": diagonal,
            "Seitenverhältnis a:b": a / b,
            "Seitenverhältnis b:a": b / a,
        }


    def calc_square(self, v):
        a = v["a"]
        diagonal = a * math.sqrt(2)
        return {
            "Fläche A": a ** 2,
            "Umfang U": 4 * a,
            "Diagonale d": diagonal,
            "Inkreisradius r_i": a / 2,
            "Umkreisradius r_u": a / math.sqrt(2),
            "Winkel (alle)": 90.0,
        }


    def calc_circle(self, v):
        r = v["r"]
        diameter = 2 * r
        area = math.pi * r ** 2
        return {
            "Fläche A": area,
            "Umfang U": 2 * math.pi * r,
            "Durchmesser d": diameter,
            "Kreisfläche je Umfang² (A/U²)": area / ((2 * math.pi * r) ** 2),
        }


    def calc_annulus(self, v):
        R, r = v["R"], v["r"]
        if r >= R:
            raise ValueError("Innenradius r muss kleiner als Außenradius R sein.")
        area = math.pi * (R ** 2 - r ** 2)
        outer_u = 2 * math.pi * R
        inner_u = 2 * math.pi * r
        return {
            "Fläche A": area,
            "Außenumfang U_a": outer_u,
            "Innenumfang U_i": inner_u,
            "Umfang gesamt U_ges": outer_u + inner_u,
            "Wandstärke t": R - r,
        }


    def calc_ellipse(self, v):
        a, b = v["a"], v["b"]
        u = math.pi * (3 * (a + b) - math.sqrt((3 * a + b) * (a + 3 * b)))
        c = math.sqrt(abs(a * a - b * b))
        e = c / max(a, b)
        return {
            "Fläche A": math.pi * a * b,
            "Umfang U (Ramanujan)": u,
            "Lineare Exzentrizität c": c,
            "Numerische Exzentrizität e": e,
        }


    def calc_sector(self, v):
        r, alpha_deg = v["r"], v["alpha_deg"]
        alpha_rad = math.radians(alpha_deg)
        full_circle_area = math.pi * r * r
        full_circle_u = 2 * math.pi * r
        return {
            "Winkel α_deg": alpha_deg,
            "Winkel α_rad": alpha_rad,
            "Bogenlänge s": r * alpha_rad,
            "Fläche A": 0.5 * r * r * alpha_rad,
            "Sehnenlänge c": 2 * r * math.sin(alpha_rad / 2),
            "Flächenanteil": (0.5 * r * r * alpha_rad) / full_circle_area,
            "Umfangsanteil (Bogen)": (r * alpha_rad) / full_circle_u,
        }


    def calc_segment(self, v):
        r, alpha_deg = v["r"], v["alpha_deg"]
        alpha_rad = math.radians(alpha_deg)
        chord = 2 * r * math.sin(alpha_rad / 2)
        seg_h = r * (1 - math.cos(alpha_rad / 2))
        return {
            "Winkel α_deg": alpha_deg,
            "Winkel α_rad": alpha_rad,
            "Segmentfläche A": 0.5 * r * r * (alpha_rad - math.sin(alpha_rad)),
            "Sehnenlänge c": chord,
            "Segmenthöhe h": seg_h,
            "Sektorfläche A_sektor": 0.5 * r * r * alpha_rad,
        }

    def calc_triangle_general(self, v):
        a = v.get("a")
        b = v.get("b")
        c = v.get("c")
        alpha = v.get("alpha_deg")
        beta = v.get("beta_deg")
        gamma = v.get("gamma_deg")
        h_a_input = v.get("h_a")

        given_sides = sum(x is not None for x in (a, b, c))
        given_angles = sum(x is not None for x in (alpha, beta, gamma))

        if given_sides == 3:
            if a + b <= c or a + c <= b or b + c <= a:
                raise ValueError("Ungültiges Dreieck: Dreiecksungleichung verletzt.")
            alpha = math.degrees(math.acos((b * b + c * c - a * a) / (2 * b * c)))
            beta = math.degrees(math.acos((a * a + c * c - b * b) / (2 * a * c)))
            gamma = 180.0 - alpha - beta
        elif given_sides >= 1 and given_angles >= 2:
            if alpha is None:
                alpha = 180.0 - beta - gamma
            elif beta is None:
                beta = 180.0 - alpha - gamma
            elif gamma is None:
                gamma = 180.0 - alpha - beta

            if min(alpha, beta, gamma) <= 0:
                raise ValueError("Winkel müssen > 0° sein und zusammen 180° ergeben.")

            if a is not None:
                b = a * math.sin(math.radians(beta)) / math.sin(math.radians(alpha))
                c = a * math.sin(math.radians(gamma)) / math.sin(math.radians(alpha))
            elif b is not None:
                a = b * math.sin(math.radians(alpha)) / math.sin(math.radians(beta))
                c = b * math.sin(math.radians(gamma)) / math.sin(math.radians(beta))
            elif c is not None:
                a = c * math.sin(math.radians(alpha)) / math.sin(math.radians(gamma))
                b = c * math.sin(math.radians(beta)) / math.sin(math.radians(gamma))
            else:
                raise ValueError("Für Winkel-Definition mindestens eine Seitenlänge angeben.")
        else:
            raise ValueError(
                "Dreieck allgemein: bitte entweder 3 Seiten angeben ODER 1 Seite + 2 Winkel (α/β/γ)."
            )

        perimeter = a + b + c
        s = perimeter / 2
        area_heron = math.sqrt(max(s * (s - a) * (s - b) * (s - c), 0.0))
        h_a_heron = 2 * area_heron / a
        area_via_ha = a * h_a_input / 2 if h_a_input else area_heron

        return {
            "Seite a": a,
            "Seite b": b,
            "Seite c": c,
            "Winkel α": alpha,
            "Winkel β": beta,
            "Winkel γ": gamma,
            "Umfang U": perimeter,
            "Halbumfang s": s,
            "Fläche A über h_a": area_via_ha,
            "Fläche A nach Heron": area_heron,
            "Höhe h_a (Heron)": h_a_heron,
            "Höhe h_b": 2 * area_heron / b,
            "Höhe h_c": 2 * area_heron / c,
            "Inkreisradius r_i": area_heron / s,
            "Umkreisradius r_u": (a * b * c) / (4 * area_heron),
        }


    def calc_triangle_general(self, v):
        a, b, c, h_a = v["a"], v["b"], v["c"], v["h_a"]
        if a + b <= c or a + c <= b or b + c <= a:
            raise ValueError("Ungültiges Dreieck: Dreiecksungleichung verletzt.")
        perimeter = a + b + c
        s = perimeter / 2
        area_heron = math.sqrt(s * (s - a) * (s - b) * (s - c))
        alpha = math.degrees(math.acos((b * b + c * c - a * a) / (2 * b * c)))
        beta = math.degrees(math.acos((a * a + c * c - b * b) / (2 * a * c)))
        gamma = 180.0 - alpha - beta
        return {
            "Umfang U": perimeter,
            "Halbumfang s": s,
            "Fläche A über h_a": a * h_a / 2,
            "Fläche A nach Heron": area_heron,
            "Höhe h_a (Heron)": 2 * area_heron / a,
            "Höhe h_b": 2 * area_heron / b,
            "Höhe h_c": 2 * area_heron / c,
            "Winkel α": alpha,
            "Winkel β": beta,
            "Winkel γ": gamma,
            "Inkreisradius r_i": area_heron / s,
            "Umkreisradius r_u": (a * b * c) / (4 * area_heron),
        }

    def calc_triangle_right(self, v):
        a, b = v["a"], v["b"]
        c = math.sqrt(a * a + b * b)
        alpha = math.degrees(math.atan2(b, a))
        beta = 90 - alpha
        area = a * b / 2
        return {
            "Hypotenuse c": c,
            "Fläche A": area,
            "Umfang U": a + b + c,
            "Winkel α": alpha,
            "Winkel β": beta,
            "Winkel γ": 90.0,
            "Höhe auf Hypotenuse h_c": (a * b) / c,
            "Inkreisradius r_i": (a + b - c) / 2,
            "Umkreisradius r_u": c / 2,
        }


    def calc_triangle_equilateral(self, v):
        a = v["a"]
        area = a * a * math.sqrt(3) / 4
        return {
            "Höhe h": a * math.sqrt(3) / 2,
            "Fläche A": area,
            "Umfang U": 3 * a,
            "Inkreisradius r_i": a * math.sqrt(3) / 6,
            "Umkreisradius r_u": a * math.sqrt(3) / 3,
            "Winkel α": 60.0,
            "Winkel β": 60.0,
            "Winkel γ": 60.0,
        }


    def calc_trapezoid(self, v):
        a, c, h, b, d = v["a"], v["c"], v["h"], v["b"], v["d"]
        midline = (a + c) / 2
        return {
            "Fläche A": midline * h,
            "Umfang U": a + b + c + d,
            "Mittellinie m": midline,
            "Differenz Grundseiten |a-c|": abs(a - c),
        }


    def calc_parallelogram(self, v):
        a, b, h, alpha_deg = v["a"], v["b"], v["h"], v["alpha_deg"]
        alpha_rad = math.radians(alpha_deg)
        beta_deg = 180 - alpha_deg
        area_by_angle = a * b * math.sin(alpha_rad)
        return {
            "Fläche A über Höhe": a * h,
            "Fläche A über Winkel": area_by_angle,
            "Umfang U": 2 * (a + b),
            "Winkel α_rad": alpha_rad,
            "Winkel α_deg": alpha_deg,
            "Winkel β_deg": beta_deg,
            "Höhe auf b": b * math.sin(alpha_rad),
        }


    def calc_rhombus(self, v):
        a, e, f = v["a"], v["e"], v["f"]
        alpha = 2 * math.degrees(math.atan2(f, e))
        return {
            "Fläche A": e * f / 2,
            "Umfang U": 4 * a,
            "Inkreisradius r_i": (e * f / 2) / (2 * a),
            "Winkel α (aus Diagonalen)": alpha,
            "Winkel β (aus Diagonalen)": 180 - alpha,
        }


    def calc_kite(self, v):
        a, b, e, f = v["a"], v["b"], v["e"], v["f"]
        return {
            "Fläche A": e * f / 2,
            "Umfang U": 2 * (a + b),
            "Halbe Diagonalen e/2": e / 2,
            "Halbe Diagonalen f/2": f / 2,
        }


    def calc_regular_polygon(self, v):
        n, a = int(v["n"]), v["a"]
        if n < 3:
            raise ValueError("Ein regelmäßiges n-Eck benötigt mindestens 3 Seiten.")
        alpha_deg = (n - 2) * 180 / n
        exterior_deg = 360 / n
        apothem = a / (2 * math.tan(math.pi / n))
        circumradius = a / (2 * math.sin(math.pi / n))
        area = n * a * a / (4 * math.tan(math.pi / n))
        return {
            "Innenwinkel α": alpha_deg,
            "Außenwinkel ε": exterior_deg,
            "Umfang U": n * a,
            "Apothem r": apothem,
            "Umkreisradius R": circumradius,
            "Fläche A": area,
            "Diagonalenanzahl": n * (n - 3) / 2,
        }

    # ---------- 3D ----------

    # ---------- 3D ----------
    def calc_cube(self, v):
        a = v["a"]
        return {
            "Volumen V": a ** 3,
            "Oberfläche O": 6 * a ** 2,
            "Raumdiagonale d": a * math.sqrt(3),
            "Flächendiagonale d_f": a * math.sqrt(2),
            "Inkreisradius r_i": a / 2,
            "Umkugelradius r_u": a * math.sqrt(3) / 2,
        }


    def calc_cuboid(self, v):
        a, b, c = v["a"], v["b"], v["c"]
        return {
            "Volumen V": a * b * c,
            "Oberfläche O": 2 * (a * b + a * c + b * c),
            "Raumdiagonale d": math.sqrt(a * a + b * b + c * c),
            "Flächendiagonale ab": math.sqrt(a * a + b * b),
            "Flächendiagonale ac": math.sqrt(a * a + c * c),
            "Flächendiagonale bc": math.sqrt(b * b + c * c),
        }


    def calc_sphere(self, v):
        r = v["r"]
        return {
            "Volumen V": 4 / 3 * math.pi * r ** 3,
            "Oberfläche O": 4 * math.pi * r ** 2,
            "Durchmesser d": 2 * r,
            "Großkreisumfang U": 2 * math.pi * r,
        }


    def calc_hemisphere(self, v):
        r = v["r"]
        return {
            "Volumen V": 2 / 3 * math.pi * r ** 3,
            "Mantelfläche M": 2 * math.pi * r ** 2,
            "Oberfläche O": 3 * math.pi * r ** 2,
            "Grundfläche G": math.pi * r ** 2,
            "Durchmesser d": 2 * r,
        }


    def calc_cylinder(self, v):
        r, h = v["r"], v["h"]
        base_area = math.pi * r ** 2
        return {
            "Volumen V": base_area * h,
            "Mantelfläche M": 2 * math.pi * r * h,
            "Oberfläche O": 2 * base_area + 2 * math.pi * r * h,
            "Grundfläche G": base_area,
            "Durchmesser d": 2 * r,
        }


    def calc_hollow_cylinder(self, v):
        R, r, h = v["R"], v["r"], v["h"]
        if r >= R:
            raise ValueError("Innenradius r muss kleiner als Außenradius R sein.")
        ring_area = math.pi * (R ** 2 - r ** 2)
        return {
            "Volumen V": ring_area * h,
            "Außenmantel M_a": 2 * math.pi * R * h,
            "Innenmantel M_i": 2 * math.pi * r * h,
            "Gesamtoberfläche O": 2 * ring_area + 2 * math.pi * h * (R + r),
            "Wandstärke t": R - r,
            "Ring-Grundfläche G_ring": ring_area,
        }


    def calc_cone(self, v):
        r, h = v["r"], v["h"]
        s = math.sqrt(r * r + h * h)
        alpha_deg = math.degrees(math.atan2(r, h))
        return {
            "Mantellinie s": s,
            "Volumen V": math.pi * r ** 2 * h / 3,
            "Mantelfläche M": math.pi * r * s,
            "Oberfläche O": math.pi * r ** 2 + math.pi * r * s,
            "Öffnungs-Halbwinkel α": alpha_deg,
        }


    def calc_frustum(self, v):
        R, r, h = v["R"], v["r"], v["h"]
        if r >= R:
            raise ValueError("Kleiner Radius r muss kleiner als großer Radius R sein.")
        s = math.sqrt((R - r) ** 2 + h ** 2)
        base_area_diff = math.pi * (R ** 2 - r ** 2)
        return {
            "Mantellinie s": s,
            "Volumen V": math.pi * h * (R ** 2 + R * r + r ** 2) / 3,
            "Mantelfläche M": math.pi * (R + r) * s,
            "Oberfläche O": math.pi * (R + r) * s + math.pi * R ** 2 + math.pi * r ** 2,
            "Ringfläche (Grundflächen-Differenz)": base_area_diff,
            "Wandstärke radial t": R - r,
        }


    def calc_prism(self, v):
        G, U_G, h = v["G"], v["U_G"], v["h"]
        return {
            "Volumen V": G * h,
            "Mantelfläche M": U_G * h,
            "Oberfläche O": 2 * G + U_G * h,
            "Grundfläche G": G,
            "Grundumfang U_G": U_G,
        }


    def calc_pyramid(self, v):
        G, h, M = v["G"], v["h"], v["M"]
        return {
            "Volumen V": G * h / 3,
            "Oberfläche O": G + M,
            "Grundfläche G": G,
            "Mantelfläche M": M,
        }


    def calc_tetrahedron(self, v):
        a = v["a"]
        return {
            "Volumen V": a ** 3 / (6 * math.sqrt(2)),
            "Oberfläche O": math.sqrt(3) * a ** 2,
            "Höhe h": a * math.sqrt(2 / 3),
            "Inkugelradius r_i": a * math.sqrt(6) / 12,
            "Umkugelradius r_u": a * math.sqrt(6) / 4,
        }

    # ---------- Analytik ----------

    # ---------- Analytik ----------
    def calc_angle_circle(self, v):
        r, alpha_deg = v["r"], v["alpha_deg"]
        alpha_rad = math.radians(alpha_deg)
        return {
            "Winkel α_deg": alpha_deg,
            "Winkel α_rad": alpha_rad,
            "Bogenlänge s": r * alpha_rad,
            "Sehne c": 2 * r * math.sin(alpha_rad / 2),
            "Sektorfläche A": 0.5 * r * r * alpha_rad,
        }


    def calc_cartesian_polar(self, v):
        x, y = v["x"], v["y"]
        r = math.sqrt(x * x + y * y)
        phi_rad = math.atan2(y, x)
        phi_deg = math.degrees(phi_rad)
        return {
            "Radius r": r,
            "Winkel φ_rad": phi_rad,
            "Winkel φ_deg": phi_deg,
            "x aus Polar": r * math.cos(phi_rad),
            "y aus Polar": r * math.sin(phi_rad),
        }


    def calc_distance_2d(self, v):
        x1, y1, x2, y2 = v["x1"], v["y1"], v["x2"], v["y2"]
        dx = x2 - x1
        dy = y2 - y1
        return {
            "Δx": dx,
            "Δy": dy,
            "Abstand d": math.sqrt(dx ** 2 + dy ** 2),
            "Mittelpunkt x_M": (x1 + x2) / 2,
            "Mittelpunkt y_M": (y1 + y2) / 2,
        }


    def calc_line_2d(self, v):
        x1, y1, x2, y2 = v["x1"], v["y1"], v["x2"], v["y2"]
        if x2 == x1:
            raise ValueError("Senkrechte Gerade: Steigung nicht definiert.")
        m = (y2 - y1) / (x2 - x1)
        b = y1 - m * x1
        angle_deg = math.degrees(math.atan(m))
        return {
            "Steigung m": m,
            "Achsenabschnitt b": b,
            "Winkel zur x-Achse": angle_deg,
            "Geradengleichung": f"y = {self.fmt(m)}x + {self.fmt(b)}",
        }


def main():
    root = tk.Tk()
    style = ttk.Style()
    try:
        style.theme_use("clam")
    except Exception:
        pass
    AdvancedGeometryApp(root)
    root.mainloop()




def main():
    root = tk.Tk()
    style = ttk.Style()
    try:
        style.theme_use("clam")
    except Exception:
        pass
    AdvancedGeometryApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
