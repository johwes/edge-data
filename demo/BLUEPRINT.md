# Edge Data Triage & Deduplication Blueprint
## Hello-World Implementation Guide for Red Hat OpenShift, NetApp Storage & RHACM

**Document Version:** 2.0  
**Status:** Approved Engineering Blueprint & Implementation Guide  
**Upstream Specifications:** [Spec 01: Data Filtering & Triage](../docs/01_data_filtering_and_triage.md) | [Spec 02: Data Reduction & Metadata](../docs/02_data_reduction_and_metadata_schema.md)  
**Target Environments:** Red Hat MicroShift (Lightweight CPU Edge) / Single Node OpenShift (SNO with GPU), NetApp ONTAP (via Astra Trident CSI), Red Hat Advanced Cluster Management (RHACM)

---

## 1. Executive Overview & Objective

This blueprint bridges the high-level system architecture defined in **Specification 01 (Data Filtering, Triage & Deduplication)** and **Specification 02 (Data Reduction & Metadata Schema)** into an actionable, containerized "Hello World" application ready for deployment on Red Hat OpenShift, NetApp Storage, and RHACM.

### 1.1 The Business & Network Bottleneck
Industrial autonomous haulage operations (e.g., Cat 797F, Komatsu 930E) generate between 3.0 and 5.0 TB of uncompressed multi-modal sensor data per vehicle per 24-hour shift (35–60 MB/s). Across a 100-truck fleet, aggregate daily generation scales to approximately 500 TB. 

However, remote extraction sites (Western Australia's Pilbara, Chile's Atacama Desert) lack terrestrial fiber, relying on commercial LEO satellite uplinks (Starlink Business / OneWeb) delivering 10–25 Mbps sustained uplink. This limits cumulative site egress to **100–250 GB/day for the entire site**, with an allocated budget of **10–20 GB/day per 10-truck operational cell** (yielding ~3.5 to 7.0 GB/day nominal upload post-deduplication). Over 99.9% of raw sensor data cannot physically leave the site.

### 1.2 The Platform Value Proposition
By deploying an intelligent edge triage and deduplication workload onto **Red Hat OpenShift at the Edge**, backed by **NetApp Enterprise Storage**, and governed centrally via **Red Hat Advanced Cluster Management (RHACM)**, industrial operators can:
1. **Filter 95%+ of low-entropy nominal driving** directly at edge station pods before data hits the WAN.
2. **Eliminate 60%–80% of repetitive cross-fleet scenes** via spatial-temporal coreset deduplication.
3. **Preserve 100% of safety-critical events and operational anomalies** in a standardized, low-overhead catalog (`gds_metadata_v2.json`).
4. **Reduce recurring cloud storage and labeling costs by over 99%**, replacing unmanaged multi-petabyte cloud floods ($345k+/mo) with a curated Golden Data Set (GDS) ($10–$35/mo).

---

## 2. Target Platform & Infrastructure Architecture

