#!/usr/bin/env python3
"""
stream_demo.py: Dual-Stream Live Log Runner for Edge Data Triage Demo.

Tails both the Fleet Telemetry Simulator and the Edge Triage Worker simultaneously
in real time with ANSI color highlighting and live event classification.
"""

import sys
import os
import time
import signal
import subprocess
import threading
from typing import Optional

# ANSI Color Codes
CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
MAGENTA = "\033[95m"
DIM = "\033[90m"
BOLD = "\033[1m"
RESET = "\033[0m"

running = True

def handle_sigint(sig, frame):
    global running
    print(f"\n{YELLOW}Stopping log streams...{RESET}")
    running = False
    sys.exit(0)

signal.signal(signal.SIGINT, handle_sigint)

def run_cmd(cmd_list: list) -> str:
    try:
        res = subprocess.run(cmd_list, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
        return res.stdout.strip()
    except Exception:
        return ""

def get_oc_binary() -> str:
    from shutil import which
    exe = which("oc")
    if exe:
        return exe
    candidate = os.path.expanduser("~/.local/bin/oc")
    if os.path.exists(candidate) and os.access(candidate, os.X_OK):
        return candidate
    return "oc"

def colorize_worker_line(line: str) -> str:
    """Applies contextual color highlights to triage worker log lines."""
    if "[VLM]" in line:
        return f"{MAGENTA}{BOLD}[OPENSHIFT AI VLM]{RESET} {CYAN}{BOLD}{line}{RESET}"
    elif "[PREDICTIVE MAINT]" in line:
        return f"{YELLOW}{BOLD}[PREDICTIVE MAINT]{RESET} {YELLOW}{line}{RESET}"
    elif "[OPS ADVISORY]" in line:
        return f"{CYAN}{BOLD}[HITL OPS ADVISORY]{RESET} {CYAN}{line}{RESET}"
    elif "Extracted" in line and "clip" in line:
        return f"{GREEN}{BOLD}[VIDEO EXTRACTION]{RESET} {GREEN}{line}{RESET}"
    elif "TIER_1_FORENSIC" in line or "AEB" in line or "ROLLOVER" in line:
        return f"{RED}{BOLD}[TIER-1 FORENSIC]{RESET} {RED}{line}{RESET}"
    elif "TIER_2_MODEL_UNCERTAINTY" in line or "DUST" in line:
        return f"{YELLOW}[TIER-2 UNCERTAINTY]{RESET} {YELLOW}{line}{RESET}"
    elif "TIER_3_FEATURE_NOVELTY" in line:
        return f"{MAGENTA}[TIER-3 NOVELTY]{RESET} {MAGENTA}{line}{RESET}"
    elif "Suppressed by Filter 6" in line or "DEDUP" in line:
        return f"{GREEN}{BOLD}[FILTER-6 DEDUP]{RESET} {GREEN}{line}{RESET}"
    elif "Discarded by Filters" in line or "nominal_discard" in line:
        return f"{DIM}[NOMINAL DISCARD] {line}{RESET}"
    elif "[Done] Curated" in line:
        return f"{CYAN}{BOLD}[CURATED]{RESET} {line}"
    return f"{CYAN}[WORKER]{RESET} {line}"

def stream_worker_logs(oc: str):
    """Streams live logs from the edge-triage-worker deployment."""
    cmd = [oc, "logs", "-l", "app.kubernetes.io/component=triage-worker", "-f", "--tail=20"]
    try:
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
        for line in iter(proc.stdout.readline, ''):
            if not running:
                break
            line_str = line.strip()
            if line_str:
                print(colorize_worker_line(line_str))
        proc.stdout.close()
        proc.wait()
    except Exception as err:
        if running:
            print(f"{DIM}[WORKER TAIL PAUSED: {err}]{RESET}")

def stream_simulator_logs(oc: str):
    """Streams live logs from the fleet telemetry simulator job."""
    print(f"{DIM}Waiting for simulator job to start...{RESET}")
    # Wait until a simulator pod appears
    sim_pod = ""
    while running and not sim_pod:
        sim_pod = run_cmd([oc, "get", "pods", "-l", "app.kubernetes.io/component=simulator", "-o", "jsonpath={.items[-1].metadata.name}"])
        if not sim_pod:
            time.sleep(1.0)

    if not running or not sim_pod:
        return

    print(f"{CYAN}{BOLD}[SIMULATOR CONNECTED]{RESET} Tailing {sim_pod}...")
    cmd = [oc, "logs", "-l", "app.kubernetes.io/component=simulator", "-f"]
    try:
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
        for line in iter(proc.stdout.readline, ''):
            if not running:
                break
            line_str = line.strip()
            if line_str:
                print(f"{CYAN}{BOLD}[SIMULATOR]{RESET} {line_str}")
        proc.stdout.close()
        proc.wait()
    except Exception as err:
        if running:
            print(f"{DIM}[SIMULATOR TAIL FINISHED: {err}]{RESET}")

def main():
    oc = get_oc_binary()
    project = run_cmd([oc, "project", "-q"]) or "active-project"
    route_host = run_cmd([oc, "get", "route", "edge-triage-dashboard", "-o", "jsonpath={.spec.host}"])
    dash_url = f"https://{route_host}" if route_host else "http://localhost:8080"

    print("=" * 80)
    print(f"{BOLD} Enterprise Edge Data Triage: Dual-Stream Live Monitor{RESET}")
    print(f" OpenShift Project:   {CYAN}{project}{RESET}")
    print(f" Live Web Dashboard:  {GREEN}{BOLD}{dash_url}{RESET}")
    print("=" * 80)
    print(f" Color Legend:")
    print(f"  {RED}{BOLD}[TIER-1 FORENSIC]{RESET} Kinematic Safety Incidents (AEB on -9% Grade, Reverse)")
    print(f"  {YELLOW}[TIER-2 UNCERTAINTY]{RESET} Perception Occlusions & Dust Clouds")
    print(f"  {MAGENTA}[TIER-3 NOVELTY]{RESET} USearch SIMD 128-D Cosine Anomaly Detections")
    print(f"  {GREEN}[FILTER-6 DEDUP]{RESET} Spatiotemporal Redundant Encounter Suppressions")
    print(f"  {GREEN}{BOLD}[VIDEO EXTRACTION]{RESET} In-Container FFmpeg 10s Temporal Slices (30->10 FPS)")
    print(f"  {MAGENTA}{BOLD}[OPENSHIFT AI VLM]{RESET} Multimodal Vision Root-Cause Analysis (Qwen2.5-VL-7B)")
    print(f"  {DIM}[NOMINAL DISCARD]{RESET} Routine Empty Haul Cycles Dropped at Edge")
    print("=" * 80)
    print(f"{YELLOW}Press Ctrl+C at any time to stop streaming.{RESET}\n")

    t_worker = threading.Thread(target=stream_worker_logs, args=(oc,), daemon=True)
    t_sim = threading.Thread(target=stream_simulator_logs, args=(oc,), daemon=True)

    t_worker.start()
    t_sim.start()

    while running:
        time.sleep(0.5)

if __name__ == "__main__":
    main()
