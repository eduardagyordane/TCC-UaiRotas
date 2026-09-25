const test=require("node:test");
const assert=require("node:assert/strict");
const vm=require("node:vm");
const fs=require("node:fs");
const {routeStore}=require("../../uairotas/static/js/core.js");

class Element {
  constructor() {this.listeners={};this.attributes={};this.children=[];this.dataset={};this.hidden=false;this.style={setProperty(){}};}
  addEventListener(name, fn) {this.listeners[name]=fn;}
  click() {return this.listeners.click?.({currentTarget:this});}
  setAttribute(name,value) {this.attributes[name]=value;}
  appendChild(child) {this.children.push(child);}
  scrollIntoView() {}
}
async function setup(fail=false, delayed=false) {
  const state={calls:0,fail,markers:[],events:{},timers:[]};
  const routes=[{id:"1",name:"Alfa",color:"#a00",path_kind:"planned",points:[[0,0],[1,1]]},
    {id:"2",name:"Beta",color:"#00a",path_kind:"planned",points:[[2,2],[3,3]]}];
  const data={center:{lng:0,lat:0},zoom:13,date:"2026-09-25",routes,
    orders:[{id:"1",code:"OS1",customer:"Teste",address:"Endereço",service:"Instalação",status:"Atrasada",route_id:"1",lng:1,lat:1,label:"1"}],
    places:[{name:"Base",address:"Base teste",type:"office",lng:0,lat:0}]};
  const nodes={map:new Element(),status:new Element(),retry:new Element(),reset:new Element(),payload:{textContent:JSON.stringify(data)},meta:{content:"pk.fake"}};
  const buttons=routes.map(route=>{const e=new Element();e.dataset.routeFocus=route.id;return e;});
  const theme={dataset:{theme:"light"}};
  class MapMock {
    constructor(){this.handlers={};this.sources={};this.layers={};state.map=this;}
    addControl(){}
    on(name,idOrFn,fn){if(typeof idOrFn==="function")(this.handlers[name]??=[]).push(idOrFn);}
    async emit(name){for(const fn of this.handlers[name]||[])fn({});await new Promise(resolve=>setImmediate(resolve));await new Promise(resolve=>setImmediate(resolve));}
    isStyleLoaded(){return true;}
    getSource(id){return this.sources[id];}
    addSource(id,value){this.sources[id]={data:value.data,setData(data){this.data=data;}};}
    getLayer(id){return this.layers[id];}
    addLayer(layer){this.layers[layer.id]=layer;}
    setLayoutProperty(id,name,value){this.layers[id].layout[name]=value;}
    fitBounds(bounds){this.bounds=bounds;}
    setStyle(){this.sources={};this.layers={};this.emit("style.load");}
    resize(){}
  }
  class Bounds{constructor(){this.points=[];}extend(point){this.points.push(point);}}
  class Popup{setDOMContent(node){this.node=node;return this;}setLngLat(){return this;}addTo(){return this;}}
  class Marker{constructor({element}){this.element=element;state.markers.push(this);}setLngLat(){return this;}setPopup(p){this.popup=p;return this;}addTo(){return this;}}
  const mapboxgl={Map:MapMock,LngLatBounds:Bounds,Popup,Marker,NavigationControl:class{},FullscreenControl:class{},supported:()=>true};
  const window={mapboxgl,innerWidth:1400,matchMedia:()=>({matches:false}),addEventListener:(name,fn)=>{state.events[name]=fn;},location:{reload(){state.reloaded=true;}}};
  const document={documentElement:theme,
    getElementById:id=>id==="operational-map"?nodes.map:nodes.payload,
    querySelector:selector=>selector.includes("meta[")?nodes.meta:selector.includes("map-status")?nodes.status:selector.includes("map-retry")?nodes.retry:nodes.reset,
    querySelectorAll:()=>buttons,
    createElement:()=>new Element(),createElementNS:()=>new Element()};
  const context={window,document,mapboxgl,UaiRotas:{routeStore},AbortController,console,
    setTimeout:(fn,ms)=>{state.timers.push({fn,ms});return state.timers.length;},clearTimeout(){},
    fetch:async(url,options)=>{
      state.calls++;state.lastSignal=options.signal;
      if(delayed) return new Promise((resolve,reject)=>options.signal.addEventListener("abort",()=>reject(Object.assign(new Error("timeout"),{name:"AbortError"}))));
      if(state.fail)throw new Error("network");
      const base=url.includes("2,2;3,3")?2:0;
      return {ok:true,json:async()=>({routes:[{geometry:{type:"LineString",coordinates:[[base,base],[base+.4,base+.7],[base+1,base+1]]}}]})};
    }};
  vm.runInNewContext(fs.readFileSync("uairotas/static/js/maps.js","utf8"),context);
  await state.map.emit("style.load");await state.map.emit("load");
  return {...state,state,nodes,buttons,theme};
}
test("theme switch keeps matched geometry, does not fetch again, and preserves route focus",async()=>{
  const s=await setup();
  assert.equal(s.state.calls,2);assert.equal(s.state.map.sources["route-1"].data.geometry.coordinates.length,3);
  await s.buttons[0].click();
  assert.equal(s.state.map.layers["route-2"].layout.visibility,"none");
  assert.equal(s.state.markers[1].element.hidden,true);
  s.theme.dataset.theme="dark";s.state.events["uairotas:theme"]();
  assert.equal(s.state.map.sources["route-1"].data.geometry.coordinates.length,3);
  assert.equal(s.state.map.layers["route-2"].layout.visibility,"none");assert.equal(s.state.calls,2);
  await s.nodes.reset.click();assert.equal(s.state.markers[1].element.hidden,false);
  assert.equal(s.state.map.layers["route-2"].layout.visibility,"visible");
  assert.equal(s.state.markers[2].element.children[0].className,"map-marker-inner map-alert-ring");
});
test("Directions errors show an approximate route and retry can recover",async()=>{
  const s=await setup(true);
  assert.match(s.nodes.status.textContent,/aproximada/);assert.equal(s.nodes.retry.hidden,false);
  assert.equal(s.state.map.sources["route-1"].data.geometry.coordinates.length,2);
  s.state.fail=false;await s.nodes.retry.click();
  await new Promise(resolve=>setImmediate(resolve));await new Promise(resolve=>setImmediate(resolve));
  assert.equal(s.nodes.retry.hidden,true);
  assert.equal(s.state.map.sources["route-1"].data.geometry.coordinates.length,3);
});
test("slow Directions requests are aborted after the configured timeout",async()=>{
  const s=await setup(false,true);
  s.state.timers.filter(timer=>timer.ms===10000).forEach(timer=>timer.fn());
  await new Promise(resolve=>setImmediate(resolve));await new Promise(resolve=>setImmediate(resolve));
  assert.equal(s.state.lastSignal.aborted,true);
  assert.match(s.nodes.status.textContent,/aproximada/);
  assert.equal(s.nodes.retry.hidden,false);
});
