# Presenter Guide: Live Visual Demonstration
## Autonomous Fleet Edge Data Triage & Golden Data Set (GDS) Reduction

This guide provides a structured, 5-minute narrative script and operational walkthrough for presenting the **Enterprise Edge Data Triage & Deduplication Engine** to mining executives, autonomy engineering leads, and cloud platform architects.

---

## 1. Executive Context & The Narrative Arc

### The Persona
You are presenting as the **Autonomous Systems & Edge Infrastructure Architect**.

### The 3-Act Story
1. **Act I: The Data Avalanche (The Problem)**  
   An autonomous haul fleet operating 24/7 in an open-pit mine (e.g. *Pilbara Cell 04*) generates **~500 TB/day** of dense LiDAR point clouds, radar, CAN-bus, and 4K camera streams. Satellite (Starlink) and 4G/5G edge bandwidth cannot ship 500 TB/day to AWS or cloud object stores, and storing un-curated routine data wastes millions of dollars annually.
2. **Act II: The Safety Incident on -9% Grade (The Dramatic Hook)**  
   During a routine haul shift, autonomous 400-ton haul truck `HT_402_400T` (`EVT_F1_AEB_DOWNHILL_001`) encounters an obstacle while descending a steep **-9% pitch grade**. Forward Time-to-Collision (TTC) plummets, and **Autonomous Emergency Braking (AEB)** engages. Simultaneously, other fleet trucks generate nominal, uneventful haul cycles, and another truck encounters the same intersection 3 minutes later.
3. **Act III: Edge Triage & The Visual Proof (The Payoff)**  
   Running on Red Hat OpenShift directly at the edge offload dock, our 6-filter triage engine:
   - Immediately detects the -9% grade AEB event and classifies it **Tier 1 Forensic** (uncapped quota, zero data loss).
   - Activates in-container FFmpeg to slice the exact **10-second temporal window** ($T-5\text{s}$ to $T+5\text{s}$) around the brake trigger, decimating it from 30 FPS to 10 FPS H.264 MP4 (slashing video footprint by ~85% while preserving full forensic fidelity).
   - Suppresses duplicate sensor frames from following trucks via **Spatiotemporal Coreset Deduplication (Filter 6)**.
   - Discards nominal empty road data at the edge.
   - **The Bottom Line:** Achieves a **~95% reduction** in transferred data volume (~113 MB raw ingested $\rightarrow$ ~5.1 MB curated across 8 high-entropy packages and 2 video clips; 98%+ at production scale) while preserving 100% of safety-critical evidence.

---

## 2. Pre-Demo Setup (2 Minutes Before Demo)

Open two terminal windows side-by-side on your screen:

```
+------------------------------------------+------------------------------------------+
| Terminal 1: Dual-Stream Log Monitor      | Terminal 2: Simulator & Commands         |
| python3 demo/scripts/stream_demo.py      | oc apply -f demo/k8s/05_simulator_job... |
+------------------------------------------+------------------------------------------+
| Browser Tab: OpenShift Web Dashboard (https://edge-triage-dashboard-...)           |
+-------------------------------------------------------------------------------------+
```

### Run the Prep Script in Terminal 2:
```bash
bash demo/scripts/prep_demo.sh
```
*The prep script will clean previous runs, verify worker pod health, and print your live OpenShift Web Dashboard URL.*

Copy the printed URL and open it in a browser window placed next to your terminals.

---

## 3. Step-by-Step 5-Minute Presentation Script

### [Minute 0:00 - 1:00] The Challenge & The Cost

> *"Welcome everyone. Today we're showing how we solve the multi-petabyte data dilemma for autonomous heavy equipment.*
>
> *In mining and heavy logistics, a single fleet of 400-ton autonomous trucks produces up to 500 terabytes of multi-sensor telemetry every day. Most of this data is nominal—flat roads, repetitive cycles. But when a critical event occurs—like emergency braking on an active haul ramp—we cannot afford to lose a single frame of forensic telemetry.*
>
> *Shipping 500 TB/day to the cloud over remote mining connectivity is physically impossible and cost-prohibitive. What you see on screen is our Edge Data Triage Engine running on Red Hat OpenShift right at the edge docking station."*

---

### [Minute 1:00 - 2:00] Starting the Ingest & Live Log Streaming

In **Terminal 1**, start the live dual-stream monitor:
```bash
python3 demo/scripts/stream_demo.py
```

In **Terminal 2**, launch the 100-event fleet simulator:
```bash
oc apply -f demo/k8s/05_simulator_job.yaml
```

> *"I've just simulated a vehicle offload session: 100 realistic multi-channel packages totaling ~108 MB, containing 9 sensor streams—LiDAR, radar, CAN telemetry, and rolling 30-second 30 FPS camera feeds.*
>
> *Notice Terminal 1: The cyan lines show the simulator offloading raw MCAP packages into our shared edge storage volume (`/mnt/raw_ingest`). Our triage worker detects each completed transfer and immediately evaluates it against our 6-filter information entropy funnel."*

