/* Small state controllers, shared by browser code and Node regression tests. */
(function (root, factory) {
  const api = factory();
  if (typeof module === "object" && module.exports) module.exports = api;
  else root.UaiRotas = api;
})(typeof globalThis !== "undefined" ? globalThis : this, function () {
  "use strict";
  function safeStorage(provider) {
    const memory = new Map();
    return {
      get(key, fallback = null) {
        try { const value = provider().getItem(key); return value === null ? (memory.get(key) ?? fallback) : value; }
        catch (_) { return memory.get(key) ?? fallback; }
      },
      set(key, value) {
        memory.set(key, String(value));
        try { provider().setItem(key, String(value)); } catch (_) { /* Memory fallback keeps controls usable. */ }
      },
      json(key, fallback) {
        try { const value = this.get(key); return value === null ? fallback : JSON.parse(value); }
        catch (_) { return fallback; }
      }
    };
  }
  function routeStore(routes) {
    const data = new Map();
    const valid = geometry => geometry?.type === "LineString" && Array.isArray(geometry.coordinates) &&
      geometry.coordinates.length >= 2 && geometry.coordinates.every(p => Array.isArray(p) && p.length >= 2 &&
        Number.isFinite(p[0]) && Number.isFinite(p[1]) && Math.abs(p[0]) <= 180 && Math.abs(p[1]) <= 90);
    for (const route of routes) {
      const geometry = { type: "LineString", coordinates: route.points };
      if (valid(geometry)) data.set(String(route.id), { geometry, matched: route.path_kind === "recorded" });
    }
    return {
      get(id) { return data.get(String(id)); },
      set(id, geometry) { if (!valid(geometry)) return false; data.set(String(id), { geometry, matched:true }); return true; },
      feature(id) { const item = this.get(id); return item ? { type:"Feature", properties:{}, geometry:item.geometry } : null; }
    };
  }
  function alertPlayer({ audio, preferences, heardStorage, userId, update = () => {} }) {
    const prefKey = "uairotas-audio-v2:" + userId;
    const heardKey = "uairotas-heard-v2:" + userId;
    const raw = preferences.json(prefKey, {}) || {};
    let enabled = raw.enabled !== false, volume = Number.isFinite(raw.volume) ? Math.max(0, Math.min(1, raw.volume)) : .72;
    const categories = { routes:true, fleet:true, forms:true, ...(raw.categories || {}) };
    const heardData = heardStorage.json(heardKey, []);
    const heard = new Set(Array.isArray(heardData) ? heardData.filter(x => typeof x === "string").slice(-500) : []);
    const pending = new Map();
    let blocked = false, failed = false, playing = false, inFlight = false;
    const snapshot = () => ({ enabled, volume, categories:{...categories}, blocked, failed, playing,
      pending:[...pending.values()].filter(x => categories[x.category] !== false).length });
    const notify = () => update(snapshot());
    const save = () => preferences.set(prefKey, JSON.stringify({enabled, volume, categories}));
    const api = {
      state: snapshot,
      receive(events) {
        for (const event of events) if (event && typeof event.id === "string" && event.id.length <= 180 && !heard.has(event.id))
          pending.set(event.id, { id:event.id, category:event.category || "routes" });
        notify();
      },
      async play(test = false) {
        if (inFlight || playing) return false;
        const batch = [...pending.values()].filter(x => categories[x.category] !== false);
        if (!test && (!enabled || batch.length === 0)) return false;
        inFlight = true;
        try {
          audio.volume = volume; audio.currentTime = 0;
          await audio.play();
          if (!test && !enabled) { audio.pause(); return false; }
          blocked = false; failed = false; playing = true;
          if (!test) {
            for (const item of batch) { pending.delete(item.id); heard.add(item.id); }
            const recent = [...heard].slice(-500); heard.clear(); recent.forEach(id => heard.add(id));
            heardStorage.set(heardKey, JSON.stringify(recent));
          }
          return true;
        } catch (error) {
          blocked = error?.name === "NotAllowedError"; failed = !blocked; return false;
        } finally { inFlight = false; notify(); }
      },
      toggle() {
        if (enabled && (blocked || failed)) return this.play();
        enabled = !enabled; save();
        if (!enabled) { audio.pause(); playing = false; }
        notify(); return enabled ? this.play() : Promise.resolve(false);
      },
      setVolume(value) { volume = Math.max(0, Math.min(1, Number(value) || 0)); audio.volume = volume; save(); notify(); },
      setCategory(category, value) { if (Object.hasOwn(categories, category)) { categories[category] = !!value; save(); notify(); } }
    };
    audio.addEventListener("ended", () => { playing = false; notify(); api.play(); });
    audio.addEventListener("error", () => { playing = false; failed = true; notify(); });
    notify();
    return api;
  }
  return { safeStorage, routeStore, alertPlayer };
});
