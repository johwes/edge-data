# Specification 00: Master Architecture & Site Infrastructure Overview

This document is the master index and executive architectural overview for the Remote Autonomous Fleet Data Triage & Golden Data Set (GDS) pipeline.

The full master architecture document is maintained at:
**[Master System Architecture & Site Infrastructure Overview (`golden_data_set_architecture.md`)](file:///home/jwesterl/Downloads/opencode/edge-data/docs/golden_data_set_architecture.md)**

---

## Direct Subsystem Specification Index

```mermaid
graph TD
    Master["<b>Master System Architecture Overview</b><br><i>golden_data_set_architecture.md</i>"]
    
    Master --> Spec1["<b>Specification 01: Data Filtering, Triage & Deduplication</b><br>• 6-Filter Entropy Funnel & Kinematic Triggers<br>• BCT & QDC Latent Vector Drift Formulations<br>• Execution Topologies A/B/C & Coreset Dedup<br>• Daily Quota Allocation & Preemption Policies"]
    
    Master --> Spec2["<b>Specification 02: Data Reduction & Metadata Schema</b><br>• 45s Temporal Ring Buffering Window<br>• Frustum Pruning & Reversing Safety Exceptions<br>• Frame Decimation & Fixed-Point LiDAR Quantization<br>• Standardized gds_metadata_v2.json Schema"]
    
    Master --> Spec3["<b>Specification 03: Edge Transport, Docking & Middleware</b><br>• Operational Compartments (Crusher, Fuel, Parkup)<br>• Dual-Mode Optical Dock (SAE J3105/3) & VFO<br>• Shift-Change M/M/c Dock Queuing Capacity Model<br>• eProsima Fast DDS + Eclipse Zenoh Middleware"]
    
    Master --> Spec4["<b>Specification 04: Site Infrastructure & Hardware Hardening</b><br>• 4U Skid-Mounted Edge Compute Pods (NVIDIA GPUs)<br>• Microchip SA.45s CSAC Atomic Clock PTP Holdover<br>• 3 DWPD NVMe SSD Endurance & Level-4 Hardware PLP<br>• storage_eviction_policy.yaml & TPM 2.0 PKI"]
    
    Master --> Spec5["<b>Specification 05: Commercial Landscape & Roadmap</b><br>• 4D Ground-Truth Auto-Labeling (EmerNeRF)<br>• Commercial Vendor Matrix & Open Standards<br>• 4-Phase Implementation Rollout Plan<br>• Pilot Commissioning Punch-List & References"]
```

1. [**Specification 01: Data Filtering, Triage & Deduplication Subsystem**](file:///home/jwesterl/Downloads/opencode/edge-data/docs/01_data_filtering_and_triage.md)
2. [**Specification 02: Data Reduction & Metadata Schema**](file:///home/jwesterl/Downloads/opencode/edge-data/docs/02_data_reduction_and_metadata_schema.md)
3. [**Specification 03: Edge Transport, Docking & Middleware Subsystem**](file:///home/jwesterl/Downloads/opencode/edge-data/docs/03_transport_docking_and_middleware.md)
4. [**Specification 04: Site Infrastructure, Hardware Hardening & Storage Lifecycle**](file:///home/jwesterl/Downloads/opencode/edge-data/docs/04_site_infrastructure_and_hardware.md)
5. [**Specification 05: Commercial Landscape, Tooling Evaluation & Implementation Roadmap**](file:///home/jwesterl/Downloads/opencode/edge-data/docs/05_commercial_landscape_and_roadmap.md)
