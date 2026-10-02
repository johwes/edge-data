# Autonomous Haulage Edge Data & GDS Architecture

This repository outlines the technical strategy and system architecture for managing high-volume sensor data (500 TB/day/site) across remote autonomous truck fleets in mining and industrial logistics.

## Key Documents

* **[Golden Data Set Architecture Specification](docs/golden_data_set_architecture.md)**: Comprehensive architectural specification detailing:
  * The 5-layer edge value triage engine (Deterministic, Active Learning, Vector Embeddings, Campaigns, Stratified Sampling)
  * The multi-tier transport hierarchy (On-Truck $\rightarrow$ Depot Wi-Fi 6 $\rightarrow$ Satellite $\rightarrow$ Sneakernet)
  * Data reduction techniques (temporal ring buffers, frustum & channel pruning, frame decimation)
  * Sizing and quantitative data reduction funnels (500 TB $\rightarrow$ 5 TB $\rightarrow$ <50 GB) and Cloud Cost Model ($345k/mo raw vs <$1.1k/mo curated)
  * Standardized JSON Metadata Schema (`gds_metadata_v2.json`)
  * Mathematical vector drift mitigation under OTA updates (Backward-Compatible Training & Zero-Shot Query Drift Compensation)
  * Hybrid transport middleware: eProsima Fast DDS (onboard IPC) + Eclipse Zenoh (depot wireless bridging)
  * Hardware hardening: Chip-Scale Atomic Clock (CSAC) PTP holdover, 10 Gbps robotic optical docking (SAE J3105/3 with dust purge), 3 DWPD NVMe storage
  * Open Standards matrix (MCAP, Fast DDS, Zenoh, USearch, LanceDB, Cleanlab, ASAM OpenSCENARIO) & Commercial Vendor Landscape (Kognic, Sift, Akridata, Voxel51, AWS IoT FleetWise, Applied Intuition)
  * Concrete configuration artifacts (`storage_eviction_policy.yaml` & `zenoh_bridge_config.json5`)
  * 4-phase implementation roadmap and operational review alignment matrix
  * **Comprehensive Reference Library (Section 13)**: 40 authoritative, hyperlinked industry citations and academic papers backing all financial, hardware, algorithmic, and networking claims.