```mermaid
flowchart TD
    subgraph CentralHub ["Central Management (RHACM Hub Cluster)"]
        RHACM["<b>Red Hat Advanced Cluster Management (RHACM)</b><br>• GitOps Configuration & Policy Distribution<br>• Centralized Daily Quota Governance<br>• Dynamic Harvesting Campaign Distribution"]
        CentralNetApp[("<b>Central NetApp Storage / Object Lake</b><br>• Consolidated Golden Data Set (GDS)<br>• Active Learning & Model Retraining Pool")]
    end

    subgraph EdgePod ["Edge Station Pod (Crusher / Fuel Island / Maintenance)"]
        EdgeK8s["<b>Red Hat Edge Compute</b><br>• <i>Default:</i> <b>MicroShift</b> (2 vCPU, 2–4 GB RAM, CPU USearch)<br>• <i>Heavy AI:</i> <b>SNO</b> (8+ vCPU, 16–32 GB RAM, NVIDIA L4/L40S GPU)<br>• Containerized Edge Triage Worker & Inotify Watcher"]
        
        subgraph NetAppEdge ["NetApp Edge Storage (Astra Trident CSI)"]
            RawPVC[("<b>Raw Ingest PVC</b><br>(NetApp ONTAP NAS / NFS - RWX)<br>• High-throughput burst writes<br>• Local 24–48h forensic ring buffer<br>• <i>Demo: 500 GiB | Prod: 30–50 TB/day</i>")]
            CuratedPVC[("<b>Curated GDS PVC</b><br>(NetApp ONTAP NAS / S3 - RWX)<br>• Pruned 45s candidate MCAP blobs<br>• Standardized gds_metadata_v2.json<br>• <i>Demo: 100 GiB | Prod: 1–2 TB</i>")]
        end
        
        TruckSimulator["<b>Fleet Telemetry Simulator</b><br>(Simulates 100 trucks dumping shift logs)"]
    end

    RHACM ==>|"1. Deploys Triage Engine & Policies (GitOps)"| EdgeK8s
    TruckSimulator -->|"2. Dumps raw MCAP & CAN logs"| RawPVC
    RawPVC -->|"3. Watches & triages incoming files (Inotify)"| EdgeK8s
    EdgeK8s -->|"4. Writes pruned clips & metadata"| CuratedPVC
    CuratedPVC -.->|"5. NetApp SnapMirror / Cloud Sync (10–20 GB/day)"| CentralNetApp
```

### 2.1 Component Mapping & Division of Responsibility

| Platform Component | Role in the Edge Triage Pipeline | Key Capabilities Demonstrated |
| :--- | :--- | :--- |
| **Red Hat MicroShift** *(Lightweight Edge Default)* | **Low-Footprint Edge Runtime:** Sized for 2 vCPU and 2–4 GB RAM on ruggedized in-vehicle PCs or Crusher skid pods running CPU-only USearch vector search and kinematic screening. | • Minimal resource overhead on industrial hardware.<br>• Deterministic offline execution during satellite WAN dropouts.<br>• Fast cold-boot recovery following vehicle battery disconnects. |
| **Red Hat OpenShift (SNO)** *(Heavy Edge AI)* | **GPU-Accelerated Edge Platform:** Single Node OpenShift (8+ vCPU, 16–32 GB RAM) deployed at Fuel Island pods equipped with NVIDIA L4/L40S GPUs for heavy 4D world modeling (EmerNeRF) and multi-truck triage. | • Native NVIDIA GPU Operator integration.<br>• Full enterprise Kubernetes API and Operator lifecycle.<br>• Complete disconnected/air-gapped registry mirroring support. |
| **NetApp ONTAP + Astra Trident** | **Edge Data Fabric & Persistence:** High-performance storage orchestrator managing raw burst ingest, instant snapshot recovery, and automated replication. | • **Trident CSI Driver:** Automated dynamic provisioning for `ReadWriteMany` (RWX via `ontap-nas`) and `ReadWriteOnce` (RWO via `ontap-san`).<br>• **NetApp Snapshot Copies:** Zero-impact point-in-time snapshots for forensic investigation retention.<br>• **NetApp SnapMirror / Cloud Sync:** Siphon curated GDS snippets over constrained WAN links to central cloud object storage.<br>• **FabricPool & Quotas:** Enforcing storage limits and offloading cold blocks to secondary flash. |
| **Red Hat ACM** *(RHACM)* | **Central Control Plane & Governance:** Centrally distributes triage policies, daily quotas, dynamic campaigns, and model drift compensation vectors across distributed edge sites. | • Multi-cluster application lifecycle via modern `Placement` API.<br>• Governance policies ensuring edge pods adhere to `storage_eviction_policy.yaml`.<br>• Automated deployment of new vision backbone version indices across Crusher and Fuel Bay pods without firmware re-flashing. |

