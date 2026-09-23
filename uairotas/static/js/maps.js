(() => {
  const mapElements = [...document.querySelectorAll("[data-mapbox-map]")];
  if (!mapElements.length) return;

  const accessToken = document.querySelector('meta[name="mapbox-access-token"]')?.content.trim();

  const showMessage = (element, message) => {
    const shell = element.closest(".mapbox-map-shell");
    const messageBox = shell?.querySelector("[data-mapbox-map-message]");
    if (!messageBox) return;
    messageBox.textContent = message;
    messageBox.hidden = false;
    element.setAttribute("aria-hidden", "true");
  };

  const readPayload = (element) => {
    const source = document.getElementById(element.dataset.mapSource);
    if (!source) throw new Error("Dados do mapa não encontrados.");
    return JSON.parse(source.textContent);
  };

  const coordinates = (item) => [item.lng, item.lat];
  const styleForTheme = () => document.body.dataset.theme === "dark"
    ? "mapbox://styles/mapbox/dark-v11"
    : "mapbox://styles/mapbox/streets-v12";

  const popupContent = (title, detail) => {
    const content = document.createElement("div");
    content.className = "map-info";
    const heading = document.createElement("strong");
    const description = document.createElement("span");
    heading.textContent = title;
    description.textContent = detail;
    content.append(heading, description);
    return content;
  };

  const addMarker = (map, item, type, label, color, title, detail) => {
    const markerElement = document.createElement("button");
    markerElement.type = "button";
    markerElement.className = `mapbox-marker mapbox-marker--${type}`;
    markerElement.style.setProperty("--marker-color", color);
    markerElement.textContent = label;
    markerElement.setAttribute("aria-label", `${title}: ${detail}`);

    return new mapboxgl.Marker({ element: markerElement, anchor: "center" })
      .setLngLat(coordinates(item))
      .setPopup(new mapboxgl.Popup({ offset: 18 }).setDOMContent(popupContent(title, detail)))
      .addTo(map);
  };

  const directionsGeometry = async (route) => {
    const waypoints = route.path.map((point) => coordinates(point).join(",")).join(";");
    const parameters = new URLSearchParams({
      access_token: accessToken,
      geometries: "geojson",
      overview: "full",
      steps: "false",
    });
    const endpoint = `https://api.mapbox.com/directions/v5/mapbox/driving/${waypoints}?${parameters}`;
    const response = await fetch(endpoint);
    if (!response.ok) throw new Error(`Directions API respondeu ${response.status}.`);
    const result = await response.json();
    const match = result.routes?.[0];
    if (!match?.geometry) throw new Error("A Directions API não retornou uma rota.");
    return {
      geometry: match.geometry,
      distanceKm: match.distance / 1000,
      durationMinutes: Math.round(match.duration / 60),
    };
  };

  const buildMap = (element) => {
    const payload = readPayload(element);
    const selectedRoute = element.dataset.selectedRoute || "todos";
    mapboxgl.accessToken = accessToken;

    const map = new mapboxgl.Map({
      container: element,
      style: styleForTheme(),
      center: coordinates(payload.center),
      zoom: payload.zoom || 13,
      locale: {
        "NavigationControl.ZoomIn": "Ampliar",
        "NavigationControl.ZoomOut": "Reduzir",
        "NavigationControl.ResetBearing": "Redefinir orientação",
        "FullscreenControl.Enter": "Tela cheia",
        "FullscreenControl.Exit": "Sair da tela cheia",
      },
    });

    map.addControl(new mapboxgl.NavigationControl({ showCompass: true }), "top-right");
    map.addControl(new mapboxgl.FullscreenControl(), "top-right");

    const boundsByRoute = new Map();
    const routeMetrics = new Map();
    const registeredRouteEvents = new Set();
    const allBounds = new mapboxgl.LngLatBounds();
    let focusedRoute = selectedRoute;

    payload.routes.forEach((route) => {
      const routeBounds = new mapboxgl.LngLatBounds();
      route.path.forEach((point) => {
        routeBounds.extend(coordinates(point));
        allBounds.extend(coordinates(point));
      });
      boundsByRoute.set(route.id, routeBounds);
    });

    const lineOpacity = (routeId) => focusedRoute === "todos" || focusedRoute === routeId ? 0.92 : 0.16;
    const lineWidth = (routeId) => focusedRoute === routeId ? 7 : 5;

    const addRouteLayers = () => {
      payload.routes.forEach((route) => {
        const sourceId = `route-source-${route.id}`;
        const layerId = `route-layer-${route.id}`;
        if (map.getSource(sourceId)) return;
        map.addSource(sourceId, {
          type: "geojson",
          data: {
            type: "Feature",
            properties: { id: route.id, name: route.name },
            geometry: { type: "LineString", coordinates: route.path.map(coordinates) },
          },
        });
        map.addLayer({
          id: layerId,
          type: "line",
          source: sourceId,
          layout: { "line-cap": "round", "line-join": "round" },
          paint: {
            "line-color": route.color,
            "line-opacity": lineOpacity(route.id),
            "line-width": lineWidth(route.id),
          },
        });

        if (!registeredRouteEvents.has(route.id)) {
          map.on("mouseenter", layerId, () => { map.getCanvas().style.cursor = "pointer"; });
          map.on("mouseleave", layerId, () => { map.getCanvas().style.cursor = ""; });
          map.on("click", layerId, (event) => {
            const metrics = routeMetrics.get(route.id);
            const detail = metrics
              ? `${metrics.distanceKm.toFixed(1).replace(".", ",")} km · cerca de ${metrics.durationMinutes} min`
              : "Trajeto planejado";
            new mapboxgl.Popup({ offset: 8 })
              .setLngLat(event.lngLat)
              .setDOMContent(popupContent(route.name, detail))
              .addTo(map);
          });
          registeredRouteEvents.add(route.id);
        }
      });
    };

    const alignRoutesToRoads = async () => {
      const results = await Promise.allSettled(payload.routes.map(async (route) => {
        const matched = await directionsGeometry(route);
        routeMetrics.set(route.id, matched);
        const source = map.getSource(`route-source-${route.id}`);
        if (source) {
          source.setData({
            type: "Feature",
            properties: { id: route.id, name: route.name },
            geometry: matched.geometry,
          });
        }
      }));
      element.dataset.routeApiStatus = results.every((result) => result.status === "fulfilled")
        ? "ready"
        : "fallback";
    };

    const focusRoute = (routeId) => {
      focusedRoute = routeId;
      payload.routes.forEach((route) => {
        const layerId = `route-layer-${route.id}`;
        if (!map.getLayer(layerId)) return;
        map.setPaintProperty(layerId, "line-opacity", lineOpacity(route.id));
        map.setPaintProperty(layerId, "line-width", lineWidth(route.id));
      });
      const bounds = boundsByRoute.get(routeId);
      if (bounds) map.fitBounds(bounds, { padding: 70, maxZoom: 15 });
    };

    map.on("load", () => {
      addRouteLayers();
      alignRoutesToRoads();
      if (selectedRoute !== "todos") focusRoute(selectedRoute);
      else if (!allBounds.isEmpty()) map.fitBounds(allBounds, { padding: 55, maxZoom: 14 });

      payload.vehicles.forEach((vehicle) => {
        const route = payload.routes.find((item) => item.id === vehicle.routeId);
        addMarker(
          map, vehicle, vehicle.alert ? "alert" : "vehicle", "🚗",
          vehicle.alert ? "#b4122d" : route?.color || "#d9233f",
          vehicle.name, vehicle.status,
        );
      });

      payload.orders.forEach((order) => addMarker(
        map, order, "order", order.label, "#5d1830", order.code, "Ordem de serviço",
      ));

      payload.places.forEach((place) => addMarker(
        map, place, "place", "◆", "#f2b622", place.name, place.kind,
      ));
    });

    map.on("style.load", addRouteLayers);
    map.on("error", (event) => {
      if (event?.error?.status === 401 || event?.error?.status === 403) {
        showMessage(element, "O Mapbox recusou o token. Verifique o token público e as URLs permitidas.");
      }
    });

    document.querySelectorAll("[data-focus-route]").forEach((button) => {
      button.addEventListener("click", () => focusRoute(button.dataset.focusRoute));
    });

    let currentStyle = styleForTheme();
    new MutationObserver(() => {
      const nextStyle = styleForTheme();
      if (nextStyle !== currentStyle) {
        currentStyle = nextStyle;
        map.setStyle(nextStyle);
      }
    }).observe(document.body, { attributes: true, attributeFilter: ["data-theme"] });
  };

  if (!window.mapboxgl) {
    mapElements.forEach((element) => showMessage(
      element, "A biblioteca do Mapbox não pôde ser carregada. Verifique a conexão.",
    ));
    return;
  }

  if (!accessToken || accessToken === "insira_seu_token_publico_restrito_aqui") {
    mapElements.forEach((element) => showMessage(
      element, "Configure MAPBOX_ACCESS_TOKEN no arquivo .env para exibir o mapa.",
    ));
    return;
  }

  mapElements.forEach((element) => {
    try {
      buildMap(element);
    } catch (error) {
      showMessage(element, "Não foi possível carregar os dados do mapa.");
    }
  });
})();
