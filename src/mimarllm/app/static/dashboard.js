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
  renderStudio();
}
async function chooseProject(id) {
  state.projectId=id;state.runId="";state.studioRunReport=null;
  $("selected-project").value=id;
  $("native-line").replaceChildren(new Option("Önce kaynak çizgileri inceleyin",""));
  await refresh();
}
async function loadProject() {
  const data=await api("/api/projects/"+state.projectId);
  const list=$("run-list");clear(list);
  if(!data.runs.length) {
    list.append(el("p","Bu çizimde henüz analiz kaydı yok.","muted"));
    state.studioRunReport=null;
    $("count-findings").textContent="—"; $("run-state").textContent="İlk analizi başlatın";
    clear($("finding-list"));clear($("report-files"));clear($("stage-list"));
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
  state.studioRunReport=data;
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
  renderStudio();
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
    const run=await api("/api/projects/"+state.projectId+"/runs",{
      method:"POST",headers:{"Content-Type":"application/json"},
      body:JSON.stringify({config,formats}),
    });
    state.runId=run.run_id;
    await loadProject();
    notice(run.completion==="PARTIAL_WITH_ERRORS"?
      "Rapor üretildi ancak bazı aşamalar hata verdi. Manifesti inceleyin.":
      "Rapor üretildi. Kaynakları ve inceleme uyarılarını kontrol edin.",
      run.completion==="PARTIAL_WITH_ERRORS");
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

/* UI-only adaptation of the user-supplied studio HTML; actual data exclusively from localhost API. */
const STUDIO_GRADES=Object.freeze({
  1:{name:"Proje I",count:18},
  2:{name:"Proje II",count:31},
  3:{name:"Proje III",count:45},
  4:{name:"Proje IV / Bitirme",count:55}
});
const STUDIO_DIMENSIONS=[
  ["TD","Teknik doğruluk"],["MK","Mekânsal kurgu"],
  ["SM","Strüktürel mantık"],["CE","Cephe ve estetik"],
  ["YU","Yönetmelik uyumu"],["SU","Sürdürülebilirlik"],
  ["SK","Sunum kalitesi"],["IF","İnovasyon faktörü"]
];
let studioGrade=1,studioView="drawing";
state.studioRunReport=null;
state.curriculumCache=new Map();

function studioLink(label) {
  const link=el("a",label);
  link.href="/api/projects/"+state.projectId+"/runs/"+state.runId+"/files/analysis.html";
  link.target="_blank";
  link.rel="noopener noreferrer";
  return link;
}
function renderStudio() {
  if(!$("studio-viewport")) return;
  const grade=STUDIO_GRADES[studioGrade], summary=$("studio-grade-summary");
  summary.textContent=grade.name+" · "+grade.count+
    " katalog modülü hedefi (tamamlanmış yazılım modülü sayısı değil).";
  for(const button of document.querySelectorAll(".studio-grade")) {
    const active=Number(button.dataset.level)===studioGrade;
    button.classList.toggle("selected",active);
    button.setAttribute("aria-pressed",String(active));
  }
  const modules=$("studio-module-list");
  clear(modules);
  const record=state.curriculumCache.get(studioGrade);
  if(!record){
    modules.append(el("p","Sunucudan müfredat kaydı bekleniyor…","studio-tip"));
  } else {
    for(const mod of record.modules) {
      const node=el("div","","studio-module");
      node.append(el("strong",mod.code),document.createTextNode(mod.title),
        el("span",mod.implementation_state+" · Puan yok"));
      modules.append(node);
    }
  }
  const rub=$("studio-rubric");
  clear(rub);
  for(const [code,label] of STUDIO_DIMENSIONS) {
    const box=el("div","","studio-dimension");
    box.title=label+" · puanlama ve Delphi doğrulaması bekliyor";
    box.append(el("strong",code),el("small","Puan: —"));
    rub.append(box);
  }
  for(const tab of document.querySelectorAll(".studio-tab[data-view]")) {
    const selected=tab.dataset.view===studioView;
    tab.classList.toggle("selected",selected);
    tab.setAttribute("aria-selected",String(selected));
  }
  const view=$("studio-viewport");
  clear(view);
  if(studioView==="legal") {
    view.append(el("strong","Mevzuat kaynak incelemesi · HOLD"),
      el("p","Gerçek Resmî Gazete belgesi, sürüm, uygulanabilirlik ve uzman doğrulaması olmadan uygunluk kararı veya sarı kaynak bağlantısı üretilemez."));
    if(state.studioRunReport&&state.projectId&&state.runId)
      view.append(studioLink("Kaynaklı teknik raporu incele ↗"));
    return;
  }
  if(!state.projectId) {
    view.append(el("strong","Önce bir DXF veya PDF yükleyin"),
      el("p","Çizim yükleme ve analiz akışı korunmuştur. Burada sahte 2B plan ya da otomatik onarım gösterilmez."));
    return;
  }
  const report=state.studioRunReport;
  if(!report) {
    view.append(el("strong","Analiz raporu bekleniyor"),
      el("p","Seçilen projeyi analiz laboratuvarında çalıştırın. 2B kaynak geometrisi ve kanıt bağlantıları mevcut HTML raporunda açılır."));
    return;
  }
  const manifest=report.manifest||{};
  const details=(manifest.completion||"INCELEME_BEKLENIYOR").replaceAll("_"," ");
  view.append(el("strong","Gerçek yerel analiz · "+details),
    el("p","Kaynak SHA-256: "+String(manifest.source_sha256||"—").slice(0,16)+"…"),
    el("p","Bulgular: "+String(manifest.report_finding_count??"—")+
      " · Kalibrasyon: "+String(manifest.calibration_state||"BELİRSİZ")),
    el("p","Bu panel kaynağa bağlı rapora yönlendirir; 3D kütle veya doğrulanmamış metre ölçümü üretmez."));
  if(report.reports?.includes("analysis.html")&&state.runId) 
    view.append(studioLink("Özgün çizim bulgularını aç ↗"));
}
async function loadStudioGrade(grade) {
  if(!state.curriculumCache.has(grade)) {
    const info=await api("/api/curriculum/grades/"+grade);
    if(info.grade!==grade || ![18,31,45,55][grade-1] ||
        info.catalogued_module_count!==[18,31,45,55][grade-1] ||
        info.legal_gate!=="REGULATORY_LOCKED") {
      throw new Error("Müfredat kayıtları tutarsız.");
    }
    state.curriculumCache.set(grade,info);
  }
  renderStudio();
}
function initStudio() {
  for(const button of document.querySelectorAll(".studio-grade")) {
    button.addEventListener("click",()=>{
      studioGrade=Number(button.dataset.level);
      renderStudio();
      loadStudioGrade(studioGrade).catch(e=>notice(e.message,true));
    });
  }
  for(const button of document.querySelectorAll(".studio-tab[data-view]")) {
    button.addEventListener("click",()=>{
      studioView=button.dataset.view;
      renderStudio();
    });
  }
  renderStudio();
  loadStudioGrade(studioGrade).catch(e=>notice(e.message,true));
}

initStudio();
start();