> **Production vs. Demo Storage Sizing Note:** In a full-scale production 10-truck cell, raw multi-sensor streaming generates **30 to 50 TB/day**, requiring high-capacity NetApp AFF/FAS arrays with FabricPool secondary tiering to hold 24–48 hours of rolling forensic ring buffers. In this "Hello World" blueprint, the raw ingest volume is sized at a **demo-scale 500 GiB PVC** (calibrated to absorb synthetic 100-event test batches), while the curated GDS volume is sized at **100 GiB** (holding ~285 pruned candidate snippets at ~350 MB each, equivalent to 14–28 days of curated site uploads).

---

## 3. Core Features & Pipeline Functional Mechanics

```mermaid
flowchart LR
    Ingest["<b>1. Storage Watcher</b><br>Inotify detects new dump on NetApp PVC"] --> Stage1
    
    subgraph Stage1 ["Stage 1: Multi-Criteria Screening (Spec 01)"]
        F1["<b>Filter 1: Kinematic / Safety</b><br>E-Stops, AEB, lateral >0.3g, TTC <3.0s"]
        F2["<b>Filter 2: Uncertainty (Raw 30 FPS)</b><br>Epistemic entropy >0.70, confidence <0.65"]
        F3["<b>Filter 3: Vector Novelty</b><br>USearch 128-D cosine distance > τ"]
        F4["<b>Filter 4: Campaigns (RHACM)</b><br>Dynamic geofence & condition match"]
        F5["<b>Filter 5: ODD Baseline</b><br>0.1% uniform nominal sample"]
    end
    
    F1 --> CandidateCheck{"Any Filter<br>Triggered?"}
    F2 --> CandidateCheck
    F3 --> CandidateCheck
    F4 --> CandidateCheck
    F5 --> CandidateCheck

    CandidateCheck -- No (Nominal 95%) --> Purge["<b>Purge / Overwrite</b><br>Release NetApp staging space"]
    CandidateCheck -- Yes (Candidate 5%) --> Stage2
    
    subgraph Stage2 ["Stage 2: Cross-Fleet Deduplication (Spec 01)"]
        F6["<b>Filter 6: Coreset Dedup</b><br>Match geohash (±100m) + 2h window<br>+ cosine distance <0.10"]
    end

    Stage2 -- Duplicate Detected --> DedupDrop["<b>Suppress</b><br>Retain single highest-entropy event"]
    Stage2 -- Unique Novelty --> Stage3
    
    subgraph Stage3 ["Stage 3: Data Reduction & Schema (Spec 02)"]
        Prune["<b>Frustum & Sensor Pruning</b><br>Strip side/cabin cams; keep 8MP front & 128L"]
        Decimate["<b>Perceptual Decimation</b><br>Downsample 30→10 FPS; crop LiDAR >100m"]
        ReverseCheck["<b>Reverse Safety Exception</b><br>Promote rear vision/LiDAR/radars if reversing"]
        EmitMeta["<b>Metadata Schema Emission</b><br>Generate standardized gds_metadata_v2.json"]
    end

    Stage3 --> Staging["<b>Curated Output</b><br>Write to NetApp Curated PVC (ready for SnapMirror)"]
```

### 3.1 Stage 1: Ingestion & Storage Trigger
* The triage daemon monitors the incoming directory on the NetApp raw ingest PVC: `/mnt/raw_ingest/{truck_id}/{timestamp}/`.
* Ingested files comprise multi-channel **MCAP container files** paired with dynamic `telemetry.json` records.
* Upon detecting a closed write handle via `inotify` or file-close events, the daemon initiates the triage pipeline.

