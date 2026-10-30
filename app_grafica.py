from __future__ import annotations

import re
import sys
import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path

# Importar el motor lógico desde proposiciones.py
try:
    from proposiciones import BaseReglas, ParserLogico, EvaluadorLogico, ARCHIVO_DEFECTO, ALFABETO_PROPOSICIONES
except ImportError:
    sys.path.append(str(Path(__file__).parent))
    from proposiciones import BaseReglas, ParserLogico, EvaluadorLogico, ARCHIVO_DEFECTO, ALFABETO_PROPOSICIONES


class AppGraficaSistemasExpertos(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Sistemas Expertos - Visualizador de Grafos y Lógica Proposicional")
        self.geometry("1100x750")
        self.minsize(950, 650)

        # Instancia central de la base de conocimiento
        self.base = BaseReglas()
        if Path(ARCHIVO_DEFECTO).exists():
            try:
                self.base.cargar(ARCHIVO_DEFECTO)
            except Exception:
                pass

        self._configurar_estilos()
        self._construir_encabezado()
        self._construir_pestanas()

        self.actualizar_tablas()
        self.actualizar_selector_arbol()

    def _configurar_estilos(self) -> None:
        self.style = ttk.Style(self)
        self.style.theme_use("clam")

        self.COLOR_FONDO = "#F1F5F9"
        self.COLOR_PRIMARIO = "#2563EB"
        self.COLOR_TEXTO = "#1E293B"
        self.COLOR_VERDE = "#16A34A"
        self.COLOR_ROJO = "#DC2626"
        self.COLOR_TARJETA = "#FFFFFF"

        self.configure(bg=self.COLOR_FONDO)

        self.style.configure(".", background=self.COLOR_FONDO, foreground=self.COLOR_TEXTO, font=("Segoe UI", 10))
        self.style.configure("TNotebook", background=self.COLOR_FONDO, borderwidth=0)
        self.style.configure(
            "TNotebook.Tab",
            padding=[16, 8],
            font=("Segoe UI", 10, "bold"),
            background="#E2E8F0",
            foreground="#475569"
        )
        self.style.map(
            "TNotebook.Tab",
            background=[("selected", self.COLOR_PRIMARIO)],
            foreground=[("selected", "#FFFFFF")]
        )

        self.style.configure(
            "BotonPrimario.TButton",
            font=("Segoe UI", 10, "bold"),
            background=self.COLOR_PRIMARIO,
            foreground="#FFFFFF",
            padding=[12, 6]
        )
        self.style.map("BotonPrimario.TButton", background=[("active", "#1D4ED8")])

        self.style.configure(
            "BotonVerde.TButton",
            font=("Segoe UI", 10, "bold"),
            background=self.COLOR_VERDE,
            foreground="#FFFFFF",
            padding=[12, 6]
        )
        self.style.map("BotonVerde.TButton", background=[("active", "#15803D")])

        self.style.configure(
            "Treeview.Heading",
            font=("Segoe UI", 10, "bold"),
            background="#E2E8F0",
            foreground="#1E293B",
            padding=[6, 4]
        )
        self.style.configure("Treeview", rowheight=26, font=("Segoe UI", 9))

    def _construir_encabezado(self) -> None:
        header = tk.Frame(self, bg=self.COLOR_PRIMARIO, height=65)
        header.pack(fill="x", side="top")
        header.pack_propagate(False)

        lbl_titulo = tk.Label(
            header,
            text="SISTEMAS EXPERTOS: BASE DE REGLAS & ÁRBOLES SEMÁNTICOS",
            font=("Segoe UI", 14, "bold"),
            bg=self.COLOR_PRIMARIO,
            fg="#FFFFFF"
        )
        lbl_titulo.pack(side="left", padx=20, pady=8)

        lbl_sub = tk.Label(
            header,
            text="Lógica Proposicional • Análisis de Conectores • Visualizador de Grafos",
            font=("Segoe UI", 9),
            bg=self.COLOR_PRIMARIO,
            fg="#BFDBFE"
        )
        lbl_sub.pack(side="left", padx=10, pady=12)

    def _construir_pestanas(self) -> None:
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=15, pady=15)

        self.tab_agregar = ttk.Frame(self.notebook)
        self.tab_catalogo = ttk.Frame(self.notebook)
        self.tab_arbol = ttk.Frame(self.notebook)

        self.notebook.add(self.tab_agregar, text="  ➕ 1. Agregar Reglas  ")
        self.notebook.add(self.tab_catalogo, text="  📋 2. Ver Proposiciones y Reglas  ")
        self.notebook.add(self.tab_arbol, text="  🌳 3. Árbol Semántico (Grafo)  ")

        self._crear_vista_agregar()
        self._crear_vista_catalogo()
        self._crear_vista_arbol()

    # ----------------- VISTA 1: AGREGAR
    def _crear_vista_agregar(self) -> None:
        contenedor = tk.Frame(self.tab_agregar, bg=self.COLOR_FONDO)
        contenedor.pack(fill="both", expand=True, padx=20, pady=20)

        card_input = tk.Frame(contenedor, bg=self.COLOR_TARJETA, bd=1, relief="solid")
        card_input.pack(fill="x", pady=(0, 15), ipady=10, ipadx=10)

        lbl_instruccion = tk.Label(
            card_input,
            text="Escribe una regla usando conectores lógicos en lenguaje natural:\n('si ... entonces', 'y', 'o', 'si y solo si', 'no')",
            font=("Segoe UI", 11, "bold"),
            bg=self.COLOR_TARJETA,
            fg=self.COLOR_TEXTO,
            justify="left"
        )
        lbl_instruccion.pack(anchor="w", padx=15, pady=(5, 10))

        bar = tk.Frame(card_input, bg=self.COLOR_TARJETA)
        bar.pack(fill="x", padx=15, pady=5)

        self.entry_regla = ttk.Entry(bar, font=("Segoe UI", 11))
        self.entry_regla.pack(side="left", fill="x", expand=True, ipady=6, padx=(0, 10))
        self.entry_regla.bind("<Return>", lambda e: self._accion_agregar_regla())

        btn_procesar = ttk.Button(
            bar,
            text="Analizar y Almacenar Regla",
            style="BotonPrimario.TButton",
            command=self._accion_agregar_regla
        )
        btn_procesar.pack(side="right")

        frame_ej = tk.Frame(card_input, bg=self.COLOR_TARJETA)
        frame_ej.pack(fill="x", padx=15, pady=(8, 0))
        tk.Label(frame_ej, text="Ejemplos rápidos:", font=("Segoe UI", 8, "italic"), bg=self.COLOR_TARJETA, fg="#64748B").pack(side="left", padx=(0, 8))

        ejemplos = [
            "llueve entonces no hay sol",
            "si no llueve entonces hay sol",
            "llueve entonces no llueve",
            "paso la materia si y solo si estudio"
        ]
        for ej in ejemplos:
            tk.Button(
                frame_ej,
                text=ej,
                font=("Segoe UI", 8),
                bg="#F1F5F9",
                relief="groove",
                command=lambda t=ej: self._cargar_ejemplo(t)
            ).pack(side="left", padx=4)

        card_res = tk.Frame(contenedor, bg=self.COLOR_TARJETA, bd=1, relief="solid")
        card_res.pack(fill="both", expand=True, ipady=10, ipadx=10)

        tk.Label(
            card_res,
            text="RESULTADO DEL ANÁLISIS EN TIEMPO REAL:",
            font=("Segoe UI", 11, "bold"),
            bg=self.COLOR_TARJETA,
            fg=self.COLOR_PRIMARIO
        ).pack(anchor="w", padx=15, pady=(10, 5))

        self.txt_analisis = tk.Text(card_res, wrap="word", font=("Consolas", 10), bg="#F8FAFC", bd=1, relief="sunken")
        self.txt_analisis.pack(fill="both", expand=True, padx=15, pady=(5, 15))
        self.txt_analisis.insert("1.0", "Ingresa una regla arriba o pulsa un ejemplo para ver su análisis...")
        self.txt_analisis.config(state="disabled")

    def _cargar_ejemplo(self, texto: str) -> None:
        self.entry_regla.delete(0, tk.END)
        self.entry_regla.insert(0, texto)
        self._accion_agregar_regla()

    def _accion_agregar_regla(self) -> None:
        texto = self.entry_regla.get().strip()
        if not texto:
            messagebox.showwarning("Atención", "Por favor ingresa una regla lógica.")
            return

        parser = ParserLogico(self.base)
        resultado = parser.analizar(texto)
        props = resultado["proposiciones"]
        negs = resultado["negadas"]

        if not props:
            messagebox.showwarning("Error", "No se detectaron proposiciones lógicas válidas.")
            return

        reglas_iguales = self.base.comparar_regla(props, negs)
        ya_existe = len(reglas_iguales) > 0

        if ya_existe:
            id_regla = reglas_iguales[0]
            aviso = f"⚠️ La regla ya existía previamente con el ID: {', '.join(reglas_iguales)}"
        else:
            id_regla = self.base.generar_id()
            datos = {
                "original": texto,
                "esquema": resultado["esquema"],
                "tipo_esquema": resultado["tipo_esquema"],
                "conectores": resultado["conectores"],
                "proposiciones": props,
                "negadas": negs,
                "simbolos": resultado["simbolos"],
                "posiciones": resultado["posiciones"],
            }
            self.base.almacenar(id_regla, datos)
            aviso = "✅ ¡Regla almacenada con éxito en la base de conocimientos!"

        self.actualizar_tablas()
        self.actualizar_selector_arbol()

        salida = [
            f"{aviso}\n",
            f"• ID Asignado:      {id_regla}",
            f"• Texto Original:   \"{texto}\"",
            f"• Esquema Formal:   {resultado['esquema']}",
            f"• Tipo de Esquema:  {resultado['tipo_esquema']}",
            f"• Conectores:       {', '.join(resultado['conectores'])}\n",
            "PROPOSICIONES ATÓMICAS DETECTADAS:"
        ]
        for simb, p, n in zip(resultado["simbolos"], props, negs):
            salida.append(f"   [{simb}] '{p}' -> {'NEGADA (¬)' if n else 'AFIRMADA'}")

        self.txt_analisis.config(state="normal")
        self.txt_analisis.delete("1.0", tk.END)
        self.txt_analisis.insert("1.0", "\n".join(salida))
        self.txt_analisis.config(state="disabled")

        if not ya_existe:
            self.entry_regla.delete(0, tk.END)

    # ----------------- VISTA 2: CATÁLOGO
    def _crear_vista_catalogo(self) -> None:
        contenedor = tk.Frame(self.tab_catalogo, bg=self.COLOR_FONDO)
        contenedor.pack(fill="both", expand=True, padx=20, pady=15)

        toolbar = tk.Frame(contenedor, bg=self.COLOR_FONDO)
        toolbar.pack(fill="x", pady=(0, 10))

        ttk.Button(toolbar, text="💾 Guardar JSON", command=self._accion_guardar).pack(side="left", padx=4)
        ttk.Button(toolbar, text="📂 Cargar JSON", command=self._accion_cargar).pack(side="left", padx=4)
        ttk.Button(toolbar, text="🗑️ Vaciar Base", command=self._accion_vaciar).pack(side="left", padx=4)
        ttk.Button(toolbar, text="🔄 Actualizar Tablas", command=self.actualizar_tablas).pack(side="right", padx=4)

        paned = ttk.PanedWindow(contenedor, orient="vertical")
        paned.pack(fill="both", expand=True)

        frame_t1 = tk.Frame(paned, bg=self.COLOR_TARJETA, bd=1, relief="solid")
        paned.add(frame_t1, weight=1)
        tk.Label(frame_t1, text="TABLA 1: Catálogo de Proposiciones Atómicas", font=("Segoe UI", 10, "bold"), bg=self.COLOR_TARJETA, fg=self.COLOR_PRIMARIO).pack(anchor="w", padx=10, pady=(6, 2))

        self.tree_atomos = ttk.Treeview(frame_t1, columns=("simb", "prop", "reglas"), show="headings", height=5)
        self.tree_atomos.heading("simb", text="Letra / Símbolo")
        self.tree_atomos.heading("prop", text="Proposición en Lenguaje Natural")
        self.tree_atomos.heading("reglas", text="Reglas donde aparece")
        self.tree_atomos.column("simb", width=120, anchor="center")
        self.tree_atomos.column("prop", width=450, anchor="w")
        self.tree_atomos.column("reglas", width=200, anchor="center")

        scroll_t1 = ttk.Scrollbar(frame_t1, orient="vertical", command=self.tree_atomos.yview)
        self.tree_atomos.configure(yscrollcommand=scroll_t1.set)
        self.tree_atomos.pack(side="left", fill="both", expand=True, padx=(10, 0), pady=(0, 10))
        scroll_t1.pack(side="right", fill="y", pady=(0, 10), padx=(0, 10))

        frame_t2 = tk.Frame(paned, bg=self.COLOR_TARJETA, bd=1, relief="solid")
        paned.add(frame_t2, weight=1)
        tk.Label(frame_t2, text="TABLA 2: Reglas Almacenadas y Esquemas Lógicos", font=("Segoe UI", 10, "bold"), bg=self.COLOR_TARJETA, fg=self.COLOR_PRIMARIO).pack(anchor="w", padx=10, pady=(6, 2))

        self.tree_reglas = ttk.Treeview(frame_t2, columns=("id", "esquema", "tipo", "conectores", "texto"), show="headings", height=6)
        self.tree_reglas.heading("id", text="ID")
        self.tree_reglas.heading("esquema", text="Esquema Lógico")
        self.tree_reglas.heading("tipo", text="Tipo")
        self.tree_reglas.heading("conectores", text="Conectores")
        self.tree_reglas.heading("texto", text="Enunciado Original")

        self.tree_reglas.column("id", width=60, anchor="center")
        self.tree_reglas.column("esquema", width=160, anchor="center")
        self.tree_reglas.column("tipo", width=160, anchor="w")
        self.tree_reglas.column("conectores", width=200, anchor="w")
        self.tree_reglas.column("texto", width=360, anchor="w")

        scroll_t2 = ttk.Scrollbar(frame_t2, orient="vertical", command=self.tree_reglas.yview)
        self.tree_reglas.configure(yscrollcommand=scroll_t2.set)
        self.tree_reglas.pack(side="left", fill="both", expand=True, padx=(10, 0), pady=(0, 10))
        scroll_t2.pack(side="right", fill="y", pady=(0, 10), padx=(0, 10))

    def _obtener_esquema_seguro(self, regla: dict) -> str:
        """Devuelve el esquema de la regla. Si viene de un JSON antiguo sin 'esquema', lo calcula automáticamente."""
        if "esquema" in regla and regla["esquema"]:
            return regla["esquema"]
        parser = ParserLogico(self.base)
        texto = regla.get("original", "")
        info = parser.analizar(texto)
        regla["esquema"] = info["esquema"]
        regla["tipo_esquema"] = info["tipo_esquema"]
        regla["conectores"] = info["conectores"]
        regla["simbolos"] = info["simbolos"]
        if not regla.get("proposiciones"):
            regla["proposiciones"] = info["proposiciones"]
        if "negadas" not in regla:
            regla["negadas"] = info["negadas"]
        if "posiciones" not in regla:
            regla["posiciones"] = info["posiciones"]
        return info["esquema"]

    def actualizar_tablas(self) -> None:
        for row in self.tree_atomos.get_children():
            self.tree_atomos.delete(row)
        for row in self.tree_reglas.get_children():
            self.tree_reglas.delete(row)

        simbolos_ordenados = sorted(
            self.base.catalogo_atomos.items(),
            key=lambda x: (
                ALFABETO_PROPOSICIONES.index(x[1]) if x[1] in ALFABETO_PROPOSICIONES else 99,
                x[1]
            )
        )
        for prop, simb in simbolos_ordenados:
            reglas_asoc = sorted({c["regla"] for c in self.base.indice_proposiciones.get(prop, [])})
            self.tree_atomos.insert("", "end", values=(simb, prop, ", ".join(reglas_asoc) or "-"))

        for id_regla, r in sorted(self.base.reglas.items()):
            esq = self._obtener_esquema_seguro(r)
            conns = ", ".join(r.get("conectores", []))
            self.tree_reglas.insert(
                "",
                "end",
                values=(id_regla, esq, r.get("tipo_esquema", "-"), conns, r["original"])
            )

    def _accion_guardar(self) -> None:
        self.base.guardar(ARCHIVO_DEFECTO)
        messagebox.showinfo("Guardado", f"Base guardada en '{ARCHIVO_DEFECTO}'.")

    def _accion_cargar(self) -> None:
        try:
            n = self.base.cargar(ARCHIVO_DEFECTO)
            self.actualizar_tablas()
            self.actualizar_selector_arbol()
            messagebox.showinfo("Cargado", f"Se cargaron {n} reglas.")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo cargar: {e}")

    def _accion_vaciar(self) -> None:
        if messagebox.askyesno("Confirmar", "¿Vaciar toda la memoria?"):
            self.base.vaciar()
            self.actualizar_tablas()
            self.actualizar_selector_arbol()
            self.canvas_grafo.delete("all")
            self.lbl_clasificacion.config(text="Base vaciada.")

    # ----------------- VISTA 3: ÁRBOL SEMÁNTICO COMO GRAFO
    def _crear_vista_arbol(self) -> None:
        frame_contenedor = tk.Frame(self.tab_arbol, bg=self.COLOR_FONDO)
        frame_contenedor.pack(fill="both", expand=True, padx=20, pady=15)

        control_bar = tk.Frame(frame_contenedor, bg=self.COLOR_TARJETA, bd=1, relief="solid")
        control_bar.pack(fill="x", pady=(0, 10), ipady=8, ipadx=10)

        tk.Label(
            control_bar,
            text="Selecciona vista / regla:",
            font=("Segoe UI", 10, "bold"),
            bg=self.COLOR_TARJETA
        ).pack(side="left", padx=(10, 8))

        self.combo_reglas = ttk.Combobox(control_bar, state="readonly", width=46, font=("Segoe UI", 10))
        self.combo_reglas.pack(side="left", padx=5)

        btn_dibujar = ttk.Button(
            control_bar,
            text="🎨 Generar Grafo",
            style="BotonVerde.TButton",
            command=self._accion_dibujar_arbol
        )
        btn_dibujar.pack(side="left", padx=6)

        btn_global = ttk.Button(
            control_bar,
            text="🌳 Árbol Global (Todas en Uno)",
            command=self._accion_dibujar_arbol_global
        )
        btn_global.pack(side="left", padx=4)

        btn_todas = ttk.Button(
            control_bar,
            text="🌐 Árboles Paralelos",
            command=self._accion_dibujar_todas
        )
        btn_todas.pack(side="left", padx=4)

        btn_red = ttk.Button(
            control_bar,
            text="🔗 Red de Conexión",
            command=self._accion_dibujar_red
        )
        btn_red.pack(side="left", padx=4)

        # Leyenda visual de nodos
        leyenda = tk.Frame(control_bar, bg=self.COLOR_TARJETA)
        leyenda.pack(side="right", padx=15)
        tk.Label(leyenda, text="Leyenda:  ", font=("Segoe UI", 9, "bold"), bg=self.COLOR_TARJETA).pack(side="left")
        tk.Label(leyenda, text="✓ Modelo", bg="#DCFCE7", fg="#166534", font=("Segoe UI", 8, "bold"), padx=6, pady=2).pack(side="left", padx=2)
        tk.Label(leyenda, text="✗ Fallo", bg="#FEE2E2", fg="#991B1B", font=("Segoe UI", 8, "bold"), padx=6, pady=2).pack(side="left", padx=2)
        tk.Label(leyenda, text="★ Conector", bg="#FEF3C7", fg="#92400E", font=("Segoe UI", 8, "bold"), padx=6, pady=2).pack(side="left", padx=2)

        frame_canvas = tk.Frame(frame_contenedor, bg=self.COLOR_TARJETA, bd=1, relief="solid")
        frame_canvas.pack(fill="both", expand=True)

        self.canvas_grafo = tk.Canvas(frame_canvas, bg="#F8FAFC", highlightthickness=0)
        scroll_x = ttk.Scrollbar(frame_canvas, orient="horizontal", command=self.canvas_grafo.xview)
        scroll_y = ttk.Scrollbar(frame_canvas, orient="vertical", command=self.canvas_grafo.yview)
        self.canvas_grafo.configure(xscrollcommand=scroll_x.set, yscrollcommand=scroll_y.set)

        scroll_y.pack(side="right", fill="y")
        scroll_x.pack(side="bottom", fill="x")
        self.canvas_grafo.pack(side="left", fill="both", expand=True)

        self.frame_resumen = tk.Frame(frame_contenedor, bg=self.COLOR_TARJETA, bd=1, relief="solid")
        self.frame_resumen.pack(fill="x", pady=(10, 0), ipady=6, ipadx=10)

        self.lbl_clasificacion = tk.Label(
            self.frame_resumen,
            text="Selecciona una regla o 'Árbol Global' para evaluar la base de conocimientos.",
            font=("Segoe UI", 10, "bold"),
            bg=self.COLOR_TARJETA,
            fg=self.COLOR_PRIMARIO
        )
        self.lbl_clasificacion.pack(side="left", padx=10)

    def actualizar_selector_arbol(self) -> None:
        opciones = [
            "🌟 [ÁRBOL GLOBAL: Todas las Reglas en un Solo Árbol]",
            "🌐 [ÁRBOLES PARALELOS (Uno al lado del otro)]",
            "🔗 [RED DE REGLAS (Grafo de Conexiones por Proposiciones)]"
        ]
        for id_regla, r in sorted(self.base.reglas.items()):
            esq = self._obtener_esquema_seguro(r)
            opciones.append(f"[{id_regla}] {esq}  —  \"{r['original'][:30]}\"")
        self.combo_reglas["values"] = opciones
        if opciones:
            self.combo_reglas.current(0)
        else:
            self.combo_reglas.set("")

    # ---------------------------------------------------------------- DIBUJADO DEL GRAFO DEL ÁRBOL
    def _accion_dibujar_arbol(self) -> None:
        sel = self.combo_reglas.get()
        if not sel:
            messagebox.showinfo("Información", "Primero agrega una regla para poder generar su árbol semántico.")
            return

        if "ÁRBOL GLOBAL" in sel:
            self._accion_dibujar_arbol_global()
            return
        elif "ÁRBOLES PARALELOS" in sel or "TODAS LAS REGLAS JUNTAS" in sel:
            self._accion_dibujar_todas()
            return
        elif "RED DE REGLAS" in sel:
            self._accion_dibujar_red()
            return

        match = re.match(r"\[(\d+)\]", sel)
        if not match:
            return
        id_regla = match.group(1)
        self._dibujar_regla_individual(id_regla)

    def _accion_dibujar_arbol_global(self) -> None:
        """Construye UN SOLO ÁRBOL SEMÁNTICO que evalúa simultáneamente toda la Base de Conocimiento."""
        self.canvas_grafo.delete("all")
        if not self.base.reglas:
            self.lbl_clasificacion.config(text="No hay reglas almacenadas en la base de conocimientos.")
            return

        # 1. Obtener todas las variables atómicas únicas de toda la base (ordenadas p, q, r, s...)
        simbolos_globales = set()
        for id_regla, r in self.base.reglas.items():
            esq = self._obtener_esquema_seguro(r)
            simbolos_globales.update(re.findall(r"[a-zA-Z]\d*", esq))

        variables = sorted(
            simbolos_globales,
            key=lambda x: (
                ALFABETO_PROPOSICIONES.index(x) if x in ALFABETO_PROPOSICIONES else 99,
                x
            )
        )

        if not variables:
            self.lbl_clasificacion.config(text="No se detectaron variables proposicionales para ramificar.")
            return

        num_vars = len(variables)
        total_hojas = 2 ** num_vars

        ESPACIO_HOJA = 125
        ALTO_NIVEL = 110
        MARGEN_Y = 125
        MARGEN_X = 60

        ancho_total = max(total_hojas * ESPACIO_HOJA + MARGEN_X * 2, 950)
        alto_total = (num_vars + 1) * ALTO_NIVEL + MARGEN_Y + 70
        self.canvas_grafo.config(scrollregion=(0, 0, ancho_total, alto_total))

        self.modelos_grafo = []
        self.fallos_grafo = []

        rx = ancho_total / 2

        # Encabezado superior
        self._dibujar_nodo_capsula(
            rx, 35,
            "ÁRBOL SEMÁNTICO GLOBAL (CONJUNCIÓN DE TODAS LAS REGLAS)",
            bg="#0F172A", fg="#38BDF8", ancho=500, alto=36
        )

        formulas_txt = " ∧ ".join(f"[{id_r}] {self._obtener_esquema_seguro(r)}" for id_r, r in sorted(self.base.reglas.items()))
        if len(formulas_txt) > 85:
            formulas_txt = formulas_txt[:82] + "..."
        self.canvas_grafo.create_text(
            rx, 70,
            text=f"Evaluación conjunta: {formulas_txt}",
            font=("Segoe UI", 9, "bold italic"),
            fill="#475569"
        )

        # Función de evaluación conjunta para las hojas
        def evaluar_base_completa(asignacion: dict[str, bool]) -> tuple[bool, str]:
            fallos = []
            for id_r, r in sorted(self.base.reglas.items()):
                esq = self._obtener_esquema_seguro(r)
                ev = EvaluadorLogico(esq, asignacion)
                if not ev.evaluar():
                    fallos.append(id_r)
            if not fallos:
                self.modelos_grafo.append(asignacion)
                return True, "✓ MODELO GLOBAL"
            else:
                self.fallos_grafo.append(asignacion)
                return False, f"✗ FALLO (R{','.join(fallos)})"

        # Dibujar el árbol único sin repetir nodos
        self._dibujar_arbol_decision(
            x=rx,
            y=MARGEN_Y,
            nivel=0,
            variables=variables,
            min_x=MARGEN_X,
            max_x=ancho_total - MARGEN_X,
            asignacion={},
            evaluador_fn=evaluar_base_completa,
            alto_nivel=ALTO_NIVEL
        )

        total_ramas = len(self.modelos_grafo) + len(self.fallos_grafo)
        num_modelos = len(self.modelos_grafo)
        porc = (num_modelos / total_ramas * 100) if total_ramas else 0

        if num_modelos > 0:
            clasif = f"BASE CONSISTENTE (Existen {num_modelos} modelos válidos para todas las reglas)"
            color_res = "#15803D"
        else:
            clasif = "BASE INCONSISTENTE / CONTRADICTORIA (0 modelos globales, todas las ramas fallan)"
            color_res = "#B91C1C"

        self.lbl_clasificacion.config(
            text=f"Árbol Global: {clasif}  •  {porc:.1f}% de satisfacción simultánea ({num_modelos}/{total_ramas} ramas).",
            fg=color_res
        )

    def _dibujar_arbol_decision(
        self,
        x: float,
        y: float,
        nivel: int,
        variables: list[str],
        min_x: float,
        max_x: float,
        asignacion: dict[str, bool],
        evaluador_fn,
        alto_nivel: int
    ) -> None:
        """Dibuja limpiamente cada nodo de decisión y sus ramas sin repetir variables en niveles incorrectos."""
        var_actual = variables[nivel]
        nombre_prop = self.base.texto_de_simbolo(var_actual)
        es_ultimo = (nivel == len(variables) - 1)

        # 1. Dibujar el nodo de decisión para la variable actual
        self._dibujar_nodo_decision(x, y, var_actual, nombre_prop)

        # 2. Calcular posiciones de las ramas
        y_hijo = y + alto_nivel
        rango = (max_x - min_x) / 2
        x_izq = min_x + rango / 2
        x_der = min_x + rango + rango / 2

        # Rama Izquierda: Verdadero (V)
        asig_v = dict(asignacion)
        asig_v[var_actual] = True
        self._dibujar_arista_grafo(x, y, x_izq, y_hijo, f"{var_actual}=V", "#16A34A")

        if es_ultimo:
            valido_v, texto_v = evaluador_fn(asig_v)
            self._dibujar_nodo_hoja(x_izq, y_hijo, texto_v, valido_v)
        else:
            self._dibujar_arbol_decision(
                x_izq, y_hijo, nivel + 1, variables,
                min_x, min_x + rango, asig_v, evaluador_fn, alto_nivel
            )

        # Rama Derecha: Falso (F)
        asig_f = dict(asignacion)
        asig_f[var_actual] = False
        self._dibujar_arista_grafo(x, y, x_der, y_hijo, f"{var_actual}=F", "#DC2626")

        if es_ultimo:
            valido_f, texto_f = evaluador_fn(asig_f)
            self._dibujar_nodo_hoja(x_der, y_hijo, texto_f, valido_f)
        else:
            self._dibujar_arbol_decision(
                x_der, y_hijo, nivel + 1, variables,
                min_x + rango, max_x, asig_f, evaluador_fn, alto_nivel
            )

    def _accion_dibujar_todas(self) -> None:
        """Dibuja todos los árboles semánticos juntos lado a lado en el mismo lienzo."""
        self.canvas_grafo.delete("all")
        if not self.base.reglas:
            self.lbl_clasificacion.config(text="No hay reglas almacenadas en la base de conocimientos.")
            return

        ESPACIO_HOJA = 95
        ALTO_NIVEL = 105
        MARGEN_Y = 110
        SEPARACION_ENTRE_GRAFOS = 80

        offset_x = 40
        max_alto = 0
        total_grafos = 0

        self.modelos_grafo = []
        self.fallos_grafo = []

        for id_regla, regla in sorted(self.base.reglas.items()):
            esquema = self._obtener_esquema_seguro(regla)
            simbolos = re.findall(r"[a-zA-Z]\d*", esquema)
            variables = sorted(
                set(simbolos),
                key=lambda x: (
                    ALFABETO_PROPOSICIONES.index(x) if x in ALFABETO_PROPOSICIONES else 99,
                    x
                )
            )

            if not variables:
                continue

            total_grafos += 1
            num_vars = len(variables)
            total_hojas = 2 ** num_vars
            ancho_arbol = max(total_hojas * ESPACIO_HOJA, 260)
            alto_arbol = (num_vars + 1) * ALTO_NIVEL + MARGEN_Y + 50

            if alto_arbol > max_alto:
                max_alto = alto_arbol

            rx = offset_x + ancho_arbol / 2

            # Título de la regla sobre su árbol
            self.canvas_grafo.create_rectangle(
                offset_x, 20,
                offset_x + ancho_arbol, 54,
                fill="#F1F5F9", outline="#CBD5E1", width=1
            )
            self.canvas_grafo.create_text(
                rx, 37,
                text=f"REGLA [{id_regla}]: \"{regla['original'][:30]}\"",
                font=("Segoe UI", 9, "bold"),
                fill="#1E293B"
            )

            # Nodo Raíz
            self._dibujar_nodo_capsula(rx, 75, f"[{id_regla}] {esquema}", bg="#1E293B", fg="#FFFFFF", ancho=min(ancho_arbol - 20, 210), alto=30)

            def ev_fn(asig: dict[str, bool]) -> tuple[bool, str]:
                ev = EvaluadorLogico(esquema, asig)
                if ev.evaluar():
                    return True, "✓ MODELO"
                else:
                    return False, "✗ FALLO"

            self._dibujar_arbol_decision(
                x=rx,
                y=MARGEN_Y,
                nivel=0,
                variables=variables,
                min_x=offset_x + 10,
                max_x=offset_x + ancho_arbol - 10,
                asignacion={},
                evaluador_fn=ev_fn,
                alto_nivel=ALTO_NIVEL
            )

            # Línea divisoria vertical entre grafos
            line_x = offset_x + ancho_arbol + (SEPARACION_ENTRE_GRAFOS / 2)
            self.canvas_grafo.create_line(line_x, 20, line_x, max(alto_arbol, 550), fill="#CBD5E1", width=1, dash=(4, 4))

            offset_x += ancho_arbol + SEPARACION_ENTRE_GRAFOS

        ancho_total = max(offset_x, 950)
        alto_total = max(max_alto + 40, 600)
        self.canvas_grafo.config(scrollregion=(0, 0, ancho_total, alto_total))

        self.lbl_clasificacion.config(
            text=f"Mostrando {total_grafos} grafos de reglas juntos en paralelo. Desplázate horizontalmente (scroll) para verlos todos.",
            fg="#2563EB"
        )

    def _accion_dibujar_red(self) -> None:
        """Dibuja la Red de Conocimiento: Grafo que une proposiciones con reglas y resalta las compartidas."""
        self.canvas_grafo.delete("all")
        if not self.base.reglas:
            self.lbl_clasificacion.config(text="No hay reglas almacenadas en la base de conocimientos.")
            return

        apariciones_prop: dict[str, list[str]] = {}
        for id_regla, r in sorted(self.base.reglas.items()):
            self._obtener_esquema_seguro(r)
            for p in r.get("simbolos", []):
                apariciones_prop.setdefault(p, []).append(id_regla)

        compartidas = {p: reglas for p, reglas in apariciones_prop.items() if len(reglas) > 1}

        MARGEN_X = 80
        MARGEN_Y = 80
        ALTO_FILA = 60

        props_ordenadas = sorted(
            self.base.catalogo_atomos.items(),
            key=lambda x: (
                ALFABETO_PROPOSICIONES.index(x[1]) if x[1] in ALFABETO_PROPOSICIONES else 99,
                x[1]
            )
        )
        reglas_ordenadas = sorted(self.base.reglas.items())

        total_filas = max(len(props_ordenadas), len(reglas_ordenadas))
        alto_total = max(total_filas * ALTO_FILA + MARGEN_Y * 2, 600)
        ancho_total = 1000

        self.canvas_grafo.config(scrollregion=(0, 0, ancho_total, alto_total))

        x_props = MARGEN_X + 130
        x_reglas = ancho_total - MARGEN_X - 160

        self.canvas_grafo.create_text(x_props, 35, text="PROPOSICIONES ATÓMICAS", font=("Segoe UI", 12, "bold"), fill="#1E293B")
        self.canvas_grafo.create_text(x_reglas, 35, text="REGLAS DE LA BASE", font=("Segoe UI", 12, "bold"), fill="#1E293B")

        pos_props: dict[str, tuple[float, float]] = {}
        pos_reglas: dict[str, tuple[float, float]] = {}

        # 1. Dibujar Proposiciones
        y_p = MARGEN_Y + 20
        for prop_txt, simb in props_ordenadas:
            es_compartida = simb in compartidas
            bg_prop = "#FEF3C7" if es_compartida else "#F1F5F9"
            borde_prop = "#D97706" if es_compartida else "#94A3B8"
            fg_prop = "#92400E" if es_compartida else "#1E293B"

            w, h = 120, 20
            self.canvas_grafo.create_rectangle(x_props - w, y_p - h, x_props + w, y_p + h, fill=bg_prop, outline=borde_prop, width=2 if es_compartida else 1)
            desc = prop_txt if len(prop_txt) <= 22 else prop_txt[:20] + ".."
            estrella = " ★" if es_compartida else ""
            self.canvas_grafo.create_text(x_props, y_p, text=f"{simb}: {desc}{estrella}", font=("Segoe UI", 9, "bold" if es_compartida else "normal"), fill=fg_prop)

            pos_props[simb] = (x_props + w, y_p)
            y_p += ALTO_FILA

        # 2. Dibujar Reglas
        y_r = MARGEN_Y + 20
        for id_regla, r in reglas_ordenadas:
            esq_r = self._obtener_esquema_seguro(r)
            w, h = 150, 22
            self.canvas_grafo.create_rectangle(x_reglas - w, y_r - h, x_reglas + w, y_r + h, fill="#EFF6FF", outline="#2563EB", width=2)
            self.canvas_grafo.create_text(x_reglas, y_r - 7, text=f"Regla [{id_regla}]: {esq_r}", font=("Segoe UI", 9, "bold"), fill="#1E3A8A")
            desc_r = r["original"] if len(r["original"]) <= 28 else r["original"][:26] + ".."
            self.canvas_grafo.create_text(x_reglas, y_r + 9, text=f"\"{desc_r}\"", font=("Segoe UI", 8, "italic"), fill="#475569")

            pos_reglas[id_regla] = (x_reglas - w, y_r)
            y_r += ALTO_FILA

        # 3. Dibujar Aristas de conexión
        for id_regla, r in reglas_ordenadas:
            xr, yr = pos_reglas[id_regla]
            self._obtener_esquema_seguro(r)
            for simb in r.get("simbolos", []):
                if simb in pos_props:
                    xp, yp = pos_props[simb]
                    es_compartida = simb in compartidas
                    color_linea = "#D97706" if es_compartida else "#94A3B8"
                    grosor = 2.5 if es_compartida else 1.2

                    self.canvas_grafo.create_line(
                        xp, yp, xr, yr,
                        fill=color_linea,
                        width=grosor,
                        arrow=tk.LAST,
                        arrowshape=(8, 10, 4)
                    )

        if compartidas:
            detalles = [f"{s} (en reglas {', '.join(rs)})" for s, rs in compartidas.items()]
            texto_res = f"🔗 Red Conectada: Las proposiciones marcadas con ★ ({'; '.join(detalles)}) unen las reglas en un mismo grafo."
            color_res = "#B45309"
        else:
            texto_res = "Red de Conocimiento: Todas las reglas son independientes (no comparten proposiciones comunes)."
            color_res = "#2563EB"

        self.lbl_clasificacion.config(text=texto_res, fg=color_res)

    def _dibujar_regla_individual(self, id_regla: str) -> None:
        """Dibuja el árbol semántico tradicional de una sola regla seleccionada."""
        regla = self.base.reglas.get(id_regla)
        if not regla:
            return

        esquema = self._obtener_esquema_seguro(regla)
        texto_original = regla["original"]

        simbolos = re.findall(r"[a-zA-Z]\d*", esquema)
        variables = sorted(
            set(simbolos),
            key=lambda x: (
                ALFABETO_PROPOSICIONES.index(x) if x in ALFABETO_PROPOSICIONES else 99,
                x
            )
        )

        self.canvas_grafo.delete("all")

        if not variables:
            self.lbl_clasificacion.config(text="La regla no contiene variables proposicionales para ramificar.")
            return

        num_vars = len(variables)
        total_hojas = 2 ** num_vars

        ESPACIO_HOJA = 120
        ALTO_NIVEL = 110
        MARGEN_X = 60
        MARGEN_Y = 110

        ancho_total = max(total_hojas * ESPACIO_HOJA + MARGEN_X * 2, 900)
        alto_total = (num_vars + 1) * ALTO_NIVEL + MARGEN_Y + 50
        self.canvas_grafo.config(scrollregion=(0, 0, ancho_total, alto_total))

        self.modelos_grafo = []
        self.fallos_grafo = []

        rx = ancho_total / 2
        # Encabezado
        self._dibujar_nodo_capsula(rx, 35, f"REGLA [{id_regla}]: {esquema}", bg="#1E293B", fg="#FFFFFF", ancho=280, alto=34)
        self.canvas_grafo.create_text(rx, 68, text=f"\"{texto_original}\"", font=("Segoe UI", 9, "italic"), fill="#64748B")

        def evaluador_regla(asig: dict[str, bool]) -> tuple[bool, str]:
            ev = EvaluadorLogico(esquema, asig)
            if ev.evaluar():
                self.modelos_grafo.append(asig)
                return True, "✓ MODELO"
            else:
                self.fallos_grafo.append(asig)
                return False, "✗ FALLO"

        self._dibujar_arbol_decision(
            x=rx,
            y=MARGEN_Y,
            nivel=0,
            variables=variables,
            min_x=MARGEN_X,
            max_x=ancho_total - MARGEN_X,
            asignacion={},
            evaluador_fn=evaluador_regla,
            alto_nivel=ALTO_NIVEL
        )

        total_ramas = len(self.modelos_grafo) + len(self.fallos_grafo)
        porc = (len(self.modelos_grafo) / total_ramas * 100) if total_ramas else 0

        if len(self.fallos_grafo) == 0:
            clasif = "TAUTOLOGÍA (Válida en el 100% de los casos)"
            color_res = "#15803D"
        elif len(self.modelos_grafo) == 0:
            clasif = "CONTRADICCIÓN (Insatisfacible en todas las ramas)"
            color_res = "#B91C1C"
        else:
            clasif = f"CONTINGENCIA ({len(self.modelos_grafo)} Modelos [✓], {len(self.fallos_grafo)} Fallos [✗])"
            color_res = "#1D4ED8"

        self.lbl_clasificacion.config(
            text=f"Análisis Semántico de '{esquema}':  {clasif}  •  {porc:.1f}% de satisfacción.",
            fg=color_res
        )

    def _dibujar_arista_grafo(self, x1: float, y1: float, x2: float, y2: float, etiqueta: str, color_arista: str) -> None:
        self.canvas_grafo.create_line(x1, y1 + 16, x2, y2 - 16, fill="#94A3B8", width=2, arrow=tk.LAST, arrowshape=(8, 10, 4))
        mx = (x1 + x2) / 2
        my = (y1 + y2) / 2
        ancho_tag, alto_tag = 24, 10
        self.canvas_grafo.create_rectangle(mx - ancho_tag, my - alto_tag, mx + ancho_tag, my + alto_tag, fill="#FFFFFF", outline=color_arista, width=1.5)
        self.canvas_grafo.create_text(mx, my, text=etiqueta, font=("Segoe UI", 8, "bold"), fill=color_arista)

    def _dibujar_nodo_capsula(self, x: float, y: float, texto: str, bg: str, fg: str, ancho: int = 150, alto: int = 32) -> None:
        w, h = ancho / 2, alto / 2
        self.canvas_grafo.create_rectangle(x - w, y - h, x + w, y + h, fill=bg, outline="#0F172A", width=1.5)
        self.canvas_grafo.create_text(x, y, text=texto, font=("Segoe UI", 10, "bold"), fill=fg)

    def _dibujar_nodo_decision(self, x: float, y: float, simbolo: str, texto_prop: str) -> None:
        w, h = 58, 18
        self.canvas_grafo.create_rectangle(x - w, y - h, x + w, y + h, fill="#EFF6FF", outline="#2563EB", width=2)
        desc = texto_prop if len(texto_prop) <= 14 else texto_prop[:12] + ".."
        self.canvas_grafo.create_text(x, y, text=f"{simbolo} ({desc})", font=("Segoe UI", 9, "bold"), fill="#1E3A8A")

    def _dibujar_nodo_hoja(self, x: float, y: float, texto: str, es_modelo: bool) -> None:
        w, h = 58, 15
        bg = "#DCFCE7" if es_modelo else "#FEE2E2"
        borde = "#16A34A" if es_modelo else "#DC2626"
        fg = "#14532D" if es_modelo else "#7F1D1D"
        self.canvas_grafo.create_rectangle(x - w, y - h, x + w, y + h, fill=bg, outline=borde, width=2)
        self.canvas_grafo.create_text(x, y, text=texto, font=("Segoe UI", 8, "bold"), fill=fg)


def main() -> None:
    app = AppGraficaSistemasExpertos()
    app.mainloop()


if __name__ == "__main__":
    main()