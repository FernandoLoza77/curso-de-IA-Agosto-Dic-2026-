"""Ejercicio 02: A* en el grafo de México (solo biblioteca estándar).

Adaptado de Búsqueda informada/project/search/astar.py del curso
https://github.com/victoruccetina/inteligencia-artificial
Se conservan f=g+h, mejor g, cola con desempate por inserción y padres.
Los estados son ids; se omiten entradas antiguas y se permiten mejoras.
"""
import argparse
import heapq
import json
import math
from pathlib import Path

DATA = Path(__file__).with_name("mexico_cities_graph.json")
EARTH_KM = 6371.0


def haversine(a, b):
    """Misma fórmula y radio que generate_mexico_graph.py del profesor."""
    p1, p2 = math.radians(a["lat"]), math.radians(b["lat"])
    dp = p2 - p1
    dl = math.radians(b["lon"] - a["lon"])
    v = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * EARTH_KM * math.asin(math.sqrt(min(1.0, v)))


def load_graph(path=DATA):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    nodes = {n["id"]: n for n in data["nodes"]}
    adj = {i: [] for i in nodes}
    scale = 1.0
    for e in data["edges"]:
        a, b, km = e["source"], e["target"], e["km"]
        adj[a].append((b, km))
        adj[b].append((a, km))
        distance = haversine(nodes[a], nodes[b])
        if distance:
            scale = min(scale, km / distance)
    # Los pesos originales se redondean a 0.01 km. Este factor asegura
    # scale * haversine(u,v) <= peso(u,v) sin modificar ninguna arista.
    scale *= 1 - 1e-12
    for neighbors in adj.values():
        neighbors.sort()
    return data, nodes, adj, scale


def resolve_city(value, nodes, state=None):
    if value.isdecimal():
        node = nodes.get(int(value))
        matches = [node] if node and (state is None or node["state"] == state) else []
    else:
        matches = [n for n in nodes.values() if n["name"].casefold() == value.casefold()
                   and (state is None or n["state"].casefold() == state.casefold())]
    if not matches:
        raise ValueError(f"No se encontró: {value!r}. Usa el nombre exacto del JSON o su id.")
    if len(matches) > 1:
        options = "; ".join(f'{n["name"]}, {n["state"]}, id={n["id"]}' for n in matches)
        raise ValueError("Nombre ambiguo. Indica el id o --from-state/--to-state: " + options)
    return matches[0]["id"]


def search(nodes, adj, start, goal, scale, algorithm="astar"):
    def h(node):
        return 0.0 if algorithm == "ucs" else scale * haversine(nodes[node], nodes[goal])

    frontier = [(h(start), 0, 0.0, start)]
    best = {start: 0.0}
    parent = {start: None}
    counter = 0
    expanded = 0
    generated = 1
    maximum = 1
    while frontier:
        _, _, g, u = heapq.heappop(frontier)
        if g > best[u] + 1e-9:
            continue
        if u == goal:
            route = []
            current = goal
            while current is not None:
                route.append(current)
                current = parent[current]
            route.reverse()
            return {"status": "success", "path": route, "depth": len(route)-1,
                    "cost": g, "expanded": expanded, "generated": generated,
                    "max_frontier": maximum, "scale": scale, "algorithm": algorithm}
        expanded += 1
        for v, cost in adj[u]:
            generated += 1
            candidate = g + cost
            if candidate + 1e-9 < best.get(v, math.inf):
                best[v] = candidate
                parent[v] = u
                counter += 1
                heapq.heappush(frontier, (candidate + h(v), counter, candidate, v))
                maximum = max(maximum, len(frontier))
    return {"status": "failure", "path": [], "depth": None, "cost": None,
            "expanded": expanded, "generated": generated, "max_frontier": maximum,
            "scale": scale, "algorithm": algorithm}


def city_label(node):
    return f'{node["name"]} ({node["state"]}; id={node["id"]})'


def main():
    parser = argparse.ArgumentParser(description="Ruta mínima en el grafo de México.")
    parser.add_argument("--from-city", required=True, help="Nombre exacto o id.")
    parser.add_argument("--to", required=True, help="Nombre exacto o id.")
    parser.add_argument("--from-state")
    parser.add_argument("--to-state")
    parser.add_argument("--algorithm", choices=("astar", "ucs"), default="astar")
    parser.add_argument("--json", action="store_true", help="Salida estructurada para verificar.")
    args = parser.parse_args()
    _, nodes, adj, scale = load_graph()
    try:
        start = resolve_city(args.from_city, nodes, args.from_state)
        goal = resolve_city(args.to, nodes, args.to_state)
    except ValueError as exc:
        parser.error(str(exc))
    result = search(nodes, adj, start, goal, scale, args.algorithm)
    if args.json:
        print(json.dumps(result, ensure_ascii=False))
        return
    print("Algorithm: A*" if args.algorithm == "astar" else "Algorithm: UCS")
    print("From:     ", city_label(nodes[start]))
    print("To:       ", city_label(nodes[goal]))
    print("Heuristic:", f"haversine al destino x {scale:.12f} (ajuste por redondeo)"
          if args.algorithm == "astar" else "h=0")
    print("Status:   ", result["status"])
    if result["status"] == "success":
        print("Path:     ", " -> ".join(f'{nodes[i]["name"]}[{i}]' for i in result["path"]))
        print("Depth:    ", result["depth"], "hops")
        print("Cost:     ", f'{result["cost"]:.2f}', "km")
    print("Expanded: ", result["expanded"])
    print("Generated:", result["generated"])
    print("Frontier: ", result["max_frontier"], "(max)")


if __name__ == "__main__":
    main()

