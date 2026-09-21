/* Ejercicio 02. Adaptación para el navegador de A* del curso:
   Búsqueda informada/project/search/astar.py.
   Usa los datos G y la proyección SVG del mapa original; no regenera el grafo. */
(() => {
  "use strict";
  const nodes = new Map(G.nodes.map(n => [n.id, n]));
  const adjacency = new Map(G.nodes.map(n => [n.id, []]));
  function haversine(a, b) {
    const rad = Math.PI / 180;
    const p1 = a.lat * rad, p2 = b.lat * rad;
    const v = Math.sin((p2 - p1) / 2) ** 2 +
      Math.cos(p1) * Math.cos(p2) * Math.sin((b.lon-a.lon)*rad/2) ** 2;
    return 2 * 6371 * Math.asin(Math.sqrt(Math.min(1, v)));
  }
  let scale = 1;
  for (const e of G.edges) {
    adjacency.get(e.source).push([e.target, e.km]);
    adjacency.get(e.target).push([e.source, e.km]);
    const d = haversine(nodes.get(e.source), nodes.get(e.target));
    if (d) scale = Math.min(scale, e.km/d);
  }
  scale *= 1-1e-12;
  for (const list of adjacency.values()) list.sort((a,b) => a[0]-b[0]);

  function search(start, goal) {
    if (!nodes.has(start) || !nodes.has(goal)) throw new Error("Selecciona origen y destino.");
    const h = id => scale * haversine(nodes.get(id), nodes.get(goal));
    const frontier = [{id:start,g:0,f:h(start),order:0}];
    const best = new Map([[start,0]]);
    const parents = new Map([[start,null]]);
    let order=0, expanded=0, generated=1, maxFrontier=1;
    while (frontier.length) {
      frontier.sort((a,b) => (a.f-b.f) || (a.order-b.order));
      const node = frontier.shift();
      if (node.g > best.get(node.id)+1e-9) continue;
      if (node.id === goal) {
        const path=[];
        for (let id=goal; id!==null; id=parents.get(id)) path.push(id);
        path.reverse();
        return {status:"success",path,cost:node.g,depth:path.length-1,
          expanded,generated,max_frontier:maxFrontier,scale};
      }
      expanded++;
      for (const [id, km] of adjacency.get(node.id)) {
        generated++;
        const candidate = node.g+km;
        if (candidate+1e-9 < (best.get(id) ?? Infinity)) {
          best.set(id,candidate);
          parents.set(id,node.id);
          frontier.push({id,g:candidate,f:candidate+h(id),order:++order});
          maxFrontier=Math.max(maxFrontier,frontier.length);
        }
      }
    }
    return {status:"failure",path:[],cost:null,depth:null,expanded,generated};
  }

  const form=document.getElementById("route-form");
  const from=document.getElementById("route-from");
  const to=document.getElementById("route-to");
  const output=document.getElementById("route-result");
  const pathText=document.getElementById("route-path");
  const routeLayer=document.createElementNS(NS,"g");
  routeLayer.id="route-layer";
  routeLayer.setAttribute("pointer-events","none");
  world.appendChild(routeLayer);
  const label=n => n.name+" ("+n.state+") [id="+n.id+"]";
  const ordered=[...nodes.values()].sort((a,b) =>
    a.name.localeCompare(b.name,"es") || a.id-b.id);
  for (const select of [from,to]) {
    for (const n of ordered) {
      const option=document.createElement("option");
      option.value=n.id;
      option.textContent=label(n);
      select.appendChild(option);
    }
  }
  function element(tag,attrs) {
    const el=document.createElementNS(NS,tag);
    for (const [key,value] of Object.entries(attrs)) el.setAttribute(key,value);
    routeLayer.appendChild(el);
    return el;
  }
  function paint(result) {
    routeLayer.replaceChildren();
    if (result.status!=="success") return;
    const points=result.path.map(id => {
      const n=nodes.get(id);
      return project(n.lon,n.lat).join(",");
    }).join(" ");
    element("polyline",{points,fill:"none",stroke:"white","stroke-width":6,
      "stroke-linejoin":"round","stroke-linecap":"round"});
    element("polyline",{points,fill:"none",stroke:"#111","stroke-width":2.6,
      "stroke-linejoin":"round","stroke-linecap":"round"});
    for (const id of result.path) {
      const n=nodes.get(id), [cx,cy]=project(n.lon,n.lat);
      element("circle",{cx,cy,r:2.4,fill:"#111",stroke:"white","stroke-width":.7});
    }
    const ends=result.path.length===1?[result.path[0]]:[result.path[0],result.path.at(-1)];
    for (const [i,id] of ends.entries()) {
      const n=nodes.get(id),[cx,cy]=project(n.lon,n.lat);
      element("circle",{cx,cy,r:6,fill:"white",stroke:"#111","stroke-width":2});
      const right=cx>W-230;
      const text=element("text",{x:cx+(right?-10:10),y:cy-12,
        "text-anchor":right?"end":"start","font-size":13,"font-family":"Arial",
        "font-weight":"bold",fill:"#111",stroke:"white","stroke-width":3,
        "paint-order":"stroke"});
      text.textContent=(result.depth===0?"Inicio y destino: ":i?"Destino: ":"Inicio: ")+n.name;
    }
  }
  function clear() {
    routeLayer.replaceChildren();
    output.textContent="";
    pathText.textContent="";
    window.mxRoutes.result=null;
  }
  function calculate(event) {
    if (event) event.preventDefault();
    clear();
    try {
      if (from.value==="" || to.value==="") throw new Error("Selecciona ambas ciudades.");
      const result=search(Number(from.value),Number(to.value));
      window.mxRoutes.result=result;
      if (result.status!=="success") {
        output.textContent="No se encontró un camino.";
        return;
      }
      output.textContent="Status: success | Costo: "+result.cost.toFixed(2)+
        " km | Saltos: "+result.depth+" | Expandidos: "+result.expanded;
      pathText.textContent=result.path.map(id=>label(nodes.get(id))).join(" -> ");
      document.getElementById("q").value="";
      stateSel.value="";
      applyFilter();
      panX=0;panY=0;zoom=1;applyView();
      paint(result);
    } catch(error) {
      output.textContent=error.message;
    }
  }
  window.mxRoutes={search,calculate,clear,scale,result:null};
  form.addEventListener("submit",calculate);
  document.getElementById("route-clear").addEventListener("click",clear);
  from.addEventListener("change",clear);
  to.addEventListener("change",clear);
  from.value="6";to.value="25";
  document.getElementById("labels").checked=false;
  labelLayer.style.display="none";
  document.getElementById("route-heuristic").textContent=
    "A*: f=g+h. h=haversine al destino x "+scale.toFixed(9)+
    ". Ajuste por redondeo de los pesos originales.";
})();
