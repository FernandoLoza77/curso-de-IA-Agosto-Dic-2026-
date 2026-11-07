# Encadenamiento hacia adelante y hacia atras (clausulas definidas, AIMA cap. 9)
# Ejercicio 1 de Razonamiento logico: quien entra de noche a la biblioteca.
#
# Escrito para entenderse: un atomo es una tupla ("Predicado", ("Arg1", "Arg2", ...)).
# Uso:  python3 1.encadenamiento.py 1.biblioteca.yaml

import sys
import yaml


# ---------------------------------------------------------------
# 1) ATOMOS Y UNIFICACION
# ---------------------------------------------------------------
def leer_atomo(texto):
    """'Miembro(x)' -> ('Miembro', ('x',))"""
    texto = texto.strip()
    predicado, resto = texto.split("(", 1)
    argumentos = resto.rstrip(")").split(",")
    return (predicado.strip(), tuple(a.strip() for a in argumentos))


def a_texto(atomo):
    """('Miembro', ('Ana',)) -> 'Miembro(Ana)'"""
    predicado, args = atomo
    return f"{predicado}({', '.join(args)})"


def es_variable(termino):
    """Las variables empiezan con minuscula: x, y, x_3."""
    return termino[0].islower()


def sustituir(atomo, theta):
    """Cambia cada variable por su valor en theta (si lo tiene)."""
    predicado, args = atomo
    nuevos = []
    for a in args:
        while es_variable(a) and a in theta:     # sigue la cadena x -> y -> Ana
            a = theta[a]
        nuevos.append(a)
    return (predicado, tuple(nuevos))


def unificar(a1, a2, theta):
    """Intenta hacer iguales a1 y a2. Regresa la sustitucion extendida o None."""
    if theta is None:
        return None
    a1 = sustituir(a1, theta)
    a2 = sustituir(a2, theta)
    if a1[0] != a2[0] or len(a1[1]) != len(a2[1]):
        return None                         # distinto predicado o aridad
    theta = dict(theta)                     # copia: no ensuciar la de afuera
    for t1, t2 in zip(a1[1], a2[1]):
        t1 = sustituir(("", (t1,)), theta)[1][0]
        t2 = sustituir(("", (t2,)), theta)[1][0]
        if t1 == t2:
            continue
        if es_variable(t1):
            theta[t1] = t2
        elif es_variable(t2):
            theta[t2] = t1
        else:
            return None                     # dos constantes distintas: Ana != Luis
    return theta


def sustitucion_bonita(theta):
    """Solo las variables originales (x_3 -> x) y su valor final: {x/Ana}."""
    partes = []
    for var in theta:
        valor = sustituir(("", (var,)), theta)[1][0]
        nombre = var.split("_")[0]
        if not es_variable(valor):
            texto = f"{nombre}/{valor}"
            if texto not in partes:
                partes.append(texto)
    return "{" + ", ".join(partes) + "}"


# ---------------------------------------------------------------
# 2) LA BASE DE CONOCIMIENTO
# ---------------------------------------------------------------
def cargar_base(ruta):
    with open(ruta, encoding="utf-8") as f:
        datos = yaml.safe_load(f)
    hechos = [leer_atomo(h) for h in datos["facts"]]
    reglas = []
    for r in datos["rules"]:
        premisas = [leer_atomo(p) for p in r["if"]]
        cabeza = leer_atomo(r["then"])
        reglas.append((r["id"], premisas, cabeza))
    consultas = [leer_atomo(q) for q in datos["queries"]]
    return hechos, reglas, consultas


def renombrar(regla, n):
    """Copia de la regla con variables nuevas: x -> x_n (para que dos usos no choquen)."""
    nombre, premisas, cabeza = regla

    def ren(atomo):
        pred, args = atomo
        return (pred, tuple(f"{a}_{n}" if es_variable(a) else a for a in args))

    return nombre, [ren(p) for p in premisas], ren(cabeza)


# ---------------------------------------------------------------
# 3) HACIA ADELANTE (dirigido por los datos)
# ---------------------------------------------------------------
def satisfacer(premisas, hechos, theta):
    """Todas las sustituciones que hacen verdaderas TODAS las premisas, en orden."""
    if not premisas:
        return [theta]
    primera, resto = premisas[0], premisas[1:]
    resultados = []
    for hecho in hechos:                       # los hechos en el orden en que estan
        theta2 = unificar(primera, hecho, theta)
        if theta2 is not None:
            resultados.extend(satisfacer(resto, hechos, theta2))
    return resultados


