const BASE=window.__BRIDGE_BASE__||"";
let ENTITIES=[], CFG={feeds:[]}, NAME={}, TEMPLATES=[];
const nameFor=v=>v?(NAME[v]||"⚠ unknown entity"):"";

// --- theme (HA-style; follows OS dark mode until the user overrides) ---
const ROOT=document.documentElement;
const darkNow=()=> (ROOT.dataset.theme||"")==="dark" ||
  (!ROOT.dataset.theme && matchMedia("(prefers-color-scheme:dark)").matches);
function paintTheme(){ const b=document.getElementById("theme"); if(b) b.textContent=darkNow()?"☀️":"🌙"; }
(function(){ const s=localStorage.getItem("trmnl-theme"); if(s==="dark"||s==="light") ROOT.dataset.theme=s; paintTheme(); })();
function toggleTheme(){ ROOT.dataset.theme=darkNow()?"light":"dark"; localStorage.setItem("trmnl-theme",ROOT.dataset.theme); paintTheme(); }
const esc=s=>(s==null?"":String(s)).replace(/[&<>"]/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));
function status(m){document.getElementById("status").textContent=m;}

// Type-ahead entity fields are <input list>; build the shared <datalist>s once.
// The option value is the entity_id (what we save); the label is the friendly
// name, so typing either filters the suggestions.
function buildDatalists(){
  NAME={};
  const opt=e=>{NAME[e.entity_id]=e.name; return `<option value="${esc(e.entity_id)}">${esc(e.name)}</option>`;};
  const all=ENTITIES.map(opt).join("");
  const wx=ENTITIES.filter(e=>e.domain==="weather").map(opt).join("");
  document.getElementById("dl").innerHTML=
    `<datalist id="dl-all">${all}</datalist><datalist id="dl-weather">${wx}</datalist>`;
}
function ent(k,val,list){
  const bad=(val&&!NAME[val])?" bad":"";
  return `<span class="entwrap"><input class="ent" list="${list}" data-k="${k}" value="${esc(val)}" placeholder="type to search…"><span class="ename${bad}">${esc(nameFor(val))}</span></span>`;
}
function feedUrl(slug){ return `http://${location.hostname||"HA-HOST"}:8080/feeds/${slug||""}.json`; }
function feedTitle(f){ return esc(f.location||f.slug||"(new feed)"); }
function feedSum(f){
  const n=(f.sensors||[]).length+(f.entities||[]).length;
  const bits=[`/feeds/${esc(f.slug||"")}.json`];
  if((f.type||"weather")==="sensors"){
    bits.push("sensors only");
  }else{
    bits.push(f.weather_entity?esc(NAME[f.weather_entity]||f.weather_entity):"no weather");
    if(f.aqi_entity) bits.push("AQI");
    if(f.feels_like_entity) bits.push("feels-like");
  }
  bits.push(n+" reading"+(n===1?"":"s"));
  return bits.join(" · ");
}
function render(){
  const root=document.getElementById("feeds"); root.innerHTML="";
  CFG.feeds.forEach((f,fi)=>{
    const type=f.type||"weather";
    const c=document.createElement("div"); c.className="card"; c.dataset.fi=fi; c.dataset.open=f._open?"1":"0"; c.dataset.type=type;
    const url=feedUrl(f.slug);
    c.innerHTML=`
      <div class="chead">
        <span class="chev">${f._open?"▾":"▸"}</span>
        <div class="ctitlewrap"><div class="ctitle">${feedTitle(f)} <span class="badge badge--cat">${type==="sensors"?"Sensor feed":"Weather feed"}</span></div><div class="csum">${feedSum(f)}</div></div>
        <button class="del" data-del-feed>✕ remove</button>
      </div>
      <div class="cbody">
        <div class="row">
          <label>Slug (feed URL)<input data-k="slug" value="${esc(f.slug)}"></label>
          <label>Location (title)<input data-k="location" value="${esc(f.location)}"></label>
        </div>
        <div class="exchange">Terminus Exchange URL:&nbsp;<code>${esc(url)}</code>
          <button data-copy="${esc(url)}">Copy URL</button></div>
        ${type!=="sensors" ? `
        <div class="row">
          <label>Weather entity${ent("weather_entity",f.weather_entity,"dl-weather")}</label>
          <label>Feels-like sensor${ent("feels_like_entity",f.feels_like_entity,"dl-all")}</label>
          <label>AQI sensor${ent("aqi_entity",f.aqi_entity,"dl-all")}</label>
        </div>
        <div class="row">
          <label>Forecast type<select data-k="forecast_type">${["daily","hourly","twice_daily"].map(t=>`<option${t===(f.forecast_type||"daily")?" selected":""}>${t}</option>`).join("")}</select></label>
          <label>Forecast days<input type="number" min="1" max="10" data-k="forecast_days" value="${f.forecast_days||4}"></label>
        </div>` : ``}
        <h4>Sensors</h4><div data-list="sensors"></div><button data-add="sensors">+ sensor</button>
        <h4>Other entities</h4><div data-list="entities"></div><button data-add="entities">+ entity</button>
      </div>`;
    root.appendChild(c);
    rows(c.querySelector('[data-list="sensors"]'), f.sensors||[]);
    rows(c.querySelector('[data-list="entities"]'), f.entities||[]);
  });
}
function renderTemplates(){
  const el=document.getElementById("templates"); if(!el) return;
  const intro=`<p class="sub">Terminus has no API to import templates, so copy one into your
    extension's editor (Extensions → ＋ → Kind = <b>Poll</b>) and set its Exchange URL to a feed's
    URL (Feeds tab). Add your own by dropping a <code>.liquid</code> file plus a
    <code>templates.yaml</code> entry into the add-on's <code>/data/templates</code> — anything,
    not just weather — and it appears here automatically.</p>`;
  if(!TEMPLATES.length){ el.innerHTML=intro+"<p class=sub>No templates found.</p>"; return; }
  el.innerHTML=intro+TEMPLATES.map((t,i)=>`<div class="tplcard">
    <div class="tplhead">
      <div class="tpltitle"><strong>${esc(t.label)}</strong>
        ${t.size?`<span class="badge">${esc(t.size)}</span>`:""}
        ${t.category?`<span class="badge badge--cat">${esc(t.category)}</span>`:""}</div>
      <button data-copy-tpl="${i}">Copy template</button></div>
    ${t.description?`<p class="tpldesc">${esc(t.description)}</p>`:""}
    <textarea readonly spellcheck="false">${esc(t.content)}</textarea></div>`).join("");
}
async function copyText(text,btn){
  try{ await navigator.clipboard.writeText(text); }
  catch(e){ const ta=document.createElement("textarea"); ta.value=text; document.body.appendChild(ta); ta.select(); try{document.execCommand("copy");}catch(_){} ta.remove(); }
  if(btn){ const o=btn.textContent; btn.textContent="Copied ✓"; setTimeout(()=>btn.textContent=o,1200); }
}
function rows(el,items){ el.innerHTML=""; items.forEach(it=>el.appendChild(rowEl(it))); }
function rowEl(it){
  const d=document.createElement("div"); d.className="srow";
  d.innerHTML=`${ent("entity_id",it.entity_id,"dl-all")}
    <input data-k="label" placeholder="label" value="${esc(it.label)}">
    <input data-k="unit" placeholder="unit" value="${esc(it.unit)}" size="6">
    <button data-del-row>✕</button>`;
  return d;
}
function collect(){
  const feeds=[];
  document.querySelectorAll("#feeds .card").forEach(card=>{
    const f={sensors:[],entities:[],_open:card.dataset.open==="1",type:card.dataset.type||"weather"};
    card.querySelectorAll("[data-k]").forEach(el=>{
      if(el.closest("[data-list]")) return;
      f[el.dataset.k]= el.dataset.k==="forecast_days" ? parseInt(el.value||"4",10) : el.value;
    });
    ["sensors","entities"].forEach(list=>{
      card.querySelector(`[data-list="${list}"]`).querySelectorAll(".srow").forEach(r=>{
        const row={}; r.querySelectorAll("[data-k]").forEach(el=>row[el.dataset.k]=el.value);
        f[list].push(row);
      });
    });
    feeds.push(f);
  });
  return feeds;
}
document.addEventListener("click",e=>{
  const t=e.target;
  if(t.classList && t.classList.contains("tab")){
    document.querySelectorAll(".tab").forEach(b=>b.classList.toggle("active",b===t));
    document.getElementById("panel-feeds").hidden = t.dataset.tab!=="feeds";
    document.getElementById("panel-templates").hidden = t.dataset.tab!=="templates";
    return;
  }
  if(t.id==="addWeather"){ CFG.feeds=collect(); CFG.feeds.push({type:"weather",slug:"feed"+(CFG.feeds.length+1),location:"",forecast_type:"daily",forecast_days:4,sensors:[],entities:[],_open:true}); render(); }
  else if(t.id==="addSensors"){ CFG.feeds=collect(); CFG.feeds.push({type:"sensors",slug:"feed"+(CFG.feeds.length+1),location:"",sensors:[],entities:[],_open:true}); render(); }
  else if(t.dataset.delFeed!==undefined){ CFG.feeds=collect(); CFG.feeds.splice(+t.closest(".card").dataset.fi,1); render(); }
  else if(t.dataset.add){ CFG.feeds=collect(); CFG.feeds[+t.closest(".card").dataset.fi][t.dataset.add].push({}); render(); }
  else if(t.dataset.delRow!==undefined){ CFG.feeds=collect(); const card=t.closest(".card"); const le=t.closest("[data-list]");
    const idx=[...le.querySelectorAll(".srow")].indexOf(t.closest(".srow")); CFG.feeds[+card.dataset.fi][le.dataset.list].splice(idx,1); render(); }
  else if(t.dataset.copy!==undefined){ copyText(t.dataset.copy,t); }
  else if(t.dataset.copyTpl!==undefined){ copyText((TEMPLATES[+t.dataset.copyTpl]||{}).content||"",t); }
  else if(t.id==="theme"){ toggleTheme(); }
  else if(t.id==="save"){ save(); }
  else if(t.closest(".chead")){ const card=t.closest(".card"); CFG.feeds=collect();
    const fi=+card.dataset.fi; CFG.feeds[fi]._open=!(card.dataset.open==="1"); render(); }
});
document.addEventListener("input",e=>{
  if(!e.target.classList || !e.target.classList.contains("ent")) return;
  const s=e.target.parentNode.querySelector(".ename"); if(!s) return;
  const v=e.target.value;
  s.textContent=nameFor(v);
  s.classList.toggle("bad", !!(v && !NAME[v]));
});
async function save(){
  status("Saving…");
  const local=collect();
  const clean=local.map(f=>{const{_open,...rest}=f;return rest;});
  try{
    const r=await fetch(BASE+"api/config",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({feeds:clean})});
    const j=await r.json();
    if(j.ok){ j.feeds.forEach((f,i)=>f._open=local[i]?local[i]._open:false); CFG.feeds=j.feeds; render(); status("Saved ✓ — applied live."); }
    else status("Save failed: "+(j.error||r.status));
  }catch(err){ status("Save failed: "+err); }
}
async function load(){
  try{
    const [c,e,tp]=await Promise.all([
      fetch(BASE+"api/config").then(r=>r.json()),
      fetch(BASE+"api/entities").then(r=>r.json()),
      fetch(BASE+"api/templates").then(r=>r.json()).catch(()=>({templates:[]}))]);
    CFG=c&&c.feeds?c:{feeds:[]}; ENTITIES=(e&&e.entities)||[]; TEMPLATES=(tp&&tp.templates)||[];
    CFG.feeds.forEach((f,i)=>f._open=(i===0));
    if(e&&e.error) status("Entity list error: "+e.error);
    buildDatalists(); render(); renderTemplates();
  }catch(err){ status("Load failed: "+err); }
}
load();
