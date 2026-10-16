"""Conservative, inspectable memory eligibility for opt-in local llama.cpp.

File sizes approximate weights; KV cache/projector/driver may demand more.
This is a PRE-FLIGHT GATE, NOT a guarantee or hardware certification.
"""
from __future__ import annotations

from math import ceil
from os import name as os_name
from pathlib import Path
import subprocess
import shutil
import sys
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class BudgetError(ValueError):
    pass


class HardwareSnapshot(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    available_ram_mib: int | None = Field(default=None, ge=0)
    available_vram_mib: int | None = Field(default=None, ge=0)
    gpu_probe: Literal["NVIDIA_SMI_SINGLE_DEVICE", "UNAVAILABLE"] = "UNAVAILABLE"


class RuntimeBudget(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    execution_mode: Literal["CPU_FALLBACK", "GPU_BUDGETED"]
    n_gpu_layers: int = Field(ge=0, le=99)
    model_plus_mmproj_mib: int = Field(gt=0)
    estimated_ram_required_mib: int = Field(gt=0)
    estimated_vram_required_mib: int = Field(ge=0)
    measured_available_ram_mib: int
    measured_available_vram_mib: int | None = None
    estimate_only: Literal[True] = True


def probe_hardware() -> HardwareSnapshot:
    """No internet or vendor SDK dependency; unknown hardware stays unknown."""
    ram: int | None = None
    if sys.platform.startswith("linux"):
        try:
            fields = Path("/proc/meminfo").read_text("ascii")
            for line in fields.splitlines():
                if line.startswith("MemAvailable:"):
                    ram = int(line.split()[1]) // 1024
                    break
        except (OSError, ValueError, IndexError):
            pass
    elif os_name == "nt":
        try:
            import ctypes

            class Memory(ctypes.Structure):
                _fields_ = [("dwLength", ctypes.c_ulong), ("dwMemoryLoad", ctypes.c_ulong),
                            ("ullTotalPhys", ctypes.c_ulonglong),
                            ("ullAvailPhys", ctypes.c_ulonglong),
                            ("ullTotalPageFile", ctypes.c_ulonglong),
                            ("ullAvailPageFile", ctypes.c_ulonglong),
                            ("ullTotalVirtual", ctypes.c_ulonglong),
                            ("ullAvailVirtual", ctypes.c_ulonglong),
                            ("ullAvailExtendedVirtual", ctypes.c_ulonglong)]
            data = Memory()
            data.dwLength = ctypes.sizeof(data)
            if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(data)):
                ram = int(data.ullAvailPhys // (1024 * 1024))
        except (AttributeError, OSError, ValueError):
            pass
    gpu: int | None = None
    probe: Literal["NVIDIA_SMI_SINGLE_DEVICE", "UNAVAILABLE"] = "UNAVAILABLE"
    nvidia = shutil.which("nvidia-smi")
    if nvidia:
        try:
            done = subprocess.run(
                [nvidia, "--query-gpu=memory.free", "--format=csv,noheader,nounits"],
                capture_output=True, text=True, timeout=3, check=False,
            )
            rows = [line.strip() for line in done.stdout.splitlines() if line.strip()]
            # Never silently choose device 0 in ambiguous multi-GPU configurations.
            if done.returncode == 0 and len(rows) == 1 and rows[0].isdigit():
                gpu = int(rows[0])
                probe = "NVIDIA_SMI_SINGLE_DEVICE"
        except (OSError, subprocess.TimeoutExpired):
            pass
    return HardwareSnapshot(
        available_ram_mib=ram, available_vram_mib=gpu, gpu_probe=probe,
    )


def plan_budget(
    model_bytes: int, mmproj_bytes: int, hardware: HardwareSnapshot,
    *, gpu_requested: bool, allow_cpu_fallback: bool = True,
    ram_reserve_mib: int = 1024, vram_reserve_mib: int = 1024,
) -> RuntimeBudget:
    if not 0 < model_bytes <= 40_000_000_000 or not 0 < mmproj_bytes <= 20_000_000_000:
        raise BudgetError("LOCAL_MODEL_FILE_SIZE_INVALID")
    if hardware.available_ram_mib is None:
        raise BudgetError("LOCAL_RAM_BUDGET_UNKNOWN")
    weights = ceil((model_bytes + mmproj_bytes) / (1024 * 1024))
    # Conservative total estimates, not a measured GPU peak. Model-specific
    # KV cache, CUDA buffers and multimodal patch counts vary substantially.
    cpu_required = ceil(weights * 1.35) + ram_reserve_mib + 512
    gpu_required = ceil(weights * 1.35) + vram_reserve_mib + 512
    gpu_ram_required = ceil(weights * 0.20) + ram_reserve_mib + 512
    if (gpu_requested and hardware.gpu_probe == "NVIDIA_SMI_SINGLE_DEVICE"
            and hardware.available_vram_mib is not None
            and hardware.available_vram_mib >= gpu_required
            and hardware.available_ram_mib >= gpu_ram_required):
        return RuntimeBudget(
            execution_mode="GPU_BUDGETED", n_gpu_layers=99,
            model_plus_mmproj_mib=weights,
            estimated_ram_required_mib=gpu_ram_required,
            estimated_vram_required_mib=gpu_required,
            measured_available_ram_mib=hardware.available_ram_mib,
            measured_available_vram_mib=hardware.available_vram_mib,
        )
    if not allow_cpu_fallback:
        raise BudgetError("LOCAL_GPU_MEMORY_UNAVAILABLE")
    if hardware.available_ram_mib < cpu_required:
        raise BudgetError("LOCAL_CPU_MEMORY_INSUFFICIENT")
    return RuntimeBudget(
        execution_mode="CPU_FALLBACK", n_gpu_layers=0,
        model_plus_mmproj_mib=weights,
        estimated_ram_required_mib=cpu_required,
        estimated_vram_required_mib=0,
        measured_available_ram_mib=hardware.available_ram_mib,
        measured_available_vram_mib=hardware.available_vram_mib,
    )
