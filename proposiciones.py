from __future__ import annotations

import json
import re
import sys
import unicodedata
from pathlib import Path

VERSION = "v7 (Conectores, Esquemas y Árbol Semántico)"
ARCHIVO_DEFECTO = "reglas.json"

NEGACIONES = ("no", "nunca", "jamas", "tampoco")
PATRON_NEGACION_INICIAL = re.compile(
    r"^(?:(?:" + "|".join(NEGACIONES) + r")(?:\s+|$))+"
)
PATRON_SI_INICIAL = re.compile(r"^si\s+")

CONECTORES = {
    "bicondicional": {"simbolo": "↔", "nombre": "Bicondicional (↔)"},
    "condicional": {"simbolo": "→", "nombre": "Condicional (→)"},
    "disyuncion": {"simbolo": "∨", "nombre": "Disyunción (∨)"},
    "conjuncion": {"simbolo": "∧", "nombre": "Conjunción (∧)"},
    "negacion": {"simbolo": "¬", "nombre": "Negación (¬)"},
}

ALFABETO_PROPOSICIONES = [
    "p", "q", "r", "s", "t", "u", "v", "w", "x", "y", "z",
    "a", "b", "c", "d", "e", "f", "g", "h"
]


# ---------------------------------------------------------------- normalización
def normalizar(texto: str) -> str:
    """Minúsculas, sin acentos (conserva la ñ), sin signos ni espacios extra."""
    texto = texto.strip().lower()
    texto = texto.replace("ñ", "\x01")
    texto = unicodedata.normalize("NFD", texto)
    texto = "".join(c for c in texto if unicodedata.category(c) != "Mn")
    texto = texto.replace("\x01", "ñ")
    texto = re.sub(r"[^\w\s]", " ", texto)
    return re.sub(r"\s+", " ", texto).strip()


def detectar_negacion(proposicion: str) -> tuple[str, bool]:
    m = PATRON_NEGACION_INICIAL.match(proposicion)
    if not m:
        return proposicion, False
    cantidad = len(m.group(0).split())
    return proposicion[m.end():].strip(), cantidad % 2 == 1


