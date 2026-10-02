# Autonomous Haulage Edge Data & GDS Architecture

This repository outlines the technical strategy and system architecture for managing high-volume sensor data (500 TB/day/site) across remote autonomous truck fleets in mining and industrial logistics.

## Key Documents

* **[Golden Data Set Architecture Specification](docs/golden_data_set_architecture.md)**: Comprehensive architectural specification detailing:
  * The 5-layer edge value triage engine (Deterministic, Active Learning, Vector Embeddings, Campaigns, Stratified Sampling)
  * The multi-tier transport hierarchy (On-Truck $\rightarrow$ Depot Wi-Fi 6 $\rightarrow$ Satellite $\rightarrow$ Sneakernet)
  * Data reduction techniques (temporal ring buffers, frustum & channel pruning, frame decimation)
  * Sizing and quantitative data reduction funnels (500 TB $\rightarrow$ 5 TB $\rightarrow$ <50 GB)
  * Standardized JSON Metadata Schema
  * Site depot server storage lifecycle & retention policies
  * 4D world model auto-labeling and mining semantic ontology
  * Commercial product landscape & vendor evaluation (Kognic, Akridata, Voxel51, AWS IoT FleetWise, Foxglove MCAP, Applied Intuition)
  * 4-phase implementation roadmap
  * Architectural hardening & operational review alignment (PTP OCXO holdover, 10 Gbps optical dock, vector versioning, 3 DWPD NVMe grace policy)
