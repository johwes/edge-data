# Edge Data Triage & Deduplication Demo

A practical, enterprise-grade demonstration of **Autonomous Fleet Data Triage and Spatiotemporal Deduplication** running on a **3-node Red Hat OpenShift edge cluster**, backed by **NetApp Enterprise Storage (via Astra Trident CSI)**, and governed via **Red Hat Advanced Cluster Management (RHACM)**.

---

## Architecture Overview

```
100 Raw Vehicle Events (~102 MB demo / ~200 GB prod)
  │
  ▼
[NetApp Ingest NFS Ring Buffer (raw-ingest-pvc / RWX)]
  │
  ▼
[Edge Triage Engine (OpenShift Deployment)]
  ├── Filter 1: Deterministic CAN Dynamics (lateral g-force, TTC, loaded downhill grade adaptation)
  ├── Filter 2: Perception Model Uncertainty (detection confidence, Shannon entropy, temporal variance)
  ├── Filter 3: Unsupervised Feature Novelty (USearch SIMD-accelerated HNSW index on CPU)
  ├── Filter 4: Campaign Geofencing (GPS point-in-polygon ray casting)
  ├── Filter 5: Statistical ODD Baselines (uniform sampling & mandatory shift anchors)
  └── Filter 6: Cross-Fleet Deduplication (2-hour window, spherical Haversine distance, H3 index)
  │
  ├── 91 Nominal Events ──> Discarded & purged from edge ring buffer
  ├── 1 Duplicate Event  ──> Suppressed by Filter 6
  │
  ▼
[Curated & Decimated Golden Data Set (~1.4 MB demo / ~1.4 GB prod)]
  └── Written to NetApp Curated Storage (gds-curated-pvc / RWX)
  └── Live bandwidth reduction (~98.6%) exported to OpenShift Monitoring (/metrics)
```

---

## Prerequisites

1. **Red Hat OpenShift Cluster** (Version 4.12+, compact 3-node cluster or Single Node OpenShift).
2. **NetApp Astra Trident Operator** installed on the cluster (namespace: `trident`).
3. **OpenShift CLI (`oc`)** logged in with cluster administrator or project administrator privileges.
4. *(Optional)* User Workload Monitoring enabled in OpenShift to view graphs in the web console.

---

## Quick-Start Deployment Guide

### Step 1: Create Namespace and Storage Resources

Apply the namespace, RBAC, Astra Trident storage classes, and NetApp persistent volume claims:

```bash
# 1. Create edge-triage namespace and service account
oc apply -f demo/k8s/00_namespace.yaml

# 2. Configure StorageClass (NetApp ONTAP / Astra Trident ONLY)
# SKIP THIS STEP if deploying on public cloud (AWS ROSA, Azure ARO, GCP OCP).
# Only apply this if your cluster has the NetApp Astra Trident CSI Operator installed:
# oc apply -f demo/k8s/01_storage_classes.yaml

# 3. Create Persistent Volume Claims
# By default, storageClassName is omitted so it binds automatically to your cluster's default StorageClass.
# Sized at a lean 10Gi (raw) and 5Gi (curated) to eliminate cloud provisioning fees.
oc apply -f demo/k8s/02_persistent_volumes.yaml

# 4. Deploy the runtime triage policy ConfigMap
oc apply -f demo/k8s/03_triage_configmap.yaml
```

> **Decoupled Storage Architecture & Cloud vs. On-Prem NetApp:**  
> * **Zero Application Coupling:** The Deployment (`04_triage_deployment.yaml`) and Simulator (`05_simulator_job.yaml`) reference only the logical names `raw-ingest-pvc` and `gds-curated-pvc`. They run identically whether backed by NetApp ONTAP, AWS EFS, Azure Files, or GCP Filestore.
> * **Cloud Public Demos:** Cloud OpenShift clusters (ROSA, ARO, GCP) can run the demo immediately with zero NetApp dependencies. Snapshots are handled via native cloud VolumeSnapshotClasses (e.g., AWS EBS/EFS or Azure Backup).
> * **Production Operational Note ($N \ge 150$ Trucks):** While cloud-native RWX (EFS / Azure Files) easily satisfies this 100 MB demo, high-throughput industrial mining cells (30–50 TB/day uncompressed) require NetApp ONTAP AFF/FAS NVMe/NFS arrays with 1MB rsize/wsize mount tuning and hardware SnapMirror replication to sustain 100 GbE line-rate optical wireless docking within the 240-second berth occupancy window.