# ---------------------------------------------------------------- base de datos
class BaseReglas:
    def __init__(self) -> None:
        self.reglas: dict[str, dict] = {}
        self.indice_proposiciones: dict[str, list[dict]] = {}
        self.firmas: dict[tuple, list[str]] = {}
        self.catalogo_atomos: dict[str, str] = {}  # "llueve" -> "p", "hay sol" -> "q"
        self._siguiente_regla = 1
        self._siguiente_atomo = 1

    def vaciar(self) -> None:
        self.reglas.clear()
        self.indice_proposiciones.clear()
        self.firmas.clear()
        self.catalogo_atomos.clear()
        self._siguiente_regla = 1
        self._siguiente_atomo = 1

    def obtener_o_crear_simbolo(self, proposicion: str) -> str:
        if proposicion not in self.catalogo_atomos:
            idx = self._siguiente_atomo - 1
            if idx < len(ALFABETO_PROPOSICIONES):
                simbolo = ALFABETO_PROPOSICIONES[idx]
            else:
                simbolo = f"p{self._siguiente_atomo}"
            self._siguiente_atomo += 1
            self.catalogo_atomos[proposicion] = simbolo
        return self.catalogo_atomos[proposicion]

    def texto_de_simbolo(self, simbolo: str) -> str:
        for prop, simb in self.catalogo_atomos.items():
            if simb == simbolo:
                return prop
        return simbolo

    def comparar_proposicion(self, proposicion: str, negada: bool) -> list[dict]:
        return [
            {**c, "misma_negacion": c["negada"] == negada}
            for c in self.indice_proposiciones.get(proposicion, [])
        ]

    def comparar_regla(self, proposiciones: list[str], negadas: list[bool]) -> list[str]:
        return list(self.firmas.get(tuple(zip(proposiciones, negadas)), []))

    def generar_id(self) -> str:
        id_regla = f"{self._siguiente_regla:03d}"
        self._siguiente_regla += 1
        return id_regla

    def almacenar(self, id_regla: str, datos_regla: dict) -> None:
        self.reglas[id_regla] = datos_regla
        props = datos_regla["proposiciones"]
        negs = datos_regla["negadas"]
        posiciones = datos_regla["posiciones"]

        for p, n, pos in zip(props, negs, posiciones):
            self.indice_proposiciones.setdefault(p, []).append(
                {"regla": id_regla, "posicion": pos, "negada": n}
            )
        self.firmas.setdefault(tuple(zip(props, negs)), []).append(id_regla)

    def guardar(self, ruta: str = ARCHIVO_DEFECTO) -> None:
        payload = {"catalogo_atomos": self.catalogo_atomos, "reglas": self.reglas}
        Path(ruta).write_text(
            json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    def cargar(self, ruta: str = ARCHIVO_DEFECTO) -> int:
        datos = json.loads(Path(ruta).read_text(encoding="utf-8"))
        self.vaciar()
        reglas_dict = datos.get("reglas", datos)
        self.catalogo_atomos = datos.get("catalogo_atomos", {})

        parser = ParserLogico(self)
        for id_regla, r in sorted(reglas_dict.items()):
            # Si el JSON es de una versión anterior sin esquema o símbolos, regenerarlos
            if "esquema" not in r or not r.get("simbolos"):
                texto = r.get("original", "")
                if texto:
                    info = parser.analizar(texto)
                    r["esquema"] = info["esquema"]
                    r["tipo_esquema"] = info["tipo_esquema"]
                    r["conectores"] = info["conectores"]
                    r["simbolos"] = info["simbolos"]
                    if not r.get("proposiciones"):
                        r["proposiciones"] = info["proposiciones"]
                    if "negadas" not in r:
                        r["negadas"] = info["negadas"]
                    if "posiciones" not in r:
                        r["posiciones"] = info["posiciones"]

            for p in r.get("proposiciones", []):
                self.obtener_o_crear_simbolo(p)
            self.almacenar(id_regla, r)

        if reglas_dict:
            self._siguiente_regla = max(int(i) for i in reglas_dict) + 1
        if self.catalogo_atomos:
            nums = [int(re.sub(r"\D", "", s)) for s in self.catalogo_atomos.values() if re.sub(r"\D", "", s)]
            self._siguiente_atomo = max(nums, default=0) + 1
        return len(reglas_dict)


# ---------------------------------------------------------------- parser lógico
class ParserLogico:
    def __init__(self, base: BaseReglas) -> None:
        self.base = base

    def analizar(self, texto: str) -> dict:
        norm = normalizar(texto)
        props: list[dict] = []
        conns: set[str] = set()

        esquema = self._parse_implicacion(norm, props, conns)

        if "condicional" in conns:
            tipo = "Condicional (Implicación)"
        elif "bicondicional" in conns:
            tipo = "Bicondicional (Doble Implicación)"
        elif "disyuncion" in conns:
            tipo = "Disyunción"
        elif "conjuncion" in conns:
            tipo = "Conjunción"
        elif "negacion" in conns:
            tipo = "Negación Simple"
        else:
            tipo = "Proposición Atómica"

        nombres_conns = [CONECTORES[c]["nombre"] for c in sorted(conns)] or ["(Atómica)"]

        return {
            "esquema": esquema,
            "tipo_esquema": tipo,
            "conectores": nombres_conns,
            "proposiciones": [p["texto"] for p in props],
            "negadas": [p["negada"] for p in props],
            "simbolos": [p["simbolo"] for p in props],
            "posiciones": list(range(1, len(props) + 1)),
        }

    def _parse_implicacion(self, texto: str, props: list[dict], conns: set[str]) -> str:
        partes = re.split(r"\bentonces\b", texto)
        if len(partes) > 1:
            conns.add("condicional")
            ant = PATRON_SI_INICIAL.sub("", partes[0].strip())
            cons = " entonces ".join(partes[1:]).strip()
            esq_ant = self._parse_bicondicional(ant, props, conns)
            esq_cons = self._parse_bicondicional(cons, props, conns)
            if any(op in esq_ant for op in ("∧", "∨", "↔")):
                esq_ant = f"({esq_ant})"
            if any(op in esq_cons for op in ("∧", "∨", "↔", "→")):
                esq_cons = f"({esq_cons})"
            return f"{esq_ant} → {esq_cons}"
        return self._parse_bicondicional(texto, props, conns)

    def _parse_bicondicional(self, texto: str, props: list[dict], conns: set[str]) -> str:
        partes = re.split(r"\b(?:si y solo si|syss)\b", texto)
        if len(partes) > 1:
            conns.add("bicondicional")
            sub_esq = [self._parse_disyuncion(p.strip(), props, conns) for p in partes]
            sub_form = [f"({s})" if any(op in s for op in ("∧", "∨")) else s for s in sub_esq]
            return " ↔ ".join(sub_form)
        return self._parse_disyuncion(texto, props, conns)

    def _parse_disyuncion(self, texto: str, props: list[dict], conns: set[str]) -> str:
        partes = re.split(r"\b(?:o|u)\b", texto)
        if len(partes) > 1:
            conns.add("disyuncion")
            return " ∨ ".join(self._parse_conjuncion(p.strip(), props, conns) for p in partes)
        return self._parse_conjuncion(texto, props, conns)

    def _parse_conjuncion(self, texto: str, props: list[dict], conns: set[str]) -> str:
        partes = re.split(r"\b(?:y|e)\b", texto)
        if len(partes) > 1:
            conns.add("conjuncion")
            return " ∧ ".join(self._parse_atomo(p.strip(), props, conns) for p in partes)
        return self._parse_atomo(texto, props, conns)

    def _parse_atomo(self, texto: str, props: list[dict], conns: set[str]) -> str:
        frag = PATRON_SI_INICIAL.sub("", texto).strip()
        limpia, negada = detectar_negacion(frag)
        if not limpia:
            return "?"
        simbolo = self.base.obtener_o_crear_simbolo(limpia)
        if negada:
            conns.add("negacion")
        props.append({"texto": limpia, "simbolo": simbolo, "negada": negada})
        return f"¬{simbolo}" if negada else simbolo


# ---------------------------------------------------------------- evaluador formal
class EvaluadorLogico:
    """Evalúa un esquema formal dada una asignación {p: True, q: False}."""

    def __init__(self, formula: str, asignacion: dict[str, bool]) -> None:
        self.tokens = re.findall(r"[a-zA-Z]\d*|¬|∧|∨|→|↔|\(|\)", formula)
        self.asignacion = asignacion
        self.pos = 0

    def _peek(self) -> str | None:
        return self.tokens[self.pos] if self.pos < len(self.tokens) else None

    def _consume(self) -> str:
        tok = self._peek()
        self.pos += 1
        return tok or ""

    def evaluar(self) -> bool:
        if not self.tokens:
            return True
        return self._parse_bicond()

    def _parse_bicond(self) -> bool:
        val = self._parse_impl()
        while self._peek() == "↔":
            self._consume()
            der = self._parse_impl()
            val = val == der
        return val

    def _parse_impl(self) -> bool:
        val = self._parse_disj()
        while self._peek() == "→":
            self._consume()
            der = self._parse_disj()
            val = (not val) or der
        return val

    def _parse_disj(self) -> bool:
        val = self._parse_conj()
        while self._peek() == "∨":
            self._consume()
            der = self._parse_conj()
            val = val or der
        return val

    def _parse_conj(self) -> bool:
        val = self._parse_unary()
        while self._peek() == "∧":
            self._consume()
            der = self._parse_unary()
            val = val and der
        return val

    def _parse_unary(self) -> bool:
        if self._peek() == "¬":
            self._consume()
            return not self._parse_unary()
        return self._parse_atom()

    def _parse_atom(self) -> bool:
        tok = self._consume()
        if tok == "(":
            res = self._parse_bicond()
            if self._peek() == ")":
                self._consume()
            return res
        return self.asignacion.get(tok, False)


# ---------------------------------------------------------------- visualizador de árbol semántico (consola)
class ArbolSemantico:
    """Construye y visualiza las ramas del árbol semántico en consola."""

    def __init__(self, base: BaseReglas, esquema: str, texto_regla: str) -> None:
        self.base = base
        self.esquema = esquema
        self.texto_regla = texto_regla
        simbolos_encontrados = re.findall(r"[a-zA-Z]\d*", esquema)
        self.variables = sorted(
            set(simbolos_encontrados),
            key=lambda x: (
                ALFABETO_PROPOSICIONES.index(x) if x in ALFABETO_PROPOSICIONES else 99,
                x
            )
        )
        self.modelos: list[dict[str, bool]] = []
        self.fallos: list[dict[str, bool]] = []

    def mostrar(self) -> None:
        print("\n" + "=" * 80)
        print("                 ÁRBOL SEMÁNTICO (RAMAS DE VALUACIÓN)")
        print("=" * 80)
        print(f" Regla:   \"{self.texto_regla}\"")
        print(f" Esquema: {self.esquema}")
        print(" Variables atómicas involucradas:")
        for v in self.variables:
            print(f"   • {v}: '{self.base.texto_de_simbolo(v)}'")
        print("-" * 80)

        if not self.variables:
            print("  (No hay variables para ramificar)\n")
            return

        print(f"\n ● Raíz: {self.esquema}")
        self._construir_ramas(nivel=0, asignacion={}, prefijo=" ")

        total = len(self.modelos) + len(self.fallos)
        porc = (len(self.modelos) / total * 100) if total else 0

        if len(self.fallos) == 0:
            clasif = "TAUTOLOGÍA (Válida en todas sus interpretaciones)"
        elif len(self.modelos) == 0:
            clasif = "CONTRADICCIÓN / INSATISFACIBLE (Todas las ramas fallan)"
        else:
            clasif = "CONTINGENCIA (Satisfecha en unas ramas y falsa en otras)"

        print("\n" + "-" * 80)
        print(" RESUMEN DEL ANÁLISIS SEMÁNTICO:")
        print(f"  • Total de interpretaciones (ramas evaluadas): {total}")
        print(f"  • Ramas que satisfacen la regla [✓]:         {len(self.modelos)} ({porc:.1f}%)")
        print(f"  • Ramas con contradicción / fallo [✗]:       {len(self.fallos)} ({100-porc:.1f}%)")
        print(f"  • Clasificación: {clasif}")

        if self.modelos:
            print("\n Modelos válidos (interpretaciones que hacen VERDADERA la regla):")
            for i, mod in enumerate(self.modelos, 1):
                asig_str = ", ".join(f"{k}={'V' if v else 'F'}" for k, v in mod.items())
                print(f"   [{i}] {asig_str}")
        print("=" * 80 + "\n")

    def _construir_ramas(self, nivel: int, asignacion: dict[str, bool], prefijo: str) -> None:
        var_actual = self.variables[nivel]
        nombre_prop = self.base.texto_de_simbolo(var_actual)
        es_ultimo_nivel = nivel == len(self.variables) - 1

        for valor_bool, es_rama_final in ((True, False), (False, True)):
            nueva_asig = dict(asignacion)
            nueva_asig[var_actual] = valor_bool

            etiqueta_val = "V" if valor_bool else "F"
            desc_val = nombre_prop if valor_bool else f"no {nombre_prop}"

            conector_rama = "└── " if es_rama_final else "├── "
            nodo_texto = f"{var_actual} = {etiqueta_val} ({desc_val})"

            if es_ultimo_nivel:
                evaluador = EvaluadorLogico(self.esquema, nueva_asig)
                es_valida = evaluador.evaluar()

                if es_valida:
                    self.modelos.append(nueva_asig)
                    resultado = "──► [✓ SATISFACE] (Modelo)"
                else:
                    self.fallos.append(nueva_asig)
                    resultado = "──► [✗ NODO DE FALLO] (Contramodelo)"

                print(f"{prefijo}{conector_rama}{nodo_texto} {resultado}")
            else:
                print(f"{prefijo}{conector_rama}{nodo_texto}")
                nuevo_prefijo = prefijo + ("    " if es_rama_final else "│   ")
                self._construir_ramas(nivel + 1, nueva_asig, nuevo_prefijo)


# ---------------------------------------------------------------- tablas y procesamiento
def mostrar_tablas(base: BaseReglas) -> None:
    print("\n" + "=" * 80)
    print("        TABLA 1: CATÁLOGO DE PROPOSICIONES ATÓMICAS (ÁLGEBRA PROPOSICIONAL)")
    print("=" * 80)

    if not base.catalogo_atomos:
        print("  (No hay proposiciones atómicas almacenadas todavía)\n")
    else:
        print(f" {'Símbolo':<10} | {'Proposición Atómica':<40} | {'Reglas donde aparece'}")
        print("-" * 80)
        simbolos_ordenados = sorted(
            base.catalogo_atomos.items(),
            key=lambda x: (
                ALFABETO_PROPOSICIONES.index(x[1]) if x[1] in ALFABETO_PROPOSICIONES else 99,
                x[1]
            )
        )
        for prop, simb in simbolos_ordenados:
            reglas_asoc = sorted({c["regla"] for c in base.indice_proposiciones.get(prop, [])})
            print(f" {simb:<10} | {prop:<40} | {', '.join(reglas_asoc) or '-'}")
        print()

    print("=" * 80)
    print("        TABLA 2: REGLAS Y ESQUEMAS LÓGICOS GENERADOS")
    print("=" * 80)

    if not base.reglas:
        print("  (No hay reglas almacenadas todavía)\n")
    else:
        print(f" {'ID':<5} | {'Esquema Lógico':<22} | {'Conectores Lógicos':<25} | {'Texto Original'}")
        print("-" * 80)
        for id_regla, r in sorted(base.reglas.items()):
            original = r["original"][:28] + "..." if len(r["original"]) > 28 else r["original"]
            conns = ", ".join(r.get("conectores", []))
            print(f" {id_regla:<5} | {r.get('esquema', '-'):<22} | {conns:<25} | {original}")
        print()


def procesar_texto(base: BaseReglas, texto: str) -> None:
    parser = ParserLogico(base)
    res = parser.analizar(texto)
    proposiciones = res["proposiciones"]
    negadas = res["negadas"]

    if not proposiciones:
        print("  ! No se detectaron proposiciones válidas.\n")
        return

    reglas_iguales = base.comparar_regla(proposiciones, negadas)
    if reglas_iguales:
        print(f"\n>> La regla es IDÉNTICA a: {', '.join(reglas_iguales)}")
        print("   No se almacenó para evitar redundancia.\n")
        return

    id_regla = base.generar_id()
    datos = {
        "original": texto.strip(),
        "esquema": res["esquema"],
        "tipo_esquema": res["tipo_esquema"],
        "conectores": res["conectores"],
        "proposiciones": proposiciones,
        "negadas": negadas,
        "simbolos": res["simbolos"],
        "posiciones": res["posiciones"],
    }
    base.almacenar(id_regla, datos)

    print(f"\n=== Regla {id_regla} almacenada con éxito ===")
    print(f"Texto original:    {texto.strip()}")
    print(f"Esquema Lógico:    {res['esquema']}")
    print(f"Tipo de Esquema:   {res['tipo_esquema']}")
    print(f"Conectores:        {', '.join(res['conectores'])}")

    print("\nProposiciones detectadas:")
    coincidencias = [base.comparar_proposicion(p, n) for p, n in zip(proposiciones, negadas)]
    for simb, p, n, coincide in zip(res["simbolos"], proposiciones, negadas, coincidencias):
        estado = "NEGADA" if n else "afirmada"
        print(f"  {simb}: '{p}' -> {estado}")
        otras = [c for c in coincide if c["regla"] != id_regla]
        if not otras:
            print("      (primera vez que aparece en la base)")
        for c in otras:
            rel = "igual negación" if c["misma_negacion"] else "negación OPUESTA"
            print(f"      ~ Aparece en Regla {c['regla']} (P{c['posicion']}) con {rel}")
    print()


def menu_arbol_semantico(base: BaseReglas) -> None:
    print("\n--- GENERAR ÁRBOL SEMÁNTICO VISUAL ---")
    if not base.reglas:
        print("  No hay reglas almacenadas en la base. Agrega una primero.\n")
        return

    print("Selecciona una regla para generar su árbol:")
    for id_regla, r in sorted(base.reglas.items()):
        print(f"  [{id_regla}] {r['esquema']}  <- \"{r['original']}\"")
    print("  [0] Ingresar una oración nueva en este momento")

    try:
        seleccion = input("\nElige una regla (ID o 0): ").strip()
    except (EOFError, KeyboardInterrupt):
        return

    if seleccion == "0":
        texto = input("Ingresa la oración para el árbol: ").strip()
        if texto:
            parser = ParserLogico(base)
            res = parser.analizar(texto)
            arbol = ArbolSemantico(base, res["esquema"], texto)
            arbol.mostrar()
        return

    id_formateado = f"{int(re.sub(r'\D', '', seleccion)):03d}" if re.sub(r'\D', '', seleccion) else seleccion
    if id_formateado in base.reglas:
        r = base.reglas[id_formateado]
        arbol = ArbolSemantico(base, r["esquema"], r["original"])
        arbol.mostrar()
    else:
        print("  ! ID de regla no encontrado.\n")


def listar(base: BaseReglas) -> None:
    if not base.reglas:
        print("  (no hay reglas almacenadas)\n")
        return
    print("\n--- Lista de Reglas Almacenadas ---")
    for id_regla, r in sorted(base.reglas.items()):
        print(f"  [{id_regla}] {r['original']}")
        print(f"        Esquema: {r.get('esquema', '-')}  | Conectores: {', '.join(r.get('conectores', []))}")
    print()


def confirmar(pregunta: str) -> bool:
    try:
        respuesta = input(f"{pregunta} (si/no): ")
    except (EOFError, KeyboardInterrupt):
        return False
    return normalizar(respuesta) in ("si", "s")


def borrar_base(base: BaseReglas, ruta: str = ARCHIVO_DEFECTO) -> None:
    archivo = Path(ruta)
    cantidad = len(base.reglas)
    if cantidad == 0 and not archivo.exists():
        print("  No hay nada que borrar.\n")
        return
    if cantidad:
        print(f"  ATENCIÓN: se borrarán {cantidad} reglas de la memoria.")
        if not confirmar("  ¿Estás seguro de que quieres vaciar la memoria?"):
            print("  Operación cancelada.\n")
            return
        base.vaciar()
        print("  Memoria vaciada correctamente.")
    if archivo.exists():
        if confirmar(f"  ¿Deseas también borrar el archivo '{ruta}'?"):
            try:
                archivo.unlink()
                print(f"  Archivo '{ruta}' eliminado.")
            except OSError as e:
                print(f"  Error al borrar el archivo: {e}")
    print()


def menu_agregar_reglas(base: BaseReglas) -> None:
    print("\n--- MODO: AGREGAR NUEVAS REGLAS ---")
    print("Conectores admitidos: 'si ... entonces', 'y', 'o', 'si y solo si', 'no'.")
    print("Escribe 'volver' o presiona Enter para regresar al menú principal.\n")
    while True:
        try:
            texto = input("Nueva Regla > ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not texto or normalizar(texto) in ("volver", "salir", "menu"):
            break
        procesar_texto(base, texto)


def main() -> None:
    try:
        sys.stdout.reconfigure(errors="replace")
    except Exception:
        pass

    base = BaseReglas()
    if Path(ARCHIVO_DEFECTO).exists():
        try:
            n = base.cargar()
            print(f"[Sistema] Se cargaron automáticamente {n} reglas desde {ARCHIVO_DEFECTO}")
        except Exception:
            pass

    while True:
        print("\n" + "=" * 60)
        print("   SISTEMAS EXPERTOS: MOTOR DE REGLAS Y PROPOSICIONES")
        print(f"   {VERSION}")
        print("=" * 60)
        print("  1. Agregar nueva(s) regla(s)")
        print("  2. Ver Tabla de Proposiciones Atómicas y Esquemas")
        print("  3. Generar Árbol Semántico Visual (Ramas y Modelos)")
        print("  4. Listar reglas almacenadas (detalle)")
        print("  5. Guardar base de reglas en archivo JSON")
        print("  6. Cargar base de reglas desde archivo JSON")
        print("  7. Borrar base de reglas (memoria / archivo)")
        print("  8. Salir")
        print("-" * 60)

        try:
            opcion = input("Selecciona una opción (1-8): ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nSaliendo del sistema...")
            break

        if opcion == "1":
            menu_agregar_reglas(base)
        elif opcion == "2":
            mostrar_tablas(base)
        elif opcion == "3":
            menu_arbol_semantico(base)
        elif opcion == "4":
            listar(base)
        elif opcion == "5":
            base.guardar()
            print(f"  Base guardada en '{ARCHIVO_DEFECTO}'.\n")
        elif opcion == "6":
            try:
                n = base.cargar()
                print(f"  {n} reglas cargadas desde '{ARCHIVO_DEFECTO}'.\n")
            except Exception as e:
                print(f"  Error al cargar: {e}\n")
        elif opcion == "7":
            borrar_base(base)
        elif opcion in ("8", "salir", "exit"):
            print("\n¡Hasta pronto!")
            break
        else:
            print("  Opción inválida. Ingresa un número del 1 al 8.")


if __name__ == "__main__":
    try:
        main()
    except Exception:
        import traceback
        traceback.print_exc()