### 3.2 Stage 2: Parallel Multi-Criteria Screening (Filters 1–5)
The worker evaluates the raw 45-second event buffer against the screening filters in parallel logical `OR`:
1. **Filter 1 (Kinematic & Safety Floor):** Evaluates physical chassis CAN telemetry. Triggers deterministically if:
   * Emergency Stop active (`e_stop_active == true`)
   * Autonomous Emergency Braking engaged (`aeb_engaged == true`)
   * Lateral acceleration $|a_{\text{lat}}| > 0.30\text{g}$ (dynamically tightened to $>0.20\text{g}$ on loaded downhill grades)
   * Time-to-Collision $\text{TTC} < 3.0\text{s}$ (extended to $<4.5\text{s}$ on downhill haul ramps)
2. **Filter 2 (Model Uncertainty & Disagreement):** 
   * **Critical Pipeline Ordering:** Epistemic uncertainty and bounding-box jitter variance across 5 frames (0.16s) **must be computed in real time on the raw 30 FPS stream** *before* downsampling to 10 FPS.
   * Triggers if minimum bounding-box confidence $< 0.65$, semantic segmentation Shannon entropy $> 0.70$, or detector cross-disagreement is flagged.
3. **Filter 3 (Latent Space Metric Novelty):** 
   * Reads a 128-D latent scene embedding vector (generated by an onboard or edge vision backbone, e.g. MobileNetV4 / DINO-v2 feature extractor).
   * Queries a local **USearch** HNSW index containing the operational baseline gallery.
   * Triggers if cosine distance $d(\mathbf{v}_{\text{query}}, \mathbf{V}_{\text{baseline}}) > \tau_{\text{novelty}}$ (e.g., $\tau = 0.72$).
4. **Filter 4 (Targeted Dynamic Campaigns):** Matches vehicle GPS against active campaign polygons pushed centrally via RHACM (e.g. haul road watering operations, dust plume sectors).
5. **Filter 5 (Stratified ODD Nominal Baselines):** Uniform pseudorandom sampler tagging 0.1% of nominal driving events across operational quadrants to prevent catastrophic forgetting.

### 3.3 Stage 3: Cross-Fleet Coreset Deduplication (Filter 6)
If any filter flags a candidate snippet, it enters fleet deduplication:
* The candidate's coordinate is quantized into an **Uber H3 index (resolution 9, ~100m cell)** or geohash.
* The engine queries the site coreset registry:
  * Has another truck reported an anomaly in this spatial cell within the last **2 hours**?
  * If yes, compute cosine distance between both 128-D embeddings.
  * If $d(\mathbf{v}_1, \mathbf{v}_2) < 0.10$, suppress the duplicate snippet and retain only the instance with higher sensor confidence or sharper exposure.
* **Impact:** Suppresses **60% to 80%** of redundant fleet triggers caused by static obstacles encountered by multiple trucks.

### 3.4 Stage 4: Representation Reduction & Safety Exceptions (Spec 02)
* **Temporal Slicing:** Extracts exactly $T - 30\text{s}$ pre-trigger (root cause onset) to $T + 15\text{s}$ post-trigger (stopping stabilization).
* **Canonical Sensor Stream IDs & Frustum Pruning:**
  * `cam_front_center_8mp`: **KEEP** (High Resolution)
  * `lidar_128_beam_main`: **KEEP** (High Resolution, cropped to 100m nominal ODD range; 50m crop only applied under Tier 3 emergency storage shedding)
  * `radar_4d_imaging_front`: **KEEP** (High Resolution)
  * `vehicle_telemetry_bus`: **KEEP** (Native 100 Hz CAN/IMU)
  * `cam_rear_perimeter_4mp`: **DROP** (Forward) / **KEEP** (Reversing)
  * `lidar_perimeter_solid_state`: **DROP** (Forward) / **KEEP** (Reversing)
  * `radar_perimeter_rear`: **DROP** (Forward) / **KEEP** (Reversing)
  * `radar_blind_spot_side_left` & `radar_blind_spot_side_right`: **DROP** (Forward) / **KEEP** (Reversing)
  * `cam_in_cabin_driver`: **DROP** (Excluded for privacy)
