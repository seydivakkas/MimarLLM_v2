"""Operator-only local GGUF/MMProj setup; never exposed as browser API.

Example (explicit and offline, no automatic downloads):
python scripts/windows/configure_vlm_027.py --workspace <workspace> \
  --llama-server <local-binary> --model <weights.gguf> --mmproj <vision.gguf>
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
import os
from uuid import uuid4

from mimarllm.vlm.local_engine import LocalVlmConfig, _checked_file


def configure(workspace: Path, *, llama_server: Path, model: Path, mmproj: Path,
              gpu: bool, cpu_fallback: bool) -> Path:
    workspace=workspace.expanduser().resolve(strict=True)
    if not workspace.is_dir():
        raise ValueError("Workspace must exist; run a trusted local dashboard once first")
    payload={}
    for key,path,extension,max_bytes in [
        ("llama_server",llama_server,None,400_000_000),
        ("model",model,".gguf",40_000_000_000),
        ("mmproj",mmproj,".gguf",20_000_000_000),
    ]:
        path=path.expanduser()
        if not path.is_absolute() or path.is_symlink() or not path.is_file():
            raise ValueError("Only absolute, non-symlink, already downloaded local artifacts allowed")
        h=sha256()
        with path.open("rb") as fd:
            for part in iter(lambda:fd.read(1024*1024),b""):
                h.update(part)
        digest=h.hexdigest()
        _checked_file(path,digest,allowed_extension=extension,max_bytes=max_bytes)
        payload[key+"_path"]=path
        payload[key+"_sha256"]=digest
    config=LocalVlmConfig(
        **payload,gpu_requested=gpu,allow_cpu_fallback=cpu_fallback)
    target=workspace/"vlm-runtime.json"
    if target.is_symlink() or target.exists():
        raise ValueError("Existing model setup requires explicit removal and independent hash review")
    temp=workspace/("." + uuid4().hex + ".vlm-config-tmp")
    try:
        with temp.open("x",encoding="utf-8") as fd:
            fd.write(config.model_dump_json(indent=2))
        os.chmod(temp,0o600)
        os.replace(temp,target)
    finally:
        temp.unlink(missing_ok=True)
    return target


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--workspace",type=Path,required=True)
    parser.add_argument("--llama-server",type=Path,required=True)
    parser.add_argument("--model",type=Path,required=True)
    parser.add_argument("--mmproj",type=Path,required=True)
    parser.add_argument("--gpu",action="store_true")
    parser.add_argument("--no-cpu-fallback",action="store_true")
    args=parser.parse_args()
    result=configure(args.workspace,llama_server=args.llama_server,model=args.model,
                     mmproj=args.mmproj,gpu=args.gpu,cpu_fallback=not args.no_cpu_fallback)
    print(json.dumps({"status":"LOCAL_CONFIG_CREATED","filename":result.name,
                      "gpu_requested":args.gpu,"model_downloaded":False,
                      "legal_gate":"REGULATORY_LOCKED"}))


if __name__=="__main__":
    main()