def hacia_adelante(hechos_iniciales, reglas, consulta, max_rondas=50):
    hechos = list(hechos_iniciales)
    nuevos_total = []
    traza = [f"Hechos iniciales: {', '.join(a_texto(h) for h in hechos)}",
             f"Consulta: {a_texto(consulta)}"]
    contador = 0

    for ronda in range(1, max_rondas + 1):
        traza.append(f"--- ronda {ronda} ---")
        nuevos = []                            # lo que sale en ESTA ronda
        for regla in reglas:                   # las reglas en el orden de la tabla
            contador += 1
            nombre, premisas, cabeza = renombrar(regla, contador)
            # OJO: uso 'hechos' (lo que habia al empezar la ronda), no 'nuevos'
            for theta in satisfacer(premisas, hechos, {}):
                conclusion = sustituir(cabeza, theta)
                if conclusion in hechos or conclusion in nuevos:
                    continue                   # ya lo sabia: no lo repito
                nuevos.append(conclusion)
                traza.append(f"Dispara {nombre} {sustitucion_bonita(theta)} => {a_texto(conclusion)}")
        if not nuevos:
            traza.append("Nada nuevo: se detiene.")
            break
        hechos.extend(nuevos)                  # hasta AHORA se pueden usar como premisas
        nuevos_total.extend(nuevos)

    # La consulta se busca al final, entre todo lo que quedo
    probada = False
    for hecho in hechos:
        if unificar(consulta, hecho, {}) is not None:
            probada = True
            break
    traza.append(f"Atomos nuevos: {', '.join(a_texto(a) for a in nuevos_total)}")
    traza.append("RESULTADO: probada" if probada else "RESULTADO: NO probada")
    return probada, nuevos_total, traza


# ---------------------------------------------------------------
# 4) HACIA ATRAS (dirigido por la meta)
# ---------------------------------------------------------------
def hacia_atras(hechos, reglas, consulta, max_prof=25):
    traza = [f"Consulta: {a_texto(consulta)}"]
    contador = [0]

    def sangria(p):
        return "  " * p

    def probar_meta(meta, theta, prof, pila):
        """bc_or: probar UNA meta. Primero hechos, luego reglas. Regresa theta o None."""
        meta = sustituir(meta, theta)
        if a_texto(meta) in pila:
            traza.append(f"{sangria(prof)}ciclo: {a_texto(meta)} ya esta en la pila, se corta")
            return None
        if prof > max_prof:
            traza.append(f"{sangria(prof)}demasiado profundo en {a_texto(meta)}")
            return None
        traza.append(f"{sangria(prof)}meta   {a_texto(meta)}")

        for hecho in hechos:                           # 1) es un hecho?
            theta2 = unificar(meta, hecho, theta)
            if theta2 is not None:
                traza.append(f"{sangria(prof)}hecho  {a_texto(hecho)}")
                return theta2

        for regla in reglas:                           # 2) alguna regla concluye la meta?
            contador[0] += 1
            nombre, premisas, cabeza = renombrar(regla, contador[0])
            theta2 = unificar(meta, cabeza, theta)
            if theta2 is None:
                continue                               # la cabeza no se parece: ni la abro
            traza.append(f"{sangria(prof)}regla  {nombre} {sustitucion_bonita(theta2)}")
            respuesta = probar_todas(premisas, theta2, prof + 1, pila + [a_texto(meta)])
            if respuesta is not None:
                return respuesta                       # la primera que funciona gana
        traza.append(f"{sangria(prof)}falla  {a_texto(meta)}")
        return None

    def probar_todas(premisas, theta, prof, pila):
        """bc_and: probar las premisas una tras otra; si una falla, falla todo."""
        if not premisas:
            return theta
        theta2 = probar_meta(premisas[0], theta, prof, pila)
        if theta2 is None:
            return None
        return probar_todas(premisas[1:], theta2, prof, pila)

    resultado = probar_meta(consulta, {}, 0, [])
    probada = resultado is not None
    traza.append("RESULTADO: probada" if probada else "RESULTADO: NO probada")
    return probada, traza


# ---------------------------------------------------------------
# 5) CORRER TODO
# ---------------------------------------------------------------
def correr(hechos, reglas, consultas, titulo):
    print("=" * 70)
    print(titulo)
    print("=" * 70)
    for q in consultas:
        print(f"\n##### {a_texto(q)} -- HACIA ADELANTE")
        _, _, traza = hacia_adelante(hechos, reglas, q)
        print("\n".join(traza))
        print(f"\n##### {a_texto(q)} -- HACIA ATRAS")
        _, traza = hacia_atras(hechos, reglas, q)
        print("\n".join(traza))
    print("\nResumen:")
    for q in consultas:
        ad = hacia_adelante(hechos, reglas, q)[0]
        at = hacia_atras(hechos, reglas, q)[0]
        print(f"  {a_texto(q):22s} adelante: {'si' if ad else 'no':2s}   atras: {'si' if at else 'no'}")
    print()


if __name__ == "__main__":
    ruta = sys.argv[1] if len(sys.argv) > 1 else "1.biblioteca.yaml"
    hechos, reglas, consultas = cargar_base(ruta)

    correr(hechos, reglas, consultas, "BASE DE LA BIBLIOTECA (sin cambios)")

    # Pregunta 3 del reporte: anadir TieneCredencial(Luis) (solo en memoria, el YAML no se toca)
    extra = hechos + [leer_atomo("TieneCredencial(Luis)")]
    correr(extra, reglas, [leer_atomo("AccesoNoche(Luis)")],
           "EXPERIMENTO: base + TieneCredencial(Luis)")