* **Reversing & Hopper Maneuvering Exception:** If CAN powertrain signals reverse gear or geofencing locates the truck within a dump pocket or crusher hopper, the pruning mask dynamically flips: `cam_rear_perimeter_4mp`, `lidar_perimeter_solid_state`, `radar_perimeter_rear`, `radar_blind_spot_side_left`, and `radar_blind_spot_side_right` are promoted to **KEEP** at native resolution to prevent hopper wall collisions and articulated jackknifing, while forward auxiliary channels are decimated.
* **Perceptual Decimation:** Decimates camera frames from 30 FPS down to 10 FPS for archival serialization (66% volume reduction). Converts LiDAR 32-bit floats to 16-bit fixed-point coordinates (50% vertex payload reduction).
* **Metadata Schema Emission:** Generates a standardized `gds_metadata_v2.json` record capturing software manifests, SA.45s CSAC clock telemetry (`PTP_HOLDOVER_ACTIVE`, 112 ns drift), filter scores, embedding vector, and optical dock metrics.

### 3.5 End-to-End Demo I/O Math Closure
* **Input Volume (100 synthetic events):** 100 raw 45s events @ 1.6 to 2.7 GB unpruned = **~160 to 270 GB raw ingest**.
* **Stage 1 & 2 Filtering:** 95 nominal events discarded (Filter 5 retains 1 nominal anchor). 5 candidate anomaly events flagged. Filter 6 deduplicates 2 repeated encounters.
* **Stage 3 Pruning:** The remaining 3 unique anomaly events and 1 nominal anchor are pruned from ~2.0 GB down to **~240 to 810 MB each** (nominal average ~350 MB; up to ~800 MB if reverse-gear safety exception preserves rear sensors).
* **Output Volume:** Total curated Golden Data Set volume = **~1.4 to 2.4 GB**, demonstrating a genuine **~99% data reduction** before WAN upload.

---

## 4. Open Source & Commercial Technology Stack

| Layer | Component / Tool | Licensing | Implementation Role in Blueprint |
| :--- | :--- | :--- | :--- |
| **Robotics Log Serialization** | **Foxglove MCAP** (`mcap`) | Apache-2.0 | Append-only container format for multi-modal sensor streams. Enables seeking and channel extraction without loading entire files into memory. |
| **Embedded Vector Search** | **USearch (Unum)** (`usearch` Python / C++11) | Apache-2.0 | Fast, lightweight HNSW vector index. Runs SIMD-optimized cosine distance queries on 128-D embeddings directly on edge CPU/NPU. |
| **Spatial Indexing** | **Uber H3** (`h3`) / **Geohash2** | Apache-2.0 / MIT | Hexagonal spatial indexing for quantizing truck GPS coordinates into ~100m buckets for Filter 6 coreset matching. |
| **Microservice Runtime** | **Python 3.11+** / **FastAPI** | PSF / MIT | Event-driven triage worker and mock telemetry generator. |
| **Container Base Image** | **Red Hat Universal Base Image 9 (UBI 9 Minimal)** | Red Hat UBI EULA | Hardened enterprise container base image optimized for OpenShift workloads. |
| **Storage Orchestration** | **NetApp Astra Trident CSI** | Apache-2.0 | Open-source Kubernetes CSI driver dynamically provisioning NetApp ONTAP PersistentVolumes and VolumeSnapshots. |
| **Storage Backend** | **NetApp ONTAP** | Commercial | Enterprise storage operating system providing NVMe, NFS, deduplication, and SnapMirror replication. |
| **Cluster Management** | **Red Hat ACM (RHACM)** | Commercial (Upstream: Open Cluster Management, Apache-2.0) | Multi-cluster GitOps engine deploying triage workloads and synchronizing configuration policies across edge clusters. |

---

## 5. Concrete Data Contracts & Mock Payload Specifications

