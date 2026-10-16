// Process 026: an explicitly prepared local JS asset, never a CDN at runtime.
// Build: npm install --no-audit --no-fund --ignore-scripts (preparation only).
// Verify (no npm/network): node scripts/build_three_vendor_026.mjs --verify
import {createHash} from "node:crypto";
import {readFileSync,copyFileSync,renameSync,rmSync,existsSync,writeFileSync,mkdirSync} from "node:fs";
import {resolve,dirname} from "node:path";

const root=resolve(import.meta.dirname,"..");
const modulePath=resolve(root,"node_modules/three/build/three.module.js");
const metadataPath=resolve(root,"node_modules/three/package.json");
const output=resolve(root,"src/mimarllm/app/static/three.module.js");
const manifest=resolve(root,"src/mimarllm/app/static/three-vendor-026.json");
const expected="0.160.1";
const verify=process.argv.includes("--verify");
const digest=bytes=>createHash("sha256").update(bytes).digest("hex");

if(!verify){
  if(!existsSync(modulePath)||!existsSync(metadataPath)){
    throw Error("Three.js source missing; prepare three@0.160.1 explicitly before offline packaging");
  }
  const metadata=JSON.parse(readFileSync(metadataPath,"utf8"));
  if(metadata.version!==expected||metadata.name!=="three"){
    throw Error("Three.js version mismatch; refuse unreviewed vendor");
  }
  const bytes=readFileSync(modulePath);
  if(bytes.length<200_000||bytes.length>3_000_000)throw Error("Unexpected Three.js ESM size");
  mkdirSync(dirname(output),{recursive:true});
  const temp=output+".tmp";
  try{
    copyFileSync(modulePath,temp);
    renameSync(temp,output);
  }finally{rmSync(temp,{force:true});}
  writeFileSync(manifest,JSON.stringify({
    schema_version:1,version:expected,asset:"three.module.js",
    sha256:digest(bytes),size_bytes:bytes.length,
    origin:"LOCAL_NPM_PREPARATION_NOT_CDN_RUNTIME",
    license:"MIT_LICENSE_REVIEW_REQUIRED",
  },null,2)+"\n");
}
if(!existsSync(output)||!existsSync(manifest)){
  throw Error("Local Three.js ESM and SHA manifest required. Runtime will not fetch a remote asset.");
}
const recorded=JSON.parse(readFileSync(manifest,"utf8"));
const bytes=readFileSync(output);
if(recorded.version!==expected||recorded.asset!=="three.module.js"||
   recorded.sha256!==digest(bytes)||recorded.size_bytes!==bytes.length){
  throw Error("Vendor SHA/size does not match recorded local Three.js asset");
}
console.log(JSON.stringify({version:recorded.version,sha256:recorded.sha256,size:bytes.length,verified:true}));
