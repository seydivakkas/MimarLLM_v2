"use strict";
/* 026 — all THREE assets resolve on local /static; zero browser CDN requests.
   Render only server-verified source-bound UNVERIFIED_MASSING_SCENARIO. */
import * as THREE from "./three.module.js";

let disposePrevious = null;

export function clearMassing() {
  if (disposePrevious) { disposePrevious(); disposePrevious = null; }
}

export function showMassing(container, preview, onSelection) {
  clearMassing();
  if (!preview || preview.status !== "UNVERIFIED_MASSING_SCENARIO" ||
      preview.legal_gate !== "REGULATORY_LOCKED" ||
      !Array.isArray(preview.footprint_metres) ||
      preview.footprint_metres.length < 3 || preview.footprint_metres.length > 64 ||
      !Number.isFinite(preview.declared_height_m) ||
      preview.declared_height_m <= 0 || preview.declared_height_m > 150 ||
      preview.footprint_metres.some(p=>!Array.isArray(p)||p.length!==2||
         !p.every(n=>Number.isFinite(n)&&Math.abs(n)<=10000))) {
    throw new Error("Güvenilir 2.5D senaryo şeması yok.");
  }
  const shape = new THREE.Shape();
  const points = preview.footprint_metres;
  shape.moveTo(points[0][0],points[0][1]);
  for (const p of points.slice(1)) shape.lineTo(p[0],p[1]);
  shape.closePath();
  const geometry = new THREE.ExtrudeGeometry(shape,{
    depth:preview.declared_height_m,steps:1,bevelEnabled:false,
    curveSegments:1,
  });
  geometry.rotateX(-Math.PI/2);
  const material = new THREE.MeshStandardMaterial({
    color:0x688cab,roughness:0.87,metalness:0.05,
    side:THREE.DoubleSide,
  });
  const mesh = new THREE.Mesh(geometry,material);
  const edgesGeometry = new THREE.EdgesGeometry(geometry);
  const edges = new THREE.LineSegments(edgesGeometry,
                  new THREE.LineBasicMaterial({color:0x23405b}));
  const scene = new THREE.Scene();
  scene.background = new THREE.Color(0xf4f8fc);
  scene.add(mesh,edges);
  scene.add(new THREE.AmbientLight(0xffffff,1.5));
  const sun = new THREE.DirectionalLight(0xffffff,2);
  sun.position.set(12,28,22);
  scene.add(sun);
  const footprintWidth=Math.max(...points.map(p=>p[0]))-Math.min(...points.map(p=>p[0]));
  const footprintDepth=Math.max(...points.map(p=>p[1]))-Math.min(...points.map(p=>p[1]));
  const span=Math.max(footprintWidth,footprintDepth,preview.declared_height_m,1);
  const camera = new THREE.PerspectiveCamera(45,1,0.01,Math.max(2000,span*100));
  let azimuth=Math.PI/4, elevation=0.5, zoom=Math.max(5,span*2.5);
  const target = new THREE.Vector3(0,preview.declared_height_m/2,0);
  const ground = new THREE.GridHelper(Math.max(span*2,5),10,0xc8d7e4,0xe2eaf1);
  scene.add(ground);
  let renderer;
  try {
    renderer = new THREE.WebGLRenderer({antialias:true,alpha:false,powerPreference:"low-power"});
  } catch(error) {
    geometry.dispose();edgesGeometry.dispose();material.dispose();
    throw new Error("WebGL kullanılamıyor; 2B kaynak çizimi geçerli kalır.");
  }
  renderer.setPixelRatio(Math.min(window.devicePixelRatio||1,2));
  renderer.outputColorSpace=THREE.SRGBColorSpace;
  container.replaceChildren(renderer.domElement);
  renderer.domElement.setAttribute("role","img");
  renderer.domElement.setAttribute("aria-label","Kaynaklı, kullanıcı yüksekliği beyanlı 2.5D kütle önizlemesi");
  renderer.domElement.tabIndex=0;
  const aim=()=>{
    const r=Math.max(2,zoom);
    camera.position.set(target.x+r*Math.cos(elevation)*Math.sin(azimuth),
      target.y+r*Math.sin(elevation),
      target.z+r*Math.cos(elevation)*Math.cos(azimuth));
    camera.lookAt(target);
    renderer.render(scene,camera);
  };
  let disposed=false;
  const resize=()=>{
    if(disposed)return;
    const width=Math.max(10,container.clientWidth),height=Math.max(10,container.clientHeight);
    renderer.setSize(width,height,false);
    camera.aspect=width/height;camera.updateProjectionMatrix();aim();
  };
  let dragging=false,previousX=0,previousY=0;
  const down=e=>{dragging=true;previousX=e.clientX;previousY=e.clientY;
    renderer.domElement.setPointerCapture(e.pointerId);};
  const move=e=>{
    if(!dragging)return;
    azimuth-=(e.clientX-previousX)*0.009;
    elevation=Math.max(0.12,Math.min(1.43,elevation+(e.clientY-previousY)*0.009));
    previousX=e.clientX;previousY=e.clientY;aim();
  };
  const up=()=>{dragging=false;};
  const wheel=e=>{e.preventDefault();zoom=Math.max(span*0.8,Math.min(span*15,zoom*Math.exp(e.deltaY*0.001)));aim();};
  const key=e=>{
    if(!["ArrowLeft","ArrowRight","ArrowUp","ArrowDown","+","-"].includes(e.key))return;
    e.preventDefault();
    if(e.key==="ArrowLeft")azimuth-=0.12;
    if(e.key==="ArrowRight")azimuth+=0.12;
    if(e.key==="ArrowUp")elevation=Math.min(1.43,elevation+0.12);
    if(e.key==="ArrowDown")elevation=Math.max(0.12,elevation-0.12);
    if(e.key==="+")zoom=Math.max(span*0.8,zoom*0.9);
    if(e.key==="-")zoom=Math.min(span*15,zoom*1.1);
    aim();
  };
  const selected=()=>{
    if(typeof onSelection==="function"){
      onSelection({
        source_sha256:preview.source_sha256,frame_id:preview.frame_id,
        face_id:preview.face_id,entity_ids:preview.source_entity_ids,
        legal_gate:preview.legal_gate,
      });
    }
  };
  renderer.domElement.addEventListener("pointerdown",down);
  renderer.domElement.addEventListener("pointermove",move);
  renderer.domElement.addEventListener("pointerup",up);
  renderer.domElement.addEventListener("pointercancel",up);
  renderer.domElement.addEventListener("wheel",wheel,{passive:false});
  renderer.domElement.addEventListener("keydown",key);
  renderer.domElement.addEventListener("click",selected);
  const observer = typeof ResizeObserver==="function" ? new ResizeObserver(resize) : null;
  observer?.observe(container);
  resize();
  disposePrevious=()=>{
    disposed=true; observer?.disconnect();
    renderer.domElement.removeEventListener("pointerdown",down);
    renderer.domElement.removeEventListener("pointermove",move);
    renderer.domElement.removeEventListener("pointerup",up);
    renderer.domElement.removeEventListener("pointercancel",up);
    renderer.domElement.removeEventListener("wheel",wheel);
    renderer.domElement.removeEventListener("keydown",key);
    renderer.domElement.removeEventListener("click",selected);
    edges.material.dispose();edgesGeometry.dispose();material.dispose();geometry.dispose();
    renderer.dispose();renderer.domElement.remove();
  };
}