### 5.1 Simulated Raw Ingest Directory Structure (NetApp Raw PVC)
```
/mnt/raw_ingest/
├── HAUL-TRUCK-002/
│   └── 20261014T080000Z/
│       ├── sensor_stream.mcap        # 45-second multi-channel raw recording (~1.6–2.7 GB)
│       └── telemetry.json             # CAN bus, IMU, GPS, and inference outputs
├── HAUL-TRUCK-007/
│   └── 20261014T081500Z/
│       ├── sensor_stream.mcap
│       └── telemetry.json
```

### 5.2 Telemetry JSON Contract (`telemetry.json`)
```json
{
  "truck_id": "HAUL-TRUCK-042",
  "timestamp_iso": "2026-10-14T08:12:40.000000Z",
  "software_version": "v4.14.0-prod",
  "kinematics": {
    "ground_speed_kph": 24.2,
    "road_grade_percent": -7.8,
    "lateral_acceleration_g": 0.34,
    "longitudinal_deceleration_g": 0.45,
    "time_to_collision_seconds": 2.6,
    "reverse_gear_engaged": false,
    "e_stop_active": false,
    "aeb_active": true
  },
  "geospatial": {
    "latitude": -22.451234,
    "longitude": 118.874512,
    "pit_sector": "BENCH_04_SOUTH_RAMP"
  },
  "perception_outputs": {
    "epistemic_entropy": 0.78,
    "minimum_detection_confidence": 0.52,
    "bounding_box_jitter_variance": 0.042,
    "sensor_disagreement": true,
    "embedding_128d": [0.0381, -0.1422, 0.8912, 0.0054, -0.0612]
  }
}
```

### 5.3 Curated GDS Output Directory Structure (NetApp Curated PVC)
```
/mnt/gds_curated/
└── SNIP-20261014-TRK042-00941/
    ├── gds_metadata_v2.json           # Standardized catalog entry (<5 KB)
    └── pruned_payload.mcap            # Pruned 45s event snippet (~240–810 MB)
```

---

## 6. OpenShift & NetApp Kubernetes Manifest Architecture

The complete deployable Kubernetes and OpenShift manifests are located in [`demo/k8s/`](./k8s/):

```
demo/
├── src/                          # Enterprise modular Python microservice source
│   ├── Containerfile             # Hardened Red Hat UBI 9 image definition
│   ├── requirements.txt          # mcap, usearch, pyyaml, pydantic, prometheus-client
│   ├── triage_engine/            # Core triage engine package
│   │   ├── config.py             # Pydantic schema validation & inotify policy reloader
│   │   ├── metrics.py            # Prometheus metrics (bytes, counters, reduction ratio)
│   │   ├── pipeline.py           # MCAP processor & USearch CPU SIMD vector index
│   │   └── main.py               # Main service daemon & HTTP metrics server
│   └── simulator/                # Benchmark fleet telemetry generator
│       └── generator.py          # Emits genuine multi-channel MCAP containers
│
└── k8s/                          # OpenShift & NetApp manifests
    ├── 00_namespace.yaml         # Namespace, ServiceAccount, non-root OpenShift SCC compliance
    ├── 01_storage_classes.yaml   # NetApp ONTAP NAS (RWX) and SAN (RWO) Trident StorageClasses + SnapshotClass
    ├── 02_persistent_volumes.yaml# Raw Ingest (500 GiB demo-scale) and Curated GDS (100 GiB) PVCs
    ├── 03_triage_configmap.yaml  # Triage quotas, thresholds, campaigns, and storage eviction policy
    ├── 04_triage_deployment.yaml # Containerized triage worker pod with probes & Prometheus port 8080
    ├── 05_simulator_job.yaml     # Benchmark fleet generator Job producing 100 MCAP test packages
    ├── 06_monitoring.yaml        # Service and OpenShift ServiceMonitor for Web Console dashboards
    └── 07_buildconfig.yaml       # OpenShift ImageStream & BuildConfig for in-cluster builds
```

