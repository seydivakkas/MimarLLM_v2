"use strict";
const state = {csrf:"",projects:[],projectId:"",runId:"",running:false};
const $ = (id) => document.getElementById(id);
const api = async (path, {method="GET",body=null,headers={}}={}) => {
  const extras = {...headers};
  if(method!=="GET") extras["X-Mimar-CSRF"]=state.csrf;
  const response = await fetch(path, {method,headers:extras,body,cache:"no-store",credentials:"same-origin"});
  let data;
  try { data=await response.json(); } catch { data={detail:"Sunucu beklenmeyen yanıt verdi."}; }
  if(!response.ok) throw new Error(typeof data.detail==="string" ? data.detail : ("HTTP "+response.status));
  return data;
};
const el = (tag,text="",cls="") => {
  const node=document.createElement(tag);
  if(text!==undefined) node.textContent=String(text);
  if(cls) node.className=cls;
  return node;
};
const clear=(node)=>node.replaceChildren();
function notice(text,bad=false) {
  const box=$("notice"); box.textContent=String(text);box.className="notice"+(bad?" bad":"");box.hidden=false;
}
function busy(flag) {
  state.running=flag;
  $("analyze-button").disabled=flag||!state.projectId;
  $("upload-button").disabled=flag;
  $("analyze-button").firstChild.textContent=flag?"Analiz yürütülüyor… ":"Kaynaklı analizi çalıştır ";
}
function projectLabel(project) {
  return project.source_kind+" · "+project.source_sha256.slice(0,12)+"…";
}
async function refresh() {
  const data=await api("/api/projects");
  state.projects=data.projects;
  $("count-projects").textContent=String(data.projects.length);
  const list=$("project-list"),select=$("selected-project");
  clear(list);clear(select);
  if(!data.projects.length) {
    list.append(el("p","Henüz yerel çizim eklenmedi.","muted"));
    select.add(new Option("Önce bir DXF veya PDF yükleyin",""));
  }
  for(const project of data.projects) {
    const button=el("button","","item"+(project.project_id===state.projectId?" chosen":""));
    button.type="button";
    const heading=el("span");
    heading.append(el("strong",projectLabel(project)),
                   el("small",new Date(project.created_utc).toLocaleString("tr-TR")));
    button.append(heading,el("span",project.source_kind,"type"));
    button.addEventListener("click",()=>chooseProject(project.project_id));
    list.append(button);
    select.add(new Option(projectLabel(project),project.project_id));
  }
  if(!state.projects.some(p=>p.project_id===state.projectId)) {
    state.projectId=state.projects[0]?.project_id||"";
    state.runId="";
  }
  select.value=state.projectId;
  $("source-type").textContent=state.projects.find(p=>p.project_id===state.projectId)?.source_kind||"—";
  $("source-meta").textContent=state.projectId?state.projectId.slice(0,12)+"…":"Dosya bekleniyor";
  $("analyze-button").disabled=!state.projectId||state.running;
  if(state.projectId) await loadProject();
}
async function chooseProject(id) {
  state.projectId=id;state.runId="";
  $("selected-project").value=id;
  $("native-line").replaceChildren(new Option("Önce kaynak çizgileri inceleyin",""));
  await refresh();
}
async function loadProject() {
  const data=await api("/api/projects/"+state.projectId);
  const list=$("run-list");clear(list);
  if(!data.runs.length) {
    list.append(el("p","Bu çizimde henüz analiz kaydı yok.","muted"));
    $("count-findings").textContent="—"; $("run-state").textContent="İlk analizi başlatın";
    clear($("finding-list"));clear($("report-files"));clear($("stage-list"));
    renderDrawing({native_lines:[],manifest:{}});
    $("stage-list").append(el("p","Analiz başladıktan sonra aşama sonuçları burada görünecek.","muted"));
    return;
  }
  for(const run of data.runs) {
    const button=el("button","","item"+(state.runId===run.run_id?" chosen":""));button.type="button";
    const wrap=el("span");
    wrap.append(el("strong",run.completion.replaceAll("_"," ")),
                el("small",run.run_id.slice(0,13)+"… · "+run.report_finding_count+" bulgu"));
    button.append(wrap,el("span",run.stage_errors?"HATA":"RAPOR","type"));
    button.addEventListener("click",()=>loadRun(run.run_id));
    list.append(button);
  }
  if(!data.runs.some(x=>x.run_id===state.runId)) state.runId=data.runs[0].run_id;
  await loadRun(state.runId);
}
async function loadRun(id) {
  state.runId=id;
  const data=await api("/api/projects/"+state.projectId+"/runs/"+id);
  $("count-findings").textContent=String(data.manifest.report_finding_count);
  $("run-state").textContent=data.manifest.completion.replaceAll("_"," ");
  const stages=$("stage-list");clear(stages);
  for(const s of data.manifest.stages) {
    const card=el("div","","stage"),left=el("div");
    left.append(el("span",s.stage+(s.frame_id?" · "+s.frame_id:""),"name"),
                el("small",s.reason_code));
    const stateClass=s.status==="COMPLETE"?"ok":s.status==="REVIEW_REQUIRED"?"review":s.status==="ERROR"?"error":"skip";
    card.append(left,el("span",s.status,"state "+stateClass));stages.append(card);
  }
  const select=$("native-line");clear(select);
  select.add(new Option("Ölçek belirsiz · kalibrasyon seçme",""));
  for(const source of data.native_lines) {
    select.add(new Option(
      (source.layer||"Katmansız")+" · "+source.frame_id+" · "+
      (source.cad_handle||source.entity_id.slice(0,16))+" · "+
      source.entity_id.slice(0,12)+"…",source.entity_id
    ));
  }
  renderDrawing(data);
  const findings=$("finding-list");clear(findings);
  findings.append(el("h3","Bulgular / değerlendirme adayları"));
  if(!data.findings.length) findings.append(el("p","Henüz bulgu yok; kaynak geometrisi HTML raporunda incelenebilir.","muted"));
  for(const f of data.findings.slice(0,35)) {
    const card=el("div","","finding");
    card.append(el("strong",f.check_id+" · "+f.status),el("small",f.reason_code+" · "+f.kind));
    findings.append(card);
  }
  if(data.truncated) findings.append(el("p","Ön izleme sayısı sınırlandırıldı; tam veri JSON raporundadır.","hint"));
  const exports=$("report-files");clear(exports);
  for(const name of data.reports) {
    if(name==="drawingir.json") continue;
    const link=el("a",name==="analysis.html"?"Görsel kanıt raporunu aç ↗":name);
    link.href="/api/projects/"+state.projectId+"/runs/"+id+"/files/"+name;
    link.target="_blank";link.rel="noopener noreferrer";
    exports.append(link);
  }
}
function renderDrawing(data) {
  const frame=$("frame-filter"),layer=$("layer-filter"),svg=$("drawing-2d");
  const summary=$("drawing-summary"),inspector=$("source-inspector");
  const lines=Array.isArray(data.native_lines)?data.native_lines:[];
  const frames=[...new Set(lines.map(s=>s.frame_id))].sort();
  clear(frame);clear(layer);clear(svg);
  inspector.textContent="Henüz kaynak seçilmedi.";
  if(!frames.length) {
    frame.add(new Option("Kaynak çizgi bulunamadı",""));
    layer.add(new Option("Katman yok",""));
    summary.textContent="Seçili raporda SVG önizlemeye uygun kaynak-native çizgi bulunamadı.";
    return;
  }
  for(const name of frames) frame.add(new Option(name,name));
  function draw() {
    clear(svg);
    const selected=lines.filter(s=>s.frame_id===frame.value &&
      (layer.value==="*" || (s.layer||"Katmansız")===layer.value));
    const good=selected.filter(s=>Array.isArray(s.points) && s.points.length===2 &&
      s.points.every(p=>Array.isArray(p)&&p.length>=2&&p.slice(0,2).every(Number.isFinite)));
    if(!good.length) {
      svg.setAttribute("viewBox","0 0 100 70");
      summary.textContent="Bu katmanda gösterilebilir çizgi bulunamadı.";
      return;
    }
    const pts=good.flatMap(s=>s.points);
    const minX=Math.min(...pts.map(p=>p[0])),maxX=Math.max(...pts.map(p=>p[0]));
    const minY=Math.min(...pts.map(p=>p[1])),maxY=Math.max(...pts.map(p=>p[1]));
    const width=Math.max(maxX-minX,1),height=Math.max(maxY-minY,1);
    const pad=Math.max(width,height)*0.04;
    svg.setAttribute("viewBox",[-pad,-pad,width+2*pad,height+2*pad].join(" "));
    const ns="http://www.w3.org/2000/svg";
    for(const source of good) {
      const flip=source.origin==="CAD_NATIVE";
      const p1=source.points[0],p2=source.points[1];
      const drawY=p=>flip?maxY-p[1]:p[1]-minY;
      const item=document.createElementNS(ns,"line");
      item.setAttribute("x1",String(p1[0]-minX));
      item.setAttribute("y1",String(drawY(p1)));
      item.setAttribute("x2",String(p2[0]-minX));
      item.setAttribute("y2",String(drawY(p2)));
      item.setAttribute("class","source-line");
      item.setAttribute("role","button");
      item.setAttribute("tabindex","0");
      item.setAttribute("aria-label","Kaynak çizgi: "+source.entity_id);
      const title=document.createElementNS(ns,"title");
      title.textContent=(source.layer||"Katmansız")+" · "+(source.cad_handle||source.entity_id);
      item.append(title);
      const focusSource=()=>{
        for(const old of svg.querySelectorAll(".selected")) old.classList.remove("selected");
        item.classList.add("selected");
        inspector.textContent=[
          "Kaynak SHA256: "+(data.source_sha256||data.manifest?.source_sha256||"BELİRSİZ"),
          "Frame: "+source.frame_id,
          "Kaynak türü: "+source.origin,
          "Katman: "+(source.layer||"Katmansız"),
          "Entity ID: "+source.entity_id,
          "CAD handle: "+(source.cad_handle||"—"),
          "Orijinal noktalar: "+JSON.stringify(source.points),
          "Durum: İNCELEME ADAYI; CAD/PDF değişmedi."
        ].join("\n");
      };
      item.addEventListener("click",focusSource);
      item.addEventListener("keydown",e=>{
        if(e.key==="Enter"||e.key===" "){e.preventDefault();focusSource();}
      });
      svg.append(item);
    }
    summary.textContent=good.length+" çizgi · "+frame.value+" · "+
      (layer.value==="*"?"tüm katmanlar":layer.value)+
      " (önizleme en fazla 400 kaynak çizgiyi kapsar).";
  }
  function updateLayers(){
    clear(layer);
    layer.add(new Option("Tüm katmanlar","*"));
    const names=[...new Set(lines.filter(s=>s.frame_id===frame.value)
      .map(s=>s.layer||"Katmansız"))].sort();
    for(const name of names) layer.add(new Option(name,name));
    draw();
  }
  frame.onchange=updateLayers;
  layer.onchange=draw;
  updateLayers();
}