---

### [Minute 2:00 - 3:15] Real-Time Filter Decisions & Video Slicing

Direct the audience's attention to the color-coded logs streaming in **Terminal 1**:

> *1. **The Safety Incident (Bright Red):** Look at `EVT_F1_AEB_DOWNHILL_001`. The kinematic filter caught the -9% grade emergency brake trigger and promoted it to Tier 1 Forensic. It triggered in-container FFmpeg to slice the critical 10-second window ($T-5\text{s}$ to $T+5\text{s}$) and downsample from 30 FPS to 10 FPS.*
>
> *2. **Model Uncertainty (Yellow):** `EVT_F2_DUST_UNCERTAINTY_002` triggered Tier 2 because perception confidence dropped and Shannon entropy spiked due to airborne dust.*
>
> *3. **Unsupervised Novelty (Magenta):** `EVT_F3_NOVEL_HAUL_ROAD_003` was detected by our SIMD-accelerated USearch vector index running directly on edge CPU without requiring costly GPU hardware.*
>
> *4. **Deduplication (Green):** `EVT_F6_INTERSECTION_DUPLICATE_004B` was suppressed by Filter 6 because another truck encountered the exact same obstacle 15 meters away 3 minutes earlier.*
>
> *5. **Nominal Discard (Dim Gray):** Notice all the gray lines—routine haul cycles are safely purged from the raw buffer, saving our edge storage and network bandwidth.*

---

### [Minute 3:15 - 4:15] The Visual Payoff: OpenShift Web Dashboard

Switch to the **Browser Window**:

> *"Now let's look at the results on our live OpenShift Dashboard:*
>
> * Look at the **Bandwidth Reduction Gauge**: We ingested **~113 MB** of raw telemetry across 100 offload events, and our curated Golden Data Set is only **~5.1 MB** (8 high-value events + 2 forensic video clips)—a **~95% reduction** in network payload achieved in seconds!
> * Every single event was evaluated in sub-millisecond to low-millisecond latency (with FFmpeg video slicing completing in ~150ms).
>
> *Now, let's verify the forensic evidence. Right here in the dashboard, I can click on **EVT_F1_AEB_DOWNHILL_001** and press play:*
>
> *(Play the 10-second video clip directly in the browser)*
>
> *The safety investigator can watch the exact 10 seconds of the downhill emergency braking maneuver. We didn't keep the full 30-second raw file, but we didn't lose any critical context. The video was downsampled to 10 FPS H.264, slashing its size from 1.26 MB down to ~190 KB."*

---

### [Minute 4:15 - 5:00] Enterprise Governance & Production Scale

> *"Finally, how does this scale across an entire enterprise?*
>
> * **Red Hat Advanced Cluster Management (RHACM):** The triage policies you saw are declarative ConfigMaps. An autonomy engineer at headquarters can tune novelty thresholds in Git, and RHACM automatically enforces the policy across 50 mining pits worldwide.*
> * **Vendor-Neutral Storage:** Our storage claims are decoupled. Here in AWS ROSA, we're backed by AWS EFS CSI (`efs-sc`). On-prem at the mine site, the exact same containers bind to NetApp ONTAP NVMe arrays with Astra Trident CSI.*
>
> *In summary: we've eliminated ~95% of edge data waste in this demo (98%+ at production scale), cut cloud costs, and preserved 100% of our safety-critical intelligence. Thank you, and I'd be happy to take questions."*

---

## 4. Presenter Q&A Cheat Sheet

| Question | Authoritative Answer |
| :--- | :--- |
| **"What happens if network drops during offload?"** | Ingestion uses atomic handshake markers (`.ready` sidecars and an mtime settle buffer $\ge 2\text{s}$). Partial files are never read or purged prematurely. |
| **"Why decimate to 10 FPS instead of 30 FPS?"** | Automotive safety investigations need kinematic sync (CAN-bus + brake state at 100 Hz), but human visual inspection and perception re-training are fully satisfied by 10 FPS keyframes, saving 66% of video storage. In production, `VIDEO_STREAM_COPY=true` can also do zero-CPU keyframe GOP slicing. |
| **"Does USearch require an NVIDIA GPU?"** | No. USearch uses SIMD vector instructions (AVX-512 / AVX2 / NEON) on standard edge x86/ARM CPUs. Cosine distance queries across 128 dimensions execute in sub-millisecond latency without needing a dedicated GPU. |
| **"How is the Web Dashboard deployed?"** | It is served directly from the worker pod's metrics port (8080) and exposed publicly via an OpenShift Route with TLS edge termination. No additional node or external load balancer is required. |
