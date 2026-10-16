"use strict";
const state = {csrf:"",projects:[],projectId:"",runId:"",running:false,selectedSource:null,reviews:[],editStatus:null,massingSources:[],massingSha:"",vlmLines:[],vlmSha:"",vlmConfigured:false,vlmRunning:false};
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
    updateMassingSources({native_lines:[],source_sha256:""});
    updateVlmSources({native_lines:[],source_sha256:""});
    state.reviews=[];showReviews();
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
  updateMassingSources(data);
  updateVlmSources(data);
  const findings=$("finding-list");clear(findings);
  findings.append(el("h3","Bulgular / değerlendirme adayları"));
  if(!data.findings.length) findings.append(el("p","Henüz bulgu yok; kaynak geometrisi HTML raporunda incelenebilir.","muted"));
  for(const f of data.findings.slice(0,35)) {
    const card=el("div","","finding");
    card.append(el("strong",f.check_id+" · "+f.status),el("small",f.reason_code+" · "+f.kind));
    findings.append(card);
  }
  if(data.truncated) findings.append(el("p","Ön izleme sayısı sınırlandırıldı; tam veri JSON raporundadır.","hint"));
  await loadReviews();
  await loadDxfEditStatus();
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
  state.selectedSource=null;
  $("save-review-note").disabled=true;
  $("edit-run").disabled=true;
  if(!frames.length) {
    frame.add(new Option("Kaynak çizgi bulunamadı",""));
    layer.add(new Option("Katman yok",""));
    summary.textContent="Seçili raporda SVG önizlemeye uygun kaynak-native çizgi bulunamadı.";
    return;
  }
  for(const name of frames) frame.add(new Option(name,name));
  function draw() {
    clear(svg);
    state.selectedSource=null;
    $("save-review-note").disabled=true;
    $("edit-run").disabled=true;
    inspector.textContent="Kaynak çizgi seçin; bu seçim orijinal dosyayı değiştirmez.";
    showReviews();
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
        state.selectedSource={...source,source_sha256:data.source_sha256||data.manifest?.source_sha256};
        $("save-review-note").disabled=false;
        const editable=source.origin==="CAD_NATIVE" && source.frame_id==="cad:Model" &&
          !!source.cad_handle && source.entity_id==="Model|"+source.cad_handle+"|LINE";
        for(const [id,value] of [["edit-start-x",source.points[0][0]],["edit-start-y",source.points[0][1]],
                                 ["edit-end-x",source.points[1][0]],["edit-end-y",source.points[1][1]]]) {
          $(id).value=editable?String(value):"";
        }
        $("edit-run").disabled=!editable || !state.editStatus || state.editStatus.head!=="original";
        showReviews();
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

function showReviews() {
  const panel=$("review-list");clear(panel);
  const current=state.selectedSource;
  const notes=(state.reviews||[]).filter(n=>!current||n.entity_id===current.entity_id);
  if(!notes.length) {
    panel.append(el("p","Bu kaynakta henüz manuel inceleme notu yok.","muted"));
    return;
  }
  for(const note of notes) {
    const card=el("div","","review-note");
    const title=el("strong",note.reviewer_label+" · "+
      (note.retracted_utc?"GERİ ALINDI":"DOĞRULANMAMIŞ GÖZLEM"));
    const detail=el("small",note.entity_id+" · "+note.created_utc);
    const body=el("p",note.note);
    card.append(title,detail,body);
    if(!note.retracted_utc) {
      const undo=el("button","Kaydı geri al","btn minor");
      undo.type="button";
      undo.addEventListener("click",()=>retractReview(note.review_id));
      card.append(undo);
    }
    panel.append(card);
  }
}
async function loadReviews() {
  const projectId=state.projectId,runId=state.runId;
  const obj=await api("/api/projects/"+projectId+"/runs/"+runId+"/reviews");
  if(projectId!==state.projectId||runId!==state.runId) return;
  state.reviews=obj.notes;
  showReviews();
}
async function saveReview() {
  const source=state.selectedSource;
  if(!source||!state.projectId||!state.runId) return notice("Önce kaynak çizgi seçin.",true);
  const reviewer=$("reviewer-input").value.trim(), note=$("review-note").value.trim();
  if(!reviewer||!note) return notice("İncelemeci etiketi ve inceleme notu zorunludur.",true);
  $("save-review-note").disabled=true;
  try {
    await api("/api/projects/"+state.projectId+"/runs/"+state.runId+"/reviews",{
      method:"POST",headers:{"Content-Type":"application/json"},
      body:JSON.stringify({
        source_sha256:source.source_sha256,
        entity_id:source.entity_id,frame_id:source.frame_id,
        reviewer_label:reviewer,note
      })
    });
    $("review-note").value="";
    await loadReviews();
    notice("Kaynaklı manuel gözlem kaydedildi; hukukî/teknik onay değildir.");
  } catch(e) {notice(e.message,true);}
  finally {$("save-review-note").disabled=!state.selectedSource;}
}
async function retractReview(reviewId) {
  try {
    await api("/api/projects/"+state.projectId+"/runs/"+state.runId+"/reviews/"+reviewId,
              {method:"DELETE"});
    await loadReviews();
    notice("İnceleme notu geri alındı; kayıt denetim izi için saklanıyor.");
  } catch(e) {notice(e.message,true);}
}


async function loadDxfEditStatus() {
  state.editStatus=null;
  $("edit-run").disabled=true;
  $("edit-undo").disabled=true;
  clear($("edit-download"));
  const project=state.projects.find(x=>x.project_id===state.projectId);
  if(!project || project.source_kind!=="DXF") {
    $("edit-status").textContent="DXF kaynağı seçildiğinde düzenleme kullanılabilir.";
    return;
  }
  const projectId=state.projectId;
  try {
    const status=await api("/api/projects/"+projectId+"/edits");
    if(projectId!==state.projectId) return;
    state.editStatus=status;
    const latest=status.history.at(-1);
    $("edit-status").textContent=status.head==="original"?
      "Özgün DXF aktif · Kaynak çizgi seçin. Henüz revizyon oluşturulmadı.":
      "Son revizyon: "+status.head.slice(0,12)+"… · "+
       status.history.length+" kayıt. Önizleme hâlâ özgün çizimi gösterir.";
    $("edit-undo").disabled=!latest || latest.operation!=="MOVE_LINE";
    const src=state.selectedSource;
    $("edit-run").disabled=!src || src.origin!=="CAD_NATIVE" || src.frame_id!=="cad:Model" ||
      !src.cad_handle || src.entity_id!=="Model|"+src.cad_handle+"|LINE" || status.head!=="original";
    if(status.head!=="original") {
      const link=el("a","Son revizyon DXF dosyasını indir ↗");
      link.href="/api/projects/"+projectId+"/edits/"+status.head+"/download";
      link.download="MimarLLM-"+status.head+".dxf";
      $("edit-download").append(link);
    }
  }catch(e) {
    $("edit-status").textContent="DXF revizyon geçmişi okunamadı: "+e.message;
    $("edit-undo").disabled=true;
  }
}
async function commitDxfEdit() {
  const source=state.selectedSource,head=state.editStatus,projectId=state.projectId;
  if(!source||!head||head.head!=="original"||source.origin!=="CAD_NATIVE"||
    source.frame_id!=="cad:Model"||!source.cad_handle) {
    return notice("Yalnız özgün doğrudan Model LINE kaynağı düzenlenebilir.",true);
  }
  const fields=["edit-start-x","edit-start-y","edit-end-x","edit-end-y"];
  if(fields.some(id=>$(id).value.trim()===""))return notice("Dört CAD koordinatı da gerekli.",true);
  const coords=fields.map(id=>Number($(id).value));
  if(coords.some(n=>!Number.isFinite(n)||Math.abs(n)>1e6))return notice("CAD koordinatları geçersiz.",true);
  const label=$("reviewer-input").value.trim();
  if(!label)return notice("İncelemeci etiketi gerekli.",true);
  $("edit-run").disabled=true;
  try {
    const result=await api("/api/projects/"+projectId+"/edits",{
      method:"POST",headers:{"Content-Type":"application/json"},
      body:JSON.stringify({
        source_sha256:head.original_sha256,expected_head:head.head,
        expected_sha256:head.head_sha256,
        entity_id:source.entity_id,frame_id:source.frame_id,
        cad_handle:source.cad_handle,expected_start:source.points[0],
        expected_end:source.points[1],
        new_start:coords.slice(0,2),new_end:coords.slice(2,4),
        reviewer_label:label
      })
    });
    notice("Yeni DXF revizyonu kaydedildi: "+result.revision_id.slice(0,12)+"… Orijinal korundu.");
    await loadDxfEditStatus();
  }catch(e){notice(e.message,true);await loadDxfEditStatus();}
}
async function undoDxfEdit() {
  const current=state.editStatus;
  if(!current||current.head==="original") return notice("Geri alınacak DXF revizyonu yok.",true);
  $("edit-undo").disabled=true;
  try {
    const result=await api("/api/projects/"+state.projectId+"/edits/undo",{
      method:"POST",headers:{"Content-Type":"application/json"},
      body:JSON.stringify({
        source_sha256:current.original_sha256,
        expected_head:current.head,expected_sha256:current.head_sha256
      })
    });
    notice("Son düzenleme geri alındı. Geri alınmış DXF revizyonu ayrıca saklandı: "+result.revision_id.slice(0,12)+"…");
    await loadDxfEditStatus();
  }catch(e){notice(e.message,true);await loadDxfEditStatus();}
}


let activeMassingModule=null;
function clearMassing() {
  activeMassingModule?.clearMassing();
  const scene=$("massing-canvas");clear(scene);
  scene.append(el("p","Henüz 2.5D senaryosu yok. Kaynak çizime veya analize dokunulmadı.","muted"));
  $("massing-evidence").textContent="Orijinal CAD/DrawingIR/rapor değişmedi.";
}
function updateMassingSources(data) {
  clearMassing();
  const frame=$("massing-frame"),list=$("massing-source-list");
  clear(frame);clear(list);
  const sources=Array.isArray(data.native_lines)?data.native_lines.filter(s=>
    s.origin==="CAD_NATIVE"&&s.frame_id==="cad:Model"&&
    s.cad_handle&&s.entity_id==="Model|"+s.cad_handle+"|LINE"):[];
  state.massingSources=sources;
  state.massingSha=data.source_sha256||"";
  frame.add(new Option(sources.length?"cad:Model — yalnız native LINE":"Uygun kaynak sınır bulunamadı",
                       sources.length?"cad:Model":""));
  $("massing-build").disabled=!sources.length;
  $("massing-status").textContent=sources.length ?
    "Yalnız seçili direkt LINE elemanları ve doğrulanmış kalibrasyonla önizleme üretilir.":
    "Önce yerel DXF analizi ve native sınır çizgileri gerekli.";
  if(!sources.length){
    list.append(el("p","Bu analizde kaynaklı doğrudan Model LINE bulunamadı.","muted"));return;
  }
  for(const src of sources) {
    const label=el("label"),box=el("input");
    box.type="checkbox";box.value=src.entity_id;box.className="massing-source-check";
    label.append(box,el("span",(src.layer||"Katmansız")+" · handle "+src.cad_handle+
       " · "+src.entity_id));
    list.append(label);
  }
}
async function buildMassing() {
  if(!state.projectId||!state.runId||!state.massingSha){
    return notice("Önce bir DXF analizini seçin.",true);
  }
  const checked=[...document.querySelectorAll(".massing-source-check:checked")].map(x=>x.value);
  if(checked.length<3||checked.length>64)return notice("3–64 adet tam kapalı sınır çizgisi seçilmelidir.",true);
  const raw=$("massing-height").value.trim().replace(",",".");
  if(!raw)return notice("Pozitif metre cinsinden kullanıcı yüksekliği beyan edin.",true);
  const height=Number(raw),reviewer=$("massing-reviewer").value.trim();
  if(!Number.isFinite(height)||height<=0||height>150||!reviewer){
    return notice("0–150 m aralığında yükseklik ve incelemeci etiketi gereklidir.",true);
  }
  const pid=state.projectId,rid=state.runId;
  $("massing-build").disabled=true;
  clearMassing();
  $("massing-status").textContent="Kapalı sınır, kaynak SHA ve fiziksel kalibrasyon doğrulanıyor…";
  try{
    const result=await api("/api/projects/"+pid+"/runs/"+rid+"/massing25d",{
      method:"POST",headers:{"Content-Type":"application/json"},
      body:JSON.stringify({
        source_sha256:state.massingSha,frame_id:"cad:Model",
        source_entity_ids:checked,declared_height_m:height,reviewer_label:reviewer,
      }),
    });
    if(pid!==state.projectId||rid!==state.runId)return;
    // Local import: THREE module and all subimports must be provided by onedir/static.
    const visualizer=await import("/static/scene25d.js");
    if(pid!==state.projectId||rid!==state.runId)return;
    activeMassingModule=visualizer;
    visualizer.showMassing($("massing-canvas"),result,provenance=>{
      $("massing-evidence").textContent=[
        "2.5D önizleme kaynağı:",provenance.source_sha256,
        "Frame: "+provenance.frame_id,
        "Face: "+provenance.face_id,
        "Orijinal CAD çizgileri: "+provenance.entity_ids.join(", "),
        "Statü: UNVERIFIED_MASSING_SCENARIO · Hukukî HOLD",
      ].join("\n");
    });
    $("massing-evidence").textContent=[
      "SHA256: "+result.source_sha256,
      "Frame / face: "+result.frame_id+" / "+result.face_id,
      "CAD handle'lar: "+result.source_cad_handles.join(", "),
      "Ölçek kanıtı: "+result.calibration_evidence_ids.join(", "),
      "Beyan yüksekliği: "+result.declared_height_m+" m (gerçek bina değeri değil)",
      "Kütle taban alanı matematiksel senaryo: "+result.footprint_area_m2+" m²",
      "Durum: "+result.status+" · "+result.legal_gate,
    ].join("\n");
    $("massing-status").textContent=
      "Kaynak bağlantılı 2.5D önizleme hazır; gerçek bina veya ruhsat onayı değildir.";
  }catch(e){
    clearMassing();
    $("massing-status").textContent="Önizleme üretilemedi: "+e.message;
    notice(e.message,true);
  }finally{
    $("massing-build").disabled=!state.massingSources.length;
  }
}


function clearVlm() {
  clear($("vlm-results"));
  $("vlm-results").append(el("p","Henüz yerel model yorum adayı yok.","muted"));
}
function vlmReady() {
  $("vlm-infer").disabled = !state.vlmConfigured || !state.vlmSha ||
      !state.vlmLines.length || !state.projectId || !state.runId ||
      !$("vlm-opt-in").checked || state.vlmRunning;
}
function vlmFrameChanged() {
  const chosen=$("vlm-source-frame").value,list=$("vlm-line-select");
  clear(list);clearVlm();
  const lines=state.vlmLines.filter(s=>s.frame_id===chosen);
  if(!lines.length) {
    list.append(el("p","Bu sayfada kaynak LINE bulunamadı.","muted"));
    vlmReady();return;
  }
  for(const line of lines) {
    const label=el("label"),checkbox=el("input");
    checkbox.type="checkbox";
    checkbox.className="vlm-source-check";
    checkbox.value=line.entity_id;
    label.append(checkbox,el("span",line.frame_id+" · "+(line.layer||"Katmansız")+
      " · "+(line.cad_handle||line.entity_id)));
    list.append(label);
  }
  vlmReady();
}
function updateVlmSources(data) {
  state.vlmSha=data.source_sha256||"";
  state.vlmLines=Array.isArray(data.native_lines)?
    data.native_lines.filter(s=>["CAD_NATIVE","PDF_NATIVE"].includes(s.origin) &&
      ["cad:Model",s.frame_id].includes(s.frame_id) &&
      Array.isArray(s.points) && s.points.length===2):[];
  $("vlm-opt-in").checked=false;
  const frame=$("vlm-source-frame");clear(frame);
  const frames=[...new Set(state.vlmLines.map(s=>s.frame_id))].sort();
  if(!frames.length)frame.add(new Option("Önce kaynak LINE içeren analiz seçin",""));
  else for(const id of frames)frame.add(new Option(id,id));
  vlmFrameChanged();
}
async function loadVlmAvailability() {
  try {
    const status=await api("/api/vlm/status");
    state.vlmConfigured=!!status.configured;
    $("vlm-config-status").textContent=status.configured ?
      "Yerel model yapılandırması mevcut. Model/VRAM doğrulaması çalıştırma sırasında yapılır.":
      "Yerel model henüz yapılandırılmadı. Deterministik DXF/PDF analizi bundan etkilenmez.";
  } catch (e) {
    state.vlmConfigured=false;
    $("vlm-config-status").textContent="Yerel VLM kullanılamıyor: "+e.message;
  }
  vlmReady();
}
async function inferVlm() {
  if(!state.vlmConfigured || !state.projectId || !state.runId ||
     !$("vlm-opt-in").checked) {
    return notice("Yerel model yapılandırması ve açık VLM onayı gerekir.",true);
  }
  const ids=[...document.querySelectorAll(".vlm-source-check:checked")].map(x=>x.value);
  const question=$("vlm-question").value.trim();
  const reviewer=$("vlm-reviewer").value.trim();
  if(!ids.length || ids.length>48 || !question || question.length>320 || !reviewer) {
    return notice("1–48 kaynak çizgi, kısa soru ve incelemeci etiketi gerekli.",true);
  }
  const projectId=state.projectId,runId=state.runId,sha=state.vlmSha,
        frame=$("vlm-source-frame").value;
  clearVlm();state.vlmRunning=true;vlmReady();
  $("vlm-status").textContent="Yerel GGUF/MMProj başlatılıyor. Sonuç yalnız onaysız yorum adayı olacaktır.";
  try {
    const result=await api("/api/projects/"+projectId+"/runs/"+runId+"/vlm/suggest",{
      method:"POST",headers:{"Content-Type":"application/json"},
      body:JSON.stringify({
        source_sha256:sha,frame_id:frame,entity_ids:ids,
        question,reviewer_label:reviewer
      })
    });
    if(projectId!==state.projectId || runId!==state.runId)return;
    if(result.status!=="UNVERIFIED_VLM_SUGGESTION" ||
       result.source_sha256!==sha || result.legal_gate!=="REGULATORY_LOCKED") {
      throw new Error("Model yanıtı kaynak veya güvenlik statüsüne uymuyor.");
    }
    const list=$("vlm-results");clear(list);
    list.append(el("p","KAYNAK SHA: "+result.source_sha256+
      " · "+result.execution_mode+" · YALNIZ ONAYSIZ YORUM","hint"));
    if(!result.suggestions.length) list.append(el("p","Model temkinli biçimde aday bildirmedi.","muted"));
    for(const candidate of result.suggestions){
      const item=el("article","","review-item");
      item.append(el("strong",candidate.kind+" · İNCELEME GEREKLİ"),
        el("p",candidate.commentary),
        el("small","Özgün çizgi kimlikleri: "+candidate.entity_ids.join(", ")));
      list.append(item);
    }
    $("vlm-status").textContent="Yerel model yorumu alındı; doğrulanmış mimari sonuç değildir.";
  }catch(e){
    $("vlm-status").textContent="Yerel VLM adayı üretilmedi: "+e.message;
    notice("VLM çalıştırılamadı; mevcut analiz ve rapor korundu.",true);
  }finally{
    state.vlmRunning=false;vlmReady();
  }
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
    await loadVlmAvailability();
  }catch(e){notice("Yerel uygulama başlatılamadı: "+e.message,true);}
}
$("upload-button").addEventListener("click",upload);
$("refresh-button").addEventListener("click",()=>refresh().catch(e=>notice(e.message,true)));
$("analyze-button").addEventListener("click",analyze);
$("save-review-note").addEventListener("click",saveReview);
$("edit-run").addEventListener("click",commitDxfEdit);
$("edit-undo").addEventListener("click",undoDxfEdit);
$("massing-build").addEventListener("click",buildMassing);
$("massing-clear").addEventListener("click",clearMassing);
$("vlm-source-frame").addEventListener("change",vlmFrameChanged);
$("vlm-opt-in").addEventListener("change",vlmReady);
$("vlm-infer").addEventListener("click",inferVlm);
$("vlm-clear").addEventListener("click",clearVlm);
$("selected-project").addEventListener("change",e=>chooseProject(e.target.value).catch(x=>notice(x.message,true)));
$("drawing-file").addEventListener("change",e=>{
  const file=e.target.files?.[0];$("picked-file").textContent=file?file.name+" · "+(file.size/1024/1024).toFixed(2)+" MB":"Henüz dosya seçilmedi.";
});
start();
