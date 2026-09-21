"""Verificación: A* contra Dijkstra independiente, sin paquetes externos."""
import heapq
import math
import random
from find_route import load_graph, resolve_city, search, haversine


def dijkstra(adj, start, goal):
    heap = [(0.0, start)]
    distances = {start: 0.0}
    while heap:
        cost, node = heapq.heappop(heap)
        if cost != distances[node]:
            continue
        if node == goal:
            return cost
        for nxt, km in adj[node]:
            new = cost + km
            if new < distances.get(nxt, math.inf):
                distances[nxt] = new
                heapq.heappush(heap, (new, nxt))
    return math.inf


def main():
    data, nodes, adj, scale = load_graph()
    assert len(nodes) == 1000 and len(data["edges"]) == 2565
    for e in data["edges"]:
        assert scale * haversine(nodes[e["source"]], nodes[e["target"]]) <= e["km"] + 1e-9
    generator = random.Random(42)
    pairs = [(6,25), (0,10), (0,0), (0,8), (4,580)]
    pairs += [tuple(generator.sample(list(nodes), 2)) for _ in range(30)]
    for start, goal in pairs:
        result = search(nodes, adj, start, goal, scale)
        assert result["status"] == "success"
        assert result["path"][0] == start and result["path"][-1] == goal
        assert result["depth"] == len(result["path"])-1
        cost = sum(dict(adj[a])[b] for a,b in zip(result["path"],result["path"][1:]))
        assert abs(cost-result["cost"]) < 1e-7
        assert abs(cost-dijkstra(adj,start,goal)) < 1e-7
    try:
        resolve_city("Puebla", nodes)
        raise AssertionError("Debió rechazar el nombre ambiguo")
    except ValueError as exc:
        assert "ambiguo" in str(exc)
    assert resolve_city("Puebla",nodes,"Baja California") == 580
    assert resolve_city("4",nodes) == 4
    try:
        resolve_city("Ciudad que no existe",nodes)
        raise AssertionError("Debió rechazar un nombre inexistente")
    except ValueError:
        pass
    print("OK: 35 parejas comparadas con Dijkstra independiente.")
    print("OK: costos, caminos, 2565 aristas, origen=destino y duplicados.")
    print(f"Factor de haversine: {scale:.12f}")


if __name__ == "__main__":
    main()

