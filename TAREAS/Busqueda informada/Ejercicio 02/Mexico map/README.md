# Ejercicio 02: rutas con A* en México

## Archivos
- `find_route.py`: A* en Python, con ids, costos, padres y cola de prioridad.
- `mexico_map.html` y `route.js`: mapa del profesor con controles para calcular rutas.
- `mexico_cities_graph.json`: copia exacta del grafo original, sin cambiar nodos ni aristas.
- `verificar.py`: comprobaciones contra Dijkstra independiente.

## Ejecutar en PowerShell
Desde esta carpeta:
```powershell
python find_route.py --from-city Tijuana --to Cancún
python find_route.py --from-city "Mexico City" --to Monterrey
python find_route.py --from-city Tijuana --to Cancún --algorithm ucs
python verificar.py
```
Python 3.10 o posterior. Solo se usa la biblioteca estándar, sin instalar paquetes.

## Usar el mapa
Abre `mexico_map.html` con Edge o Chrome. Selecciona origen y destino y pulsa
**Calcular ruta**. La línea negra muestra todas las aristas del camino.
El panel indica kilómetros, saltos y nodos expandidos; **Ver camino completo**
muestra todos los ids. **Limpiar** quita el resultado. Mantén el HTML y el JS
juntos. Funciona localmente sin conexión.

Cada opción muestra ciudad, estado e id, incluso si se repite el nombre.

## Nombres duplicados en la terminal
Si escribes `Puebla`, el programa detiene la consulta y lista las opciones.
Indica estado o usa el id:
```powershell
python find_route.py --from-city Puebla --from-state "Baja California" --to Cancún
python find_route.py --from-city 580 --to 25
```
No se selecciona una ciudad al azar.

## Heurística y redondeo
Se adapta A* de `Búsqueda informada/project/search/astar.py` del profesor:
prioridad f=g+h, mejor costo por estado y reconstrucción por padres.
Se permiten mejoras y se descartan entradas antiguas.

La fórmula haversine usa el radio 6371 km del generador. Los pesos del JSON
están redondeados a dos decimales. Para que h no sobreestime por redondeo,
se calcula una vez alpha = min(1, min(peso(u,v)/haversine(u,v))),
con un pequeño margen numérico. Se usa h(n)=alpha*haversine(n,destino),
con alpha aproximadamente 0.998517792300. No es h=0: sigue siendo A* informado.

Por desigualdad triangular, alpha*d(n,meta) <= alpha*d(n,vecino) +
alpha*d(vecino,meta). Como alpha*d(n,vecino) <= peso(n,vecino),
h es consistente y admisible. El costo siempre suma los km originales.
Python y el navegador utilizan la misma heurística y reglas de orden.

## Procedencia
Código y mapa base: https://github.com/victoruccetina/inteligencia-artificial
Datos: GeoNames cities1000, CC BY 3.0.
https://www.geonames.org/
https://creativecommons.org/licenses/by/3.0/

Esta es una copia para entregar dentro de TAREAS. No ejecutes el generador
sobre ella: reemplazaría el HTML con los controles. El grafo es de proximidad;
sus aristas no necesariamente son carreteras reales.