async function upload() {
  const file=$("drawing-file").files?.[0];
  if(!file) return notice("Önce yerel DXF veya PDF dosyası seçin.",true);
  const extension=file.name.toLowerCase().split(".").pop();
  if(!["dxf","pdf"].includes(extension)) return notice("Yalnız DXF veya PDF yüklenebilir.",true);
  const limit=extension==="dxf"?25_000_000:50_000_000;
  if(file.size>limit) return notice("Dosya boyutu güvenlik sınırını aşıyor.",true);
  busy(true);
  try {
    const created=await api("/api/projects",{method:"POST",body:file,
      headers:{"Content-Type":"application/octet-stream","X-Mimar-Extension":extension}});
    state.projectId=created.project_id;state.runId="";
    notice("Yerel çizim kaydedildi. Kaynaklı analizi başlatabilirsiniz.");
    await refresh();
    $("analysis").scrollIntoView({behavior:"smooth",block:"start"});
  } catch(e) {notice(e.message,true);} finally {busy(false);}
}
function buildConfig() {
  let advanced;
  try {advanced=JSON.parse($("config-json").value||"{}");}
  catch {throw new Error("Gelişmiş JSON ayarları geçerli JSON olmalı.");}
  if(!advanced||Array.isArray(advanced)||typeof advanced!=="object") throw new Error("JSON bir ayar nesnesi olmalı.");
  const native=$("native-line").value;
  if(native) {
    const known=Number($("known-metres").value.replace(",","."));
    const reviewer=$("reviewer-label").value.trim();
    if(!Number.isFinite(known)||known<=0||!reviewer) throw new Error("Kalibrasyon için pozitif metre ve incelemeci etiketi gerekir.");
    advanced.calibration={entity_id:native,known_length_metres:known,reviewer_id:reviewer,method:"USER_REFERENCE"};
  } else if($("known-metres").value||$("reviewer-label").value) {
    throw new Error("Fiziksel kalibrasyonda gerçek kaynak çizgi seçilmelidir.");
  }
  return advanced;
}
async function analyze() {
  if(!state.projectId) return notice("Önce proje seçin.",true);
  let config;
  try {config=buildConfig();}catch(e){return notice(e.message,true);}
  const formats=["json","html"];
  if($("export-md").checked) formats.push("md");
  if($("export-pdf").checked) formats.push("pdf");
  busy(true);
  notice("Yerel analiz başlatıldı. Lütfen diğer projeyi aynı anda başlatmayın.");
  try {
    const projectId=state.projectId;
    const queued=await api("/api/projects/"+projectId+"/jobs",{
      method:"POST",headers:{"Content-Type":"application/json"},
      body:JSON.stringify({config,formats}),
    });
    let job=queued;
    for(let attempt=0;attempt<400;attempt++) {
      $("job-status").textContent="Analiz işi "+job.job_id.slice(0,12)+"… · "+job.state;
      if(job.state==="COMPLETED"||job.state==="FAILED") break;
      await new Promise(resolve=>setTimeout(resolve,1500));
      job=await api("/api/projects/"+projectId+"/jobs/"+queued.job_id);
    }
    if(job.state==="FAILED") throw new Error("Yerel analiz tamamlanamadı: "+job.reason_code);
    if(job.state!=="COMPLETED") throw new Error("İş sürüyor; uygulamayı yenilemeden önce yerel analizi kontrol edin.");
    state.runId=job.run_id;
    await loadProject();
    $("job-status").textContent="Analiz "+job.state+" · "+job.completion;
    notice(job.completion==="PARTIAL_WITH_ERRORS"?
      "Rapor üretildi ancak bazı aşamalar hata verdi. Manifesti inceleyin.":
      "Rapor üretildi. Kaynakları ve inceleme uyarılarını kontrol edin.",
      job.completion==="PARTIAL_WITH_ERRORS");
    $("evidence").scrollIntoView({behavior:"smooth",block:"start"});
  }catch(e){notice(e.message,true);}finally{busy(false);}
}
async function start() {
  try {
    state.csrf=(await api("/api/session")).csrf;
    if(!state.csrf) throw new Error("Yerel oturum güvenlik anahtarı alınamadı.");
    await refresh();
  }catch(e){notice("Yerel uygulama başlatılamadı: "+e.message,true);}
}
$("upload-button").addEventListener("click",upload);
$("refresh-button").addEventListener("click",()=>refresh().catch(e=>notice(e.message,true)));
$("analyze-button").addEventListener("click",analyze);
$("selected-project").addEventListener("change",e=>chooseProject(e.target.value).catch(x=>notice(x.message,true)));
$("drawing-file").addEventListener("change",e=>{
  const file=e.target.files?.[0];$("picked-file").textContent=file?file.name+" · "+(file.size/1024/1024).toFixed(2)+" MB":"Henüz dosya seçilmedi.";
});
start();