Verify storage bindings:
```bash
oc get pvc -n edge-triage
```
*Expected status: Both `raw-ingest-pvc` and `gds-curated-pvc` should report `Bound`.*

---

### Step 2: Build the Container Image Inside OpenShift

You do not need external Docker Hub or Quay.io credentials. OpenShift builds the container directly using an internal `BuildConfig`:

```bash
# 1. Create the ImageStream and BuildConfig
oc apply -f demo/k8s/07_buildconfig.yaml

# 2. Trigger the in-cluster build from local source
oc start-build edge-triage-builder --from-dir=demo/src --follow -n edge-triage
```
*OpenShift will compile the UBI 9 image, install `mcap` and `usearch`, and tag `edge-triage-engine:latest` into the cluster's internal registry.*

---

### Step 3: Deploy the Triage Worker and Prometheus Monitoring

```bash
# 1. Deploy the triage worker service
oc apply -f demo/k8s/04_triage_deployment.yaml

# 2. Expose the metrics endpoint and configure OpenShift ServiceMonitor
oc apply -f demo/k8s/06_monitoring.yaml
```

Verify the triage worker is running:
```bash
oc get pods -n edge-triage -l app.kubernetes.io/component=triage-worker
```
*Expected status: `1/1 Running`.*

---

### Step 4: Run the 100-Event Fleet Telemetry Simulator

Launch the batch `Job` to generate 100 benchmark MCAP multi-channel vehicle recordings:

```bash
oc apply -f demo/k8s/05_simulator_job.yaml
```

Watch the simulator generate packages:
```bash
oc logs -n edge-triage -l app.kubernetes.io/component=simulator -f
```

---

### Step 5: Observe Live Triage & Bandwidth Reduction

#### 1. Live Pod Logs
Watch the triage engine make filtering, deduplication, and decimation decisions in real time:
```bash
oc logs -n edge-triage -l app.kubernetes.io/component=triage-worker -f
```

**Key Log Events to Highlight in Demos:**
* `[-] Event EVT_NOMINAL_HAUL_010: Discarded by Filters 1-5 (Nominal haul cycle).`
* `[+] Event EVT_F1_AEB_DOWNHILL_001: ACCEPTED under TIER_1_FORENSIC (Downhill -9% grade).`
* `[+] Event EVT_F2_DUST_UNCERTAINTY_002: ACCEPTED under TIER_2_MODEL_UNCERTAINTY (Entropy 0.82).`
* `[+] Event EVT_F3_NOVEL_HAUL_ROAD_003: ACCEPTED under TIER_3_FEATURE_NOVELTY (USearch distance 0.79 > 0.72).`
* `[+] Event EVT_F6_INTERSECTION_DUPLICATE_004A: ACCEPTED under TIER_2_MODEL_UNCERTAINTY.`
* `[-] Event EVT_F6_INTERSECTION_DUPLICATE_004B: Suppressed by Filter 6 (Duplicate haul @ 15.1m, sim: 1.000).`
* `[+] Event EVT_REVERSING_HOPPER_MANEUVER_006: ACCEPTED under TIER_1_FORENSIC (Reversing exception: promoted rear vision at 80% payload).`
* `[+] Event EVT_F4_CAMPAIGN_GEOFENCE_007: ACCEPTED under TIER_4_CAMPAIGN (Point-in-polygon match).`
* `[+] Event EVT_F5_MANDATORY_SHIFT_ANCHOR_009: ACCEPTED under TIER_5_ANCHOR.`

#### 2. OpenShift Web Console Metrics Dashboard
Navigate to **Observe $\rightarrow$ Metrics** in the OpenShift Web Console and query:

* `edge_triage_reduction_percentage` $\rightarrow$ Shows live **~98.6%** data reduction.
* `edge_triage_bytes_ingested_total` vs `edge_triage_bytes_curated_total` $\rightarrow$ Compares raw ingested bytes against curated output bytes.
* `edge_triage_events_curated_total` $\rightarrow$ Breaks down curated events by tier (`tier="TIER_1_FORENSIC"`, etc.).
* `edge_triage_dedup_suppressions_total` $\rightarrow$ Counts redundant events eliminated by Filter 6.

#### 3. Inspect Curated Persistent Storage
Verify that curated Golden Data Set packages and incident video clips exist on the storage volume:
```bash
oc exec -n edge-triage deploy/edge-triage-worker -- ls -lh /mnt/gds_curated
```

#### 4. Playback Extracted Incident Video Clips (FFmpeg In-Container Extraction)
When safety-critical events fire (e.g. `EVT_F1_AEB_DOWNHILL_001` or `EVT_REVERSING_HOPPER_MANEUVER_006`), the triage engine triggers in-container FFmpeg temporal extraction:
- Slices the exact 10-second temporal window ($T - 5\text{s}$ to $T + 5\text{s}$) centered on the telemetry trigger timestamp.
- Decimates camera frame rate from 30 FPS down to 10 FPS (matching Specification 02), slashing raw video size from ~1.25 MB to ~180 KB.
- Emits a standalone, standard `.mp4` video clip into `/mnt/gds_curated` playable anywhere without ROS2/Foxglove tools.
- Automatically purges the un-decimated rolling video buffer from `/mnt/raw_ingest`.

Fetch and play the extracted incident video clip on your local machine:
```bash
# Get the triage worker pod name
WORKER_POD=$(oc get pods -n edge-triage -l app.kubernetes.io/component=triage-worker -o jsonpath='{.items[0].metadata.name}')

# Copy the extracted 10s clip from the container volume to your workstation
oc cp -n edge-triage ${WORKER_POD}:/mnt/gds_curated/gds_curated_EVT_F1_AEB_DOWNHILL_001_clip_10s_10fps.mp4 ./aeb_incident_10fps.mp4

# Play immediately in VLC, mpv, or open directly in Chrome/Safari/Firefox
vlc ./aeb_incident_10fps.mp4
```

---

### Step 6: Test Dynamic Policy Hot-Reloading (RHACM Governance)

Without restarting the pod, change a threshold in `triage_policy.yaml`:

```bash
# Edit the ConfigMap live
oc edit configmap triage-policy -n edge-triage
# E.g., change distance_threshold_tau from 0.72 to 0.90
```

Within 5 seconds, observe the worker log:
```
[TriageConfig] Loaded triage policy v2.0 for pilbara-cell-04
```
*The policy hot-reloads instantly without container recreation or pipeline downtime.*

---

## Central Multi-Cluster Governance via RHACM

For operators managing multiple remote mine sites, apply [`08_rhacm_governance.yaml`](./k8s/08_rhacm_governance.yaml) to the **RHACM Hub Cluster**:

```bash
oc apply -f demo/k8s/08_rhacm_governance.yaml
```
*RHACM will continuously enforce the triage policy and storage eviction rules across all edge clusters labeled with `environment: edge` and `industry: mining-haulage`.*

---

## Clean-Up / Teardown

To reset the demonstration:

```bash
# Delete the simulator job
oc delete job fleet-telemetry-simulator -n edge-triage

# Clean the curated and raw storage directories
oc exec -n edge-triage deploy/edge-triage-worker -- rm -rf /mnt/raw_ingest/* /mnt/gds_curated/*

# Complete stack teardown
oc delete -f demo/k8s/05_simulator_job.yaml
oc delete -f demo/k8s/04_triage_deployment.yaml
oc delete -f demo/k8s/06_monitoring.yaml
oc delete -f demo/k8s/07_buildconfig.yaml
oc delete -f demo/k8s/03_triage_configmap.yaml
oc delete -f demo/k8s/02_persistent_volumes.yaml
oc delete -f demo/k8s/01_storage_classes.yaml
oc delete -f demo/k8s/00_namespace.yaml
```
