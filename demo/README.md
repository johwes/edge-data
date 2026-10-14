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

# 2. Configure StorageClass (If using NetApp ONTAP / Astra Trident)
# Note: If deploying on public cloud (AWS EFS, Azure Files, GCP Filestore), skip this step.
oc apply -f demo/k8s/01_storage_classes.yaml

# 3. Create Persistent Volume Claims
# Note: Sized at a lean 10Gi (raw) and 5Gi (curated) to minimize cloud allocation costs.
# Set storageClassName in 02_persistent_volumes.yaml to your cloud provider's RWX class:
#   - NetApp ONTAP / Cloud Volumes ONTAP / AWS FSx: "ontap-nas"
#   - AWS / ROSA: "efs-sc"
#   - Azure / ARO: "azurefile-csi"
#   - GCP: "standard-rwx"
#   - Cluster Default: omit storageClassName to use cluster default
oc apply -f demo/k8s/02_persistent_volumes.yaml

# 4. Deploy the runtime triage policy ConfigMap
oc apply -f demo/k8s/03_triage_configmap.yaml
```

> **Decoupled Storage Architecture:**  
> The Deployment (`04_triage_deployment.yaml`) and Simulator (`05_simulator_job.yaml`) are completely decoupled from storage backends. They strictly reference `claimName: raw-ingest-pvc` and `claimName: gds-curated-pvc`. To switch from on-prem NetApp to AWS, Azure, or GCP, you only edit `02_persistent_volumes.yaml` without touching the application manifests.

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

#### 3. Inspect Curated NetApp Persistent Storage
Verify that curated Golden Data Set packages exist on the persistent storage volume:
```bash
oc exec -n edge-triage deploy/edge-triage-worker -- ls -lh /mnt/gds_curated
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
