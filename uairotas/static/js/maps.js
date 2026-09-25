(() => {
  "use strict";
  const container = document.getElementById("operational-map");
  if (!container) return;
  const status = document.querySelector("[data-map-status]");
  const retry = document.querySelector("[data-map-retry]");
  const data = JSON.parse(document.getElementById("operational-map-data").textContent);
  const token = document.querySelector('meta[name="mapbox-access-token"]')?.content || "";
  function message(text, canRetry = false) { status.textContent = text; retry.hidden = !canRetry; }
  if (!window.mapboxgl || !token.startsWith("pk.") || !mapboxgl.supported()) {
    message(!token.startsWith("pk.") ? "Configure o token público do Mapbox para carregar o mapa. As ordens continuam disponíveis na lista." :
      "O mapa não carregou ou o navegador não disponibilizou WebGL. As ordens continuam disponíveis na lista.", true);
    retry.addEventListener("click", () => window.location.reload()); return;
  }
  const reduced = () => window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const style = () => document.documentElement.dataset.theme === "dark" ? "mapbox://styles/mapbox/dark-v11" : "mapbox://styles/mapbox/streets-v12";
  mapboxgl.accessToken = token;
  const store = UaiRotas.routeStore(data.routes), cache = new Map(), controllers = new Set(), markers = [];
  const registeredLayers = new Set();
  let focused = null, loaded = false, aligning = false;
  let map;
  try {
    map = new mapboxgl.Map({ container, style:style(), center:[data.center.lng, data.center.lat], zoom:data.zoom,
      attributionControl:true, locale:{ "NavigationControl.ZoomIn":"Ampliar", "NavigationControl.ZoomOut":"Reduzir",
        "NavigationControl.ResetBearing":"Orientar para o norte", "FullscreenControl.Enter":"Tela cheia", "FullscreenControl.Exit":"Sair da tela cheia" } });
  } catch (_) {
    message("Não foi possível iniciar o mapa. Confira a conexão e a disponibilidade de WebGL.", true);
    retry.addEventListener("click", () => window.location.reload()); return;
  }
  map.addControl(new mapboxgl.NavigationControl(), "top-right");
  map.addControl(new mapboxgl.FullscreenControl(), "top-right");
  function popup(title, lines) {
    const wrapper = document.createElement("div"), heading = document.createElement("strong");
    heading.textContent = title; wrapper.appendChild(heading);
    for (const line of lines) { const p = document.createElement("p"); p.textContent = line; wrapper.appendChild(p); }
    return new mapboxgl.Popup({ offset:24, maxWidth:"320px" }).setDOMContent(wrapper);
  }
  function applyLayers() {
    if (!map.isStyleLoaded()) return;
    for (const route of data.routes) {
      const id = "route-" + route.id, feature = store.feature(route.id);
      if (!feature) continue;
      if (map.getSource(id)) map.getSource(id).setData(feature);
      else map.addSource(id, { type:"geojson", data:feature });
      if (!map.getLayer(id)) map.addLayer({ id, type:"line", source:id,
        layout:{ "line-join":"round", "line-cap":"round" },
        paint:{ "line-color":route.color, "line-width":5, "line-opacity":.86 } });
      map.setLayoutProperty(id, "visibility", focused && String(route.id) !== focused ? "none" : "visible");
      if (!registeredLayers.has(id)) {
        map.on("click", id, event => popup(route.name, [
          route.path_kind === "recorded" ? "Trajeto registrado" : store.get(route.id)?.matched ? "Rota planejada pela malha viária" : "Ligação aproximada entre pontos",
          "Data: " + data.date, route.demo ? "Dados demonstrativos" : "Dados cadastrados"
        ]).setLngLat(event.lngLat).addTo(map));
        registeredLayers.add(id);
      }
    }
  }
  function boundsFor(routes) {
    const bounds = new mapboxgl.LngLatBounds(); let count = 0;
    for (const route of routes) for (const point of store.get(route.id)?.geometry.coordinates || []) { bounds.extend(point); count++; }
    return count ? bounds : null;
  }
  function focusRoute(id, scroll = false) {
    focused = id === null ? null : String(id); applyLayers();
    for (const entry of markers) entry.element.hidden = !!(focused && entry.routeId && entry.routeId !== focused);
    document.querySelectorAll("[data-route-focus]").forEach(button => button.setAttribute("aria-pressed", String(button.dataset.routeFocus === focused)));
    const bounds = boundsFor(focused ? data.routes.filter(r => String(r.id) === focused) : data.routes);
    if (bounds && loaded) map.fitBounds(bounds, { padding:55, maxZoom:15, duration:reduced() ? 0 : 500 });
    if (scroll && window.innerWidth < 900) container.scrollIntoView({ behavior:reduced() ? "auto" : "smooth", block:"center" });
  }
  const icons = {
    office:'<path d="M4 21V3h16v18M1 21h22M8 7h2m4 0h2M8 11h2m4 0h2M10 21v-6h4v6"/>',
    warehouse:'<path d="M2 9 12 3l10 6v12H2ZM6 21V11h12v10M6 15h12M6 18h12"/>',
    restaurant:'<path d="M5 3v7m3-7v7m3-7v7M5 7h6M8 10v11M18 3v18m0-18c-4 3-4 9 0 9"/>',
    fuel:'<path d="M3 21V4h11v17M2 21h14M5 7h7v5H5ZM14 9h3v8a2 2 0 0 0 4 0V9l-4-4"/>',
    car:'<path d="m4 9 2-5h12l2 5M3 9h18v9H3ZM6 18v3m12-3v3M6 13h2m8 0h2"/>'
  };
  function marker(point, title, lines, routeId, color, icon, label, alert = false) {
    const element = document.createElement("button");
    element.type = "button"; element.className = "map-marker" + (icon && icon !== "car" ? " map-poi" : "");
    element.setAttribute("aria-label", title); element.style.setProperty("--marker-color", color || "#681027");
    const inner = document.createElement("span"); inner.className = "map-marker-inner" + (alert ? " map-alert-ring" : "");
    if (icon) {
      const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
      svg.setAttribute("viewBox", "0 0 24 24"); svg.setAttribute("aria-hidden", "true");
      // Icons are fixed local constants; no API content is interpreted as HTML.
      svg.innerHTML = icons[icon] || icons.office; inner.appendChild(svg);
    } else inner.textContent = label;
    element.appendChild(inner);
    const m = new mapboxgl.Marker({ element }).setLngLat(point).setPopup(popup(title, lines)).addTo(map);
    markers.push({ element, marker:m, routeId:routeId == null ? null : String(routeId) });
  }
  function addMarkers() {
    for (const route of data.routes) if (store.get(route.id)) {
      marker(route.points[0], route.name, [route.path_kind === "recorded" ? "Início do trajeto registrado" : "Início da rota planejada", "Não é uma posição em tempo real."],
        route.id, route.color, "car");
    }
    for (const order of data.orders) marker([order.lng, order.lat], order.code + " · " + order.customer,
      [order.address, order.service, order.status], order.route_id, "#681027", null, order.label, order.status === "Atrasada");
    for (const place of data.places) marker([place.lng, place.lat], place.name, [place.address, "Local de interesse"],
      null, null, place.type in icons ? place.type : "office");
  }
  async function directions(route) {
    const key = JSON.stringify(route.points);
    if (cache.has(key)) return cache.get(key);
    const task = (async () => {
      if (route.points.length > 25) throw new Error("too_many_points");
      const controller = new AbortController(); controllers.add(controller);
      const timer = setTimeout(() => controller.abort(), 10000);
      try {
        const coordinates = route.points.map(p => p.join(",")).join(";");
        const url = "https://api.mapbox.com/directions/v5/mapbox/driving/" + coordinates +
          "?geometries=geojson&overview=full&access_token=" + encodeURIComponent(token);
        const response = await fetch(url, { signal:controller.signal });
        if (!response.ok) throw new Error("directions");
        const body = await response.json(), geometry = body.routes?.[0]?.geometry;
        if (!store.set(route.id, geometry)) throw new Error("geometry");
        return geometry;
      } finally { clearTimeout(timer); controllers.delete(controller); }
    })();
    cache.set(key, task);
    try { return await task; } catch (error) { cache.delete(key); throw error; }
  }
  async function alignRoutes() {
    if (aligning) return;
    aligning = true; retry.disabled = true;
    const pending = data.routes.filter(r => store.get(r.id) && !store.get(r.id).matched);
    if (pending.length) message("Calculando rotas planejadas…");
    await Promise.allSettled(pending.map(async route => { const geometry = await directions(route); store.set(route.id, geometry); applyLayers(); }));
    const fallback = data.routes.filter(r => store.get(r.id) && !store.get(r.id).matched).length;
    message(fallback ? fallback + " rota(s) com ligação aproximada entre pontos. Não foi possível calcular todas as vias." :
      data.routes.length ? "Mapa pronto. Rotas planejadas identificadas por colaborador." : "Nenhuma rota nos filtros selecionados.", fallback > 0);
    retry.disabled = false; aligning = false; focusRoute(focused);
  }
  const loadingTimer = setTimeout(() => { if (!loaded) message("O mapa demorou a carregar. Confira a conexão e tente novamente.", true); }, 15000);
  map.on("style.load", applyLayers);
  map.on("load", () => { loaded = true; clearTimeout(loadingTimer); addMarkers(); applyLayers(); focusRoute(null); alignRoutes(); });
  map.on("error", event => {
    if ([401,403].includes(event.error?.status)) message("O Mapbox recusou o acesso. Confira o token e os domínios autorizados.", true);
  });
  window.addEventListener("uairotas:theme", () => { map.setStyle(style()); });
  document.querySelectorAll("[data-route-focus]").forEach(button => button.addEventListener("click", () => focusRoute(button.dataset.routeFocus, true)));
  document.querySelector("[data-map-reset]").addEventListener("click", () => focusRoute(null));
  retry.addEventListener("click", () => { if (!loaded) window.location.reload(); else alignRoutes(); });
  let observer;
  if (typeof ResizeObserver !== "undefined") { observer = new ResizeObserver(() => map.resize()); observer.observe(container); }
  window.addEventListener("pagehide", () => { controllers.forEach(c => c.abort()); clearTimeout(loadingTimer); observer?.disconnect(); }, {once:true});
})();