### 6.1 Storage Classes & NetApp Trident Integration (`01_storage_classes.yaml`)
* **`ontap-nas`:** Configured with `nfs` protocol (NFS v4.1, 1MB rsize/wsize) and `ReadWriteMany` (RWX) access mode, allowing the simulator job and triage worker to mount the volume concurrently.
* **`ontap-san`:** Configured with `iscsi` protocol and `ReadWriteOnce` (RWO) for dedicated high-throughput raw buffers.
* **`netapp-snapshot-class`:** `VolumeSnapshotClass` enabling zero-impact point-in-time snapshots for forensic audit retention.

### 6.2 In-Cluster Image Build (`07_buildconfig.yaml`)
On OpenShift, developers do not need an external Docker Hub or Quay.io registry account. The provided `BuildConfig` builds the container directly inside the 3-node cluster:
```bash
oc start-build edge-triage-builder --from-dir=demo/src --follow -n edge-triage
```
This pushes `edge-triage-engine:latest` into the cluster's internal registry (`image-registry.openshift-image-registry.svc:5000/edge-triage/edge-triage-engine:latest`), which the Deployment and Simulator Job consume immediately.

### 6.3 OpenShift Monitoring & Telemetry Dashboard (`06_monitoring.yaml`)
The triage worker exports real-time metrics on port 8080 (`/metrics`), scraped automatically by OpenShift's cluster monitoring stack:
* `edge_triage_bytes_ingested_total` vs `edge_triage_bytes_curated_total`
* `edge_triage_reduction_percentage` (exposes live 99%+ volume reduction)
* `edge_triage_events_curated_total` (labeled by `tier`)
* `edge_triage_dedup_suppressions_total` (counts Filter 6 duplicates suppressed)

### 6.4 Hot-Reloading Configuration via RHACM & Offline Resiliency
* **ConfigMap Hot-Reloading:** The triage worker does not use static environment variables or `subPath` mounts. Instead, `03_triage_configmap.yaml` is mounted as a full directory volume at `/etc/triage-config`. The Python worker monitors file modification timestamps and hot-reloads detection thresholds, campaigns, and quotas within seconds without container restarts.
* **Satellite WAN Blackout Behavior:** If remote satellite WAN drops out, RHACM cannot reach the edge pod. The edge pod continues running deterministically using the locally cached ConfigMap and NetApp persistent storage, buffering curated GDS events locally on the 100 GiB PVC until satellite connectivity resumes.

---

## 7. Execution Guide: Running the Demo on a 3-Node OpenShift Cluster

Follow these steps to run the complete demonstration:

### Step 1: Create Namespace and Storage
```bash
kubectl apply -f demo/k8s/00_namespace.yaml
kubectl apply -f demo/k8s/01_storage_classes.yaml
kubectl apply -f demo/k8s/02_persistent_volumes.yaml
kubectl apply -f demo/k8s/03_triage_configmap.yaml
```

### Step 2: Build the Container Image in OpenShift
```bash
oc apply -f demo/k8s/07_buildconfig.yaml
oc start-build edge-triage-builder --from-dir=demo/src --follow -n edge-triage
```

### Step 3: Deploy the Triage Worker and Prometheus Monitoring
```bash
oc apply -f demo/k8s/04_triage_deployment.yaml
oc apply -f demo/k8s/06_monitoring.yaml
```

### Step 4: Run the 100-Event Fleet Simulator
```bash
oc apply -f demo/k8s/05_simulator_job.yaml
```

### Step 5: Observe Live Reduction in Logs and OpenShift Web Console
```bash
# Follow the live triage engine logs
oc logs -n edge-triage -l app.kubernetes.io/component=triage-worker -f

# Verify curated packages on the NetApp Curated Volume
oc exec -n edge-triage deploy/edge-triage-worker -- ls -lh /mnt/gds_curated
```
In the OpenShift Web Console under **Observe -> Metrics**, query `edge_triage_reduction_percentage` to observe the live 99% data volume reduction graph.

