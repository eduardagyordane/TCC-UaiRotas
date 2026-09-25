const test = require("node:test");
const assert = require("node:assert/strict");
const { safeStorage, routeStore, alertPlayer } = require("../../uairotas/static/js/core.js");

function storage() {
  const map = new Map();
  return safeStorage(() => ({ getItem:key => map.get(key) ?? null, setItem:(key,value) => map.set(key,value) }));
}
function sound(overrides={}) {
  const handlers={};
  const audio={ volume:1, currentTime:0, calls:0, paused:false,
    addEventListener:(event,fn) => { handlers[event]=fn; },
    async play() { this.calls++; }, pause() { this.paused=true; }, ...overrides };
  return {audio,handlers};
}
function player(audio,prefs=storage(),heard=storage(),userId="1") {
  return alertPlayer({audio,preferences:prefs,heardStorage:heard,userId});
}
test("storage denial and corrupt JSON cannot interrupt initialization", () => {
  const blocked=safeStorage(() => { throw new Error("denied"); });
  blocked.set("theme","dark"); assert.equal(blocked.get("theme"),"dark");
  blocked.set("data","{invalid"); assert.deepEqual(blocked.json("data",[]),[]);
  assert.equal(blocked.get("missing","light"),"light");
});
test("road geometry survives repeated source recreation; invalid coordinates rejected", () => {
  const store=routeStore([{id:1,points:[[0,0],[1,1]],path_kind:"planned"}]);
  const geometry={type:"LineString",coordinates:[[0,0],[.5,.8],[1,1]]};
  assert.ok(store.set(1,geometry));
  assert.deepEqual(store.feature(1).geometry,geometry);
  assert.deepEqual(store.feature("1").geometry,geometry);
  assert.equal(store.set(1,{type:"LineString",coordinates:[[NaN,0],[999,1]]}),false);
  assert.deepEqual(store.get(1).geometry,geometry);
});
test("first click after autoplay denial unlocks sound instead of muting", async () => {
  let denied=true; const s=sound({ async play() { this.calls++;if(denied) throw Object.assign(new Error(),{name:"NotAllowedError"}); } });
  const p=player(s.audio);p.receive([{id:"lunch:1",category:"routes"}]);
  assert.equal(await p.play(),false); assert.equal(p.state().blocked,true);
  denied=false; assert.equal(await p.toggle(),true);assert.equal(p.state().enabled,true);assert.equal(p.state().pending,0);
  await p.toggle();assert.equal(p.state().enabled,false);assert.equal(s.audio.paused,true);
});
test("global event IDs deduplicate across pages but distinct form errors play", async () => {
  const prefs=storage(),heard=storage(),s=sound(),p=player(s.audio,prefs,heard);
  p.receive([{id:"lunch:1",category:"routes"}]);await p.play();
  const nextSound=sound(),next=player(nextSound.audio,prefs,heard);
  next.receive([{id:"lunch:1",category:"routes"}]);assert.equal(await next.play(),false);assert.equal(nextSound.audio.calls,0);
  next.receive([{id:"form:one",category:"forms"}]);await next.play();nextSound.handlers.ended();
  next.receive([{id:"form:two",category:"forms"}]);await next.play();assert.equal(nextSound.audio.calls,2);
});
test("failed playback never marks an event as heard", async () => {
  const s=sound({ async play() { throw new Error("audio unavailable"); } }),heard=storage(),p=player(s.audio,storage(),heard);
  p.receive([{id:"oil:1",category:"fleet"}]);await p.play();
  assert.equal(p.state().pending,1);assert.equal(p.state().failed,true);
  assert.deepEqual(heard.json("uairotas-heard-v2:1",[]),[]);
});
test("volume and category settings persist and are isolated per user", async () => {
  const prefs=storage(),heard=storage(),s=sound(),p=player(s.audio,prefs,heard);
  p.setVolume(.25);p.setCategory("fleet",false);p.receive([{id:"oil:1",category:"fleet"}]);
  assert.equal(await p.play(),false);
  const next=player(sound().audio,prefs,heard);assert.equal(next.state().volume,.25);assert.equal(next.state().categories.fleet,false);
  const another=player(sound().audio,prefs,heard,"2");assert.equal(another.state().volume,.72);assert.equal(another.state().categories.fleet,true);
  p.setCategory("fleet",true);await p.play();assert.equal(s.audio.volume,.25);
});
test("heard state is scoped to the signed-in user", async () => {
  const prefs=storage(),heard=storage(),a=player(sound().audio,prefs,heard,"1");
  a.receive([{id:"lunch:1"}]);await a.play();
  const second=sound(),b=player(second.audio,prefs,heard,"2");b.receive([{id:"lunch:1"}]);
  assert.equal(await b.play(),true);
});
test("rapid requests do not overlap playback", async () => {
  let release;const s=sound({play() {this.calls++;return new Promise(resolve=>{release=resolve;});}});
  const p=player(s.audio);p.receive([{id:"a"}]);
  const first=p.play();assert.equal(await p.play(),false);release();await first;
  assert.equal(s.audio.calls,1);
});
test("muting during a pending play promise does not mark events heard", async () => {
  let release;const s=sound({play() {return new Promise(resolve=>{release=resolve;});}}),p=player(s.audio);
  p.receive([{id:"a"}]);const first=p.play();await p.toggle();release();await first;
  assert.equal(p.state().enabled,false);assert.equal(p.state().pending,1);assert.equal(s.audio.paused,true);
});
