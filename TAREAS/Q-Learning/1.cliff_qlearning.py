# Q-learning en Cliff Walking (el del libro de Sutton y Barto, 4 x 12)
# Escrito para entenderse: sin NumPy, sin Gym, solo listas y diccionarios.

import random

# ---------------------------------------------------------------
# 1) EL MUNDO
# ---------------------------------------------------------------
FILAS = 4
COLUMNAS = 12

INICIO = (3, 0)    # S
META = (3, 11)     # G

# El acantilado: la fila de abajo, de la columna 1 a la 10
ACANTILADO = []
for col in range(1, 11):
    ACANTILADO.append((3, col))

# Cada accion dice cuanto se mueve (fila, columna).
# OJO: la fila 0 es la de ARRIBA, por eso "N" resta 1 a la fila.
ACCIONES = ["N", "E", "S", "W"]          # este orden tambien desempata
MOVIMIENTO = {
    "N": (-1, 0),
    "E": (0, +1),
    "S": (+1, 0),
    "W": (0, -1),
}


def dar_un_paso(estado, accion):
    """Regresa (siguiente_estado, recompensa, termino_el_episodio)."""
    fila, col = estado
    df, dc = MOVIMIENTO[accion]
    nueva_fila = fila + df
    nueva_col = col + dc

    # Si me saldria del mapa, me quedo donde estoy
    if nueva_fila < 0 or nueva_fila >= FILAS:
        nueva_fila = fila
    if nueva_col < 0 or nueva_col >= COLUMNAS:
        nueva_col = col

    nuevo = (nueva_fila, nueva_col)

    if nuevo in ACANTILADO:
        # Me cai: -100 y regreso a S. El episodio NO termina.
        return INICIO, -100, False
    if nuevo == META:
        # Llegue: -1 y se acaba el episodio.
        return META, -1, True
    # Paso normal (incluye chocar con el borde)
    return nuevo, -1, False


# ---------------------------------------------------------------
# 2) LA TABLA Q
# ---------------------------------------------------------------
def tabla_q_vacia():
    """Q[estado][accion] = 0 para todo estado que no sea la meta."""
    Q = {}
    for fila in range(FILAS):
        for col in range(COLUMNAS):
            estado = (fila, col)
            if estado == META:
                continue          # la meta es terminal: no lleva fila en Q
            Q[estado] = {}
            for a in ACCIONES:
                Q[estado][a] = 0.0
    return Q


def mejor_accion(Q, estado):
    """La accion con mayor Q. En empate gana la primera de N, E, S, W."""
    mejor = ACCIONES[0]
    for a in ACCIONES[1:]:
        if Q[estado][a] > Q[estado][mejor]:   # '>' estricto: no cambia en empate
            mejor = a
    return mejor


def elegir_accion(Q, estado, epsilon, rng):
    """epsilon-greedy: con prob. epsilon al azar; si no, la mejor."""
    if rng.random() < epsilon:
        return rng.choice(ACCIONES)
    return mejor_accion(Q, estado)


# ---------------------------------------------------------------
# 3) ENTRENAR CON Q-LEARNING
# ---------------------------------------------------------------
def entrenar(episodios, alpha, gamma, epsilon, semilla, tope_pasos=200):
    rng = random.Random(semilla)
    Q = tabla_q_vacia()
    recompensa_por_episodio = []

    for _ in range(episodios):
        s = INICIO
        total = 0                       # lo que junto en este episodio

        for _paso in range(tope_pasos):
            a = elegir_accion(Q, s, epsilon, rng)       # lo que HAGO
            s_sig, r, termino = dar_un_paso(s, a)
            total += r

            # Lo que "espero" del futuro: el maximo de Q en s_sig.
            # Si llegue a la meta, ya no hay futuro -> 0.
            # Si me cai, s_sig es S, que es un estado normal -> max Q(S, .)
            if termino:
                futuro = 0.0
            else:
                futuro = max(Q[s_sig].values())

            objetivo = r + gamma * futuro
            error = objetivo - Q[s][a]
            Q[s][a] = Q[s][a] + alpha * error      # el backup de Q-learning

            s = s_sig
            if termino:
                break

        recompensa_por_episodio.append(total)

    return Q, recompensa_por_episodio


# ---------------------------------------------------------------
# 4) EVALUAR LA POLITICA GREEDY (epsilon = 0)
# ---------------------------------------------------------------
def recorrer_greedy(Q, tope_pasos=200):
    s = INICIO
    camino = [s]
    acciones = []
    total = 0
    for _ in range(tope_pasos):
        a = mejor_accion(Q, s)
        s, r, termino = dar_un_paso(s, a)
        acciones.append(a)
        camino.append(s)
        total += r
        if termino:
            break
    return camino, acciones, total


def dibujar_politica(Q, camino):
    """Flechas en cada casilla; en mayuscula/negrita mental las del camino."""
    flecha = {"N": "^", "E": ">", "S": "v", "W": "<"}
    lineas = []
    for fila in range(FILAS):
        celdas = []
        for col in range(COLUMNAS):
            e = (fila, col)
            if e == INICIO:
                celdas.append("S")
            elif e == META:
                celdas.append("G")
            elif e in ACANTILADO:
                celdas.append("C")
            else:
                celdas.append(flecha[mejor_accion(Q, e)])
        lineas.append(" ".join(celdas))
    return "\n".join(lineas)


def media_movil(datos, ventana=10):
    salida = []
    for i in range(len(datos)):
        ini = max(0, i - ventana + 1)
        trozo = datos[ini:i + 1]
        salida.append(sum(trozo) / len(trozo))
    return salida


# ---------------------------------------------------------------
# 5) CORRER TODO
# ---------------------------------------------------------------
if __name__ == "__main__":
    SEMILLA = 0
    ALPHA, GAMMA, EPSILON, EPISODIOS = 0.5, 1.0, 0.1, 500

    # Las tres comprobaciones a mano que pide el enunciado
    assert dar_un_paso(INICIO, "N") == ((2, 0), -1, False)
    assert dar_un_paso(INICIO, "E") == (INICIO, -100, False)
    assert dar_un_paso((2, 11), "S") == (META, -1, True)

    Q, recompensas = entrenar(EPISODIOS, ALPHA, GAMMA, EPSILON, SEMILLA)
    camino, acciones, retorno = recorrer_greedy(Q)

    print("Semilla:", SEMILLA)
    print("Politica greedy:")
    print(dibujar_politica(Q, camino))
    print("Acciones desde S:", " ".join(acciones))
    print("Pasos:", len(acciones), " Retorno greedy:", retorno)

    # Guardar la serie para la grafica / tabla
    with open("recompensas.csv", "w") as f:
        f.write("episodio,recompensa,media_movil_10\n")
        mm = media_movil(recompensas, 10)
        for i, (r, m) in enumerate(zip(recompensas, mm), start=1):
            f.write(f"{i},{r},{m:.2f}\n")
