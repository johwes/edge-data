# Autonomous Fleet Edge Data Triage & Golden Data Set (GDS) Architecture

This repository outlines the technical strategy, systems architecture, and implementation blueprint for managing high-volume sensor data (500 TB/day/site) across remote autonomous vehicle fleets in mining and industrial logistics.

---

## 1. Executive Architectural Specifications

The canonical system architecture is modularized into focused subsystem specifications:

* **[Master Architecture & Site Infrastructure Overview](docs/golden_data_set_architecture.md)**: Master executive overview, multi-tier system topology diagram, and architectural hardening alignment table.
* **[Specification 01: Data Filtering, Triage & Deduplication](docs/01_data_filtering_and_triage.md)**: 6-filter information entropy funnel, kinematic safety triggers, BCT/QDC latent vector drift mitigation, and daily quota allocation.
* **[Specification 02: Data Reduction & Metadata Schema](docs/02_data_reduction_and_metadata_schema.md)**: 45s temporal ring buffering, frustum pruning, reverse-gear safety exceptions, and the standardized `gds_metadata_v2.json` schema.
* **[Specification 03: Edge Transport, Docking & Middleware](docs/03_transport_docking_and_middleware.md)**: Sharded pit topologies (Crusher vs. Fuel Island), automated optical docking (SAE J3105/3 mechanical envelope reuse), shift-change M/M/c queuing models, and Eclipse Zenoh middleware.
* **[Specification 04: Site Infrastructure & Hardware Hardening](docs/04_site_infrastructure_and_hardware.md)**: 4U skid-mounted Edge Station Pods, Microchip SA.45s CSAC atomic clock PTP holdover (<0.8 µs/24h), 3 DWPD enterprise NVMe storage lifecycle (`storage_eviction_policy.yaml`), and Vault/TPM security controls.
* **[Specification 05: Commercial Landscape, Tooling Evaluation & Roadmap](docs/05_commercial_landscape_and_roadmap.md)**: 4D world modeling (EmerNeRF/Street Gaussians), commercial vendor matrix, 4-phase deployment plan, pilot commissioning punch-list, and 40 authoritative references.

---

## 2. Practical Implementation Blueprint (PoC / Demo)

* **[Edge Data Triage & Deduplication Blueprint](demo/BLUEPRINT.md)**: A concrete, actionable implementation blueprint bridging Specifications 01 and 02 into a runnable "Hello World" application designed for:
  * **Red Hat OpenShift (SNO / MicroShift / ROSA / ARO)** at the edge or in the cloud.
  * **NetApp Storage (ONTAP / Astra Trident CSI)** or cloud-native RWX storage for high-throughput raw ingest, local snapshots, and tiering.
  * **Red Hat Advanced Cluster Management (RHACM)** for centralized GitOps policy distribution, daily quota governance, and multi-cluster deployment.
* **[Quick-Start Deployment Guide (`demo/README.md`)](demo/README.md)**: Step-by-step instructions to build, deploy, and run the 100-event telemetry simulator, FFmpeg video extraction, and Prometheus metrics on OpenShift.
* **[Live Presenter & Storytelling Guide (`demo/DEMO_GUIDE.md`)](demo/DEMO_GUIDE.md)**: 5-minute narrative script, dual-stream colored log runner (`stream_demo.py`), environment reset script (`prep_demo.sh`), and live Web Dashboard walkthrough.
