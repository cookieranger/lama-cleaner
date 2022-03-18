#!/usr/bin/env python3

import argparse
import multiprocessing
import os
import time

import numpy as np
import nvidia_smi
import psutil
import torch
from tqdm import tqdm

from lama_cleaner.lama import LaMa

try:
    torch._C._jit_override_can_fuse_on_cpu(False)
    torch._C._jit_override_can_fuse_on_gpu(False)
    torch._C._jit_set_texpr_fuser_enabled(False)
    torch._C._jit_set_nvfuser_enabled(False)
except:
    pass

from lama_cleaner.helper import norm_img

NUM_THREADS = str(4)

os.environ["OMP_NUM_THREADS"] = NUM_THREADS
os.environ["OPENBLAS_NUM_THREADS"] = NUM_THREADS
os.environ["MKL_NUM_THREADS"] = NUM_THREADS
os.environ["VECLIB_MAXIMUM_THREADS"] = NUM_THREADS
os.environ["NUMEXPR_NUM_THREADS"] = NUM_THREADS
if os.environ.get("CACHE_DIR"):
    os.environ["TORCH_HOME"] = os.environ["CACHE_DIR"]


def run_model(model, size):
    # RGB
    image = np.random.randint(0, 256, (size[0], size[1], 3)).astype(np.uint8)
    image = norm_img(image)

    mask = np.random.randint(0, 255, size).astype(np.uint8)
    mask = norm_img(mask)
    model(image, mask)


def benchmark(model, times: int, empty_cache: bool):
    sizes = [
        (512, 512),
        (640, 640),
        (1080, 800),
        (2000, 2000)
    ]

    nvidia_smi.nvmlInit()
    device_id = 0
    handle = nvidia_smi.nvmlDeviceGetHandleByIndex(device_id)

    def format(metrics):
        return f"{np.mean(metrics):.2f} ± {np.std(metrics):.2f}"

    process = psutil.Process(os.getpid())
    # 每个 size 给出显存和内存占用的指标
    for size in sizes:
        torch.cuda.empty_cache()
        time_metrics = []
        cpu_metrics = []
        memory_metrics = []
        gpu_memory_metrics = []
        for _ in range(times):
            start = time.time()
            run_model(model, size)
            torch.cuda.synchronize()
            if empty_cache:
                torch.cuda.empty_cache()

            # cpu_metrics.append(process.cpu_percent())
            time_metrics.append((time.time() - start) * 1000)
            memory_metrics.append(process.memory_info().rss / 1024 / 1024)
            gpu_memory_metrics.append(nvidia_smi.nvmlDeviceGetMemoryInfo(handle).used / 1024 / 1024)

        print(f"size: {size}".center(80, "-"))
        # print(f"cpu: {format(cpu_metrics)}")
        print(f"latency: {format(time_metrics)}ms")
        print(f"memory: {format(memory_metrics)} MB")
        print(f"gpu memory: {format(gpu_memory_metrics)} MB")

    nvidia_smi.nvmlShutdown()


def get_args_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument("--device", default="cuda", type=str)
    parser.add_argument("--times", default=20, type=int)
    parser.add_argument("--empty-cache", action="store_true")
    return parser.parse_args()


if __name__ == "__main__":
    args = get_args_parser()
    device = torch.device(args.device)
    model = LaMa(device)
    benchmark(model, args.times, args.empty_cache)
