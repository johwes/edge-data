# **Scaled Edge Data Triage Architecture: Industry Benchmarking, Technical Validation, and Technology Mapping**

> [!NOTE]
> **Archival Notice:** This document represents an earlier monolithic draft and has been superseded by the modular Golden Data Set (GDS) Architecture specification series. Please refer to the primary master document: [**Master System Architecture & Site Infrastructure Overview**](./golden_data_set_architecture.md) and modular specifications [`01_`](./01_data_filtering_and_triage.md) through [`05_`](./05_commercial_landscape_and_roadmap.md).

## **1\. Executive Feasibility and Validation Scorecard**

Autonomous haulage operations across remote surface mines, mineral extraction quarries, and bulk logistics corridors operate against an unforgiving physical networking bottleneck1. A production fleet of one hundred class-8 autonomous haul trucks, each equipped with multi-modal sensor arrays comprising 128-beam mechanical and solid-state LiDARs, 4D imaging radars, multiple 8-megapixel automotive cameras, high-rate inertial measurement units (IMUs), and full-chassis Controller Area Network (CAN) telemetry taps, continuously produces between 3 TB and 5 TB of uncompressed perception data per machine per 24-hour operational cycle1. Across an entire site, aggregate data generation scales to approximately 500 TB every day1.  
Conversely, wide-area network (WAN) backhaul at these remote extraction sites is severely constrained1. Uplinks provisioned through commercial low Earth orbit (LEO) satellite constellations, such as Starlink, or carrier cellular backhauls typically deliver between 10 Mbps and 25 Mbps of sustained upload throughput1. This restricts cumulative site egress to a narrow window of 100 GB to 250 GB per day1. Consequently, approximately 99.95% of the raw sensor data generated within the pit cannot physically leave the site over wireless wide-area connections1.  
Transitioning from an unmanaged ingest strategy to an edge-to-cloud data curation architecture resolves this disparity1. Evaluating information entropy directly on vehicle edge computers and local depot storage appliances compresses the daily 500 TB sensor flood into a curated Golden Data Set (GDS) of safety-critical, novel, and operationally diverse events1. This pipeline reduces daily cloud ingest to between 20 GB and 50 GB1.  
The technical feasibility of this multi-tier architecture is rated as high, provided that specific hardware and algorithmic hardening protocols are enforced to mitigate vector space drift, precision clock phase slips, depot physical connection limits, and solid-state drive thermal degradation1.

| Architecture Tier | Operational Stage | Daily Fleet Data Volume | Retention Ratio | Primary Processing Mechanism |
| :---- | :---- | :---- | :---- | :---- |
| **Tier 0** | Vehicle Ring Buffering | 500,000 GB/day | 100.0% | Continuous volatile circular buffering in high-speed RAM and NVMe storage1. |
| **Tier 1** | On-Vehicle Triage | 5,000 to 10,000 GB/day | 1.0% – 2.0% | Kinematic triggers, model uncertainty, latent novelty, and channel pruning1. |
| **Tier 2** | Depot Edge NAS | 2,500 to 5,000 GB/day | 0.5% – 1.0% | Coreset deduplication, cross-fleet clustering, and rolling buffer staging1. |
| **Tier 3** | Central Cloud Ingest | 20 to 50 GB/day | \< 0.01% | Metadata-first selective queries and 4D auto-labeling pipeline ingest1. |

| Evaluation Dimension | Feasibility Grade | Analytical Findings and Technical Validation Status | Architecture Vulnerabilities and Dependencies |
| :---- | :---- | :---- | :---- |
| **Edge Triage Mechanics** | **A** | Multi-criteria edge filtering successfully prunes 98% to 99% of low-entropy miles without dropping safety events1. | Miscalibrated epistemic uncertainty heads risk data blind spots or candidate buffer flooding1. |
| **Depot Physical Ingestion** | **B+** | High-speed automated physical mating meets 15-minute scheduled dwell requirements1. | Heavy dust and vehicle multipath degrade wireless offloads; automated physical connection is mandatory1. |
| **Latent Novelty Engine** | **B** | Low-dimensional metric embeddings (![][image1]) provide fast semantic outlier detection1. | Over-the-air vision model updates induce representation drift, invalidating static baseline indices10. |
| **Timing Synchronization** | **A-** | Sub-microsecond sensor alignment is achievable during extended GNSS denial via disciplined holdover1. | Quartz crystal oscillators drift unacceptably; chip-scale atomic clocks are required for deep pits6. |
| **Financial Cost-Efficiency** | **A+** | Compressing site data to \<50 GB/day reduces cloud storage, compute, and labeling expenses by over 99.7%1. | Requires front-loaded capital expenditures for ruggedized in-cab compute and depot storage nodes1. |

Directly ingesting an uncurated 500 TB/day into commercial hyperscaler object storage generates approximately 15 PB of new data monthly1. At standard cloud object storage pricing of \$0.023 per gigabyte, baseline storage costs alone exceed \$345,000 per month, compounding continuously without accounting for API requests, compute cycles, and network egress1.  
Furthermore, human annotation of multi-sensor 3D point clouds, 4D radar tracks, and multi-view video streams costs between \$3 and \$8 per synchronized frame1. Attempting to annotate even a fraction of this uncurated volume would rapidly exhaust program budgets1.  
By deploying on-vehicle triage to prune candidate events down to 5 to 10 TB/day, and running depot-level coreset reduction algorithms to extract between 20 GB and 50 GB per day of high-entropy snippets, recurring cloud ingestion expenses drop below \$1,100 per month1. Capital expenditure is redirected toward on-vehicle storage arrays and on-site depot infrastructure, amortizing hardware costs across years of continuous production1.

## **2\. Industry Reference Architecture Comparison**

Autonomous vehicle operations across industrial mining, commercial long-haul trucking, passenger transport, and urban robotaxis navigate distinct operational constraints1. These structural constraints dictate data harvesting ratios, edge filtering techniques, and simulation integration strategies1.

| Architectural Dimension | Remote Mining Haulage (Proposed Pipeline) | Heavy Mining OEMs (Caterpillar / Komatsu) | Autonomous Trucking (Kodiak Robotics) | Mass Passenger AVs (Tesla Data Engine) | Urban Robotaxis (Waymo Driver) |
| :---- | :---- | :---- | :---- | :---- | :---- |
| **Operational Design Domain** | Deep open-pit benches, crushers, dumps, private haul roads1. | Structured mining benches, waste dumps, crusher ramps1. | Long-haul interstate highways and private energy corridors14. | Global consumer roadways, mixed urban and highway18. | Dense urban cores, complex intersections, arterials16. |
| **Cloud Uplink Ingest Ratio** | **\< 0.01%** uploaded over WAN (\<50 GB/day from 500 TB)1. | **\< 0.005%** over wireless; strictly critical telemetry and fault codes1. | **\< 0.05%** continuous; critical safety events and target scenarios22. | **\< 0.1%**; micro-classifier triggers and shadow mode clips1. | **\~0.5% – 2.0%**; localized depot fiber offloads with cloud active curation24. |
| **Directed Triage Mechanics** | Kinematic bounds, epistemic entropy, vector novelty, dynamic schemes, ODD anchors1. | Deterministic fault codes, geofence breaches, payload limits, obstacle stops1. | Kinematic exceptions, planner-perceiver deltas, remote ops intervention23. | Fleet-wide micro-classifiers, shadow mode path divergence, disengagements1. | Causal event logs, planner uncertainty metrics, regression triggers16. |
| **Edge Compute Footprint** | Multi-modal perception compute, NPU embedding extractor, U.2/U.3 NVMe1. | Industrial embedded controllers, telemetry gateway, circular crash logger21. | Rugged dual-stack commercial vehicle compute, local high-speed NVMe17. | In-house dual FSD System-on-Chip (SoC) executing primary and shadow heads1. | Automotive-grade custom computing cluster with redundant multi-sensor units16. |
| **Depot Edge Responsibilities** | 250 TB NAS, automated docking offload, coreset deduplication, vector re-indexing1. | Telemetry offload, scheduled maintenance diagnostics, raw log archive dumps21. | Terminal-based high-speed offload, automated safety inspection diagnostics17. | Minimal depot processing; consumer Wi-Fi uploads directly to central clusters18. | Extensive depot network infrastructure, complete raw shift ingest, autocalibration24. |
| **Simulation Integration** | Closed-loop export to ASAM OpenSCENARIO, synthetic near-miss variations1. | Fleet management replays, route optimization, mine digital twins2. | Daily simulation operations, virtual incident replay, parameter variations23. | Purely data-driven neural network weight retraining, autolabeling loops18. | High-fidelity multi-sensor simulation pipelines (e.g., Carcraft, world models)16. |

Industrial mining OEMs such as Caterpillar (MineStar) and Komatsu (FrontRunner) prioritize network Quality of Service (QoS) above all else1. Because open-pit operations rely on private LTE and 5G networks to stream safety-critical emergency stop heartbeats, precision dispatch directives, and vehicle tracking coordinates, mining network architectures forbid opportunistic streaming of rich multi-modal sensor logs over production spectrum1.  
Data harvesting in these operational environments is structurally split1. Low-frequency vehicle telemetry, fault codes, and payload data are broadcast continuously to the central Fleet Management System (FMS), whereas high-bandwidth perception diagnostics remain sequestered inside localized circular loggers1. These dense diagnostic logs are only extracted when a machine enters an equipment workshop or experiences an incident1.  
In contrast, commercial automotive and long-haul trucking stacks (Tesla, Kodiak Robotics) leverage active learning feedback loops1. Tesla’s architecture executes lightweight neural triggers and runs experimental models in "shadow mode"1. When the active driving policy diverges from an unprompted background shadow network, or when a human driver disengages the system, the vehicle preserves a rolling temporal buffer spanning ten seconds before and after the event1.  
Kodiak Robotics applies a comparable selective logging paradigm to commercial trucking, capturing kinematic outliers and perceptual edge cases to drive daily simulation and regression pipelines23.  
Waymo captures extensive multi-modal logs from its urban robotaxi fleet, but its operational topology relies on urban maintenance depots equipped with high-speed local networking16. Robotaxis return frequently to centralized service depots, offloading dense multi-terabyte drives over dedicated ground connections into enterprise computing clusters where centralized curation engines extract training batches24.  
For remote heavy logistics, where neither urban fiber depots nor pervasive wireless bandwidth exist, the architecture must synthesize the strict bandwidth isolation of industrial mining with the active edge triggers pioneered by commercial autonomous vehicle developers1.

## **3\. Edge Case Hardening Plan**

### **3.1 Vector Space Drift under Over-the-Air Model Updates**

The architecture uses a lightweight vision encoder running on an edge neural processing unit (NPU) to compress multi-camera video streams into a 128-dimensional or 256-dimensional metric vector, firing an offload trigger when the cosine distance between the current scene and an onboard baseline index exceeds a novelty threshold (![][image2])1.  
However, updating the vehicle's perception vision backbone via an Over-the-Air (OTA) deployment shifts the underlying latent manifold from ![][image3] to ![][image4]10. Comparing embeddings generated by the new backbone against a historical baseline computed with the legacy backbone causes representation collapse10. This mismatch triggers either persistent false-positive collection avalanches that saturate onboard storage, or severe false-negative blind spots that miss critical environmental anomalies10.  
To maintain consistent edge novelty scoring across OTA deployment cycles without requiring dual backbones on power-constrained compute units, three complementary mechanisms are enforced:

\[Edge Vehicle Perception\]  
       │  
       ▼  
Incoming Video Frame (x)  
       │  
       ▼  
Perception Backbone \[phi\_new\]  ────────►  Raw Latent Vector (v\_new)  
                                                    │  
                                                    ▼  
                                       Query Drift Compensation:  
                                       v\_comp \= v\_new \- Delta\_{old-\>new}  
                                                    │  
                                                    ▼  
                                       k-NN Novelty Evaluation:  
                                       d(v\_comp, V\_baseline) \> tau\_novelty  
                                                    │  
                                                    ▼  
                                       \[Candidate Trigger Evaluation\]

\[Depot Edge Infrastructure (Asynchronous Task)\]  
       │  
       ▼  
1\. Receive OTA Manifest with new model hash (e.g., b9e01d5f348a)  
       │  
       ▼  
2\. Forward-Compatible Transformation (FCT) adapts historical baseline gallery  
       │  
       ▼  
3\. Batch re-indexing computes native phi\_new vectors across local depot NAS  
       │  
       ▼  
4\. Updated k-NN baseline gallery deployed to vehicle fleet during physical docking

First, the machine learning training pipeline implements Backward-Compatible Training (BCT) with relaxed orthogonality constraints12. When training an upgraded vision backbone, the optimization loss function couples task-specific losses with a backward-compatibility constraint:  
![][image5]  
Applying an orthogonal transformation matrix ![][image6] such that ![][image7] preserves the global geometry of the legacy representation space while allowing the new model to learn novel environmental features12. This regularizer ensures that cross-model cosine similarity between new candidate query vectors and legacy baseline representations remains geometrically consistent during initial rollout11.  
Second, the edge runtime implements zero-shot Query Drift Compensation (QDC)10. Prior to fleet-wide deployment, a small calibration dataset of operational scenes is passed through both the legacy and upgraded encoders to compute a global drift vector:  
![][image8]  
This compensation offset is stored directly within the on-vehicle runtime10. When the vehicle evaluates incoming frames, the compensated query vector ![][image9] is mapped into the legacy baseline index, suppressing artificial novelty spikes caused purely by coordinate translation10.  
Third, gallery modernization is offloaded asynchronously to the on-site Depot Edge NAS1. Every recorded candidate snippet is indexed with its corresponding perception\_model\_hash1. When an OTA update is released, the depot server executes a background batch job utilizing a trained forward-compatible feature upgrade module, converting the local historical gallery to the new embedding representation1.  
Once updated, the freshly compiled index is synchronized to the vehicle's onboard vector search engine during its next scheduled service dwell, completing representation transition across the fleet1.

### **3.2 Precision Time Protocol Holdover under GNSS-Denied Conditions**

Autonomous haul trucks operating in deep open-pit extraction benches regularly experience GNSS RTK lock dropouts, carrier-phase cycle slips, and satellite constellation shadowing caused by steep pit highwalls1. Multi-modal sensor fusion depends on strict temporal synchronization1.  
For a haul truck traveling at 36 km/h (10.0 m/s), a timing desynchronization of just 10 milliseconds between an 8MP camera exposure and a 10 Hz LiDAR sweep produces a 10-centimeter spatial registration error1. Such misalignment induces bounding-box jitter, distorts 3D occupancy grids, and invalidates offline 4D auto-labeling reconstructions1. To maintain high-fidelity point cloud and imagery registration, timing drift must remain strictly below 1.0 microsecond across uninterrupted 24-hour production shifts1.

\[Multi-Constellation GNSS Antenna Array\]  
                    │  
                    ▼ (1PPS / ToD Reference)  
\+───────────────────────────────────────────────────────────+  
| Vehicle Grandmaster Clock Gateway                         |  
|                                                           |  
|   GNSS Available: Disciplines DPLL & Atomic Oscillator    |  
|   GNSS Denied:    Enters Hardware Holdover State          |  
|                   Microchip SA.45s CSAC / SiTime MEMS     |  
|                   (Drift \< 0.8 microseconds per 24 hours) |  
\+───────────────────────────────────────────────────────────+  
                    │  
                    ▼ (IEEE 1588 PTPv2 Boundary Clock Distribution)  
     ┌──────────────┼──────────────┬──────────────┐  
     ▼              ▼              ▼              ▼  
Cameras (GMSL2)   LiDARs     4D Radar Arrays   IMU / Chassis CAN

When standard quartz oscillators lose external GNSS discipline, their uncompensated frequency drift rapidly accumulates phase error, making them inadequate for production mining environments6. The vehicle gateway must incorporate specialized timing hardware to bridge prolonged satellite outages1.

| Timing Reference Technology | Frequency Stability (σy​ at τ=1000s) | Typical Daily Frequency Drift | Maximum Time Error after 24h Denial | Sub-Microsecond Holdover Duration | Operational Viability in Deep Pits |
| :---- | :---- | :---- | :---- | :---- | :---- |
| **Standard Quartz TCXO** | **![][image10]** | **![][image11]** / day | ![][image12] (5.0 ms)6 | \< 30 seconds | **Unacceptable:** Causes severe spatial registration errors within minutes1. |
| **Stratum 3E Quartz OCXO** | **![][image13]** | **![][image14]** / day | ![][image15] to ![][image16] \[cite: 38, 39\] | \~ 2 to 4 hours | **Marginal:** Requires recurring surface fixes between pit haulage cycles. |
| **Ruggedized MEMS Super-TCXO / OCXO** | **![][image13]** | **![][image17]** / day | ![][image18] over 24h38 | \~ 16 to 24 hours38 | **High:** Excellent resistance to vehicle vibration, mechanical shock, and thermal transients38. |
| **Chip-Scale Atomic Clock (Microchip SA.45s / SA.65)** | **![][image19]** \[cite: 13\] | ![][image20] **/ month** \[cite: 13\] | ![][image21] **over 24h** \[cite: 6\] | **\> 24 to 48 hours** \[cite: 6\] | **Mission-Critical:** Guarantees sub-microsecond PTP alignment throughout continuous deep-bench operations1. |

The on-vehicle network architecture incorporates an automotive IEEE 1588 PTPv2 boundary clock switch disciplined by a Chip-Scale Atomic Clock (e.g., Microchip SA.45s)6. Consuming under 120 mW of power and occupying less than 17 cm³ of volume, the CSAC integrates a coherent population trapping (CPT) rubidium physics package6.  
When the primary GNSS receiver reports Loss-of-Lock due to bench geometry, a digital phase-locked loop (DPLL) transitions into holdover mode41. Because the atomic transition frequency of rubidium provides long-term stability, clock drift is constrained below 0.8 microseconds over a continuous 24-hour outage6.  
This keeps spatial registration error below 0.01 mm at haul speeds, maintaining temporal consistency across all perception sensors and downstream 4D reconstruction pipelines1.

### **3.3 Physical Depot Ingestion and Environmental Degradation Mitigation**

Industrial Wi-Fi 6 (802.11ax) and 60 GHz millimeter-wave (802.11ad/ay) links degrade significantly when deployed in active mining operations1. Airborne mineral dust clouds scatter high-frequency radio waves, while metallic reflections from neighboring haul trucks, excavators, and structural steel gantries create heavy multipath interference1. Under typical operating conditions, theoretical multi-gigabit connections fall to sustained transfer rates of 150 Mbps to 300 Mbps1.  
At an average throughput of 200 Mbps, offloading a standard 50 GB candidate payload takes more than 33 minutes1. Haul trucks operate on strict production schedules, pausing only for 15-minute intervals during shift-change fueling stops1. Relying solely on wireless offload mechanisms under these conditions causes candidate logs to back up on vehicles, eventually triggering buffer overwrites and critical data loss1.

Scheduled Service / Fueling Bay Infrastructure  
       │  
       ▼  
Truck Enters Alignment Guide Curbs  
       │  
       ▼  
Automated Robotic Mating (Stäubli QCC-5000 / Cavotec Interface)  
       │  
       ├─► High-Pressure Compressed Air Purge Clears Dust Shutter  
       │  
       ├─► Multi-Pole Connection Engaged (SAE J3105/3 Power \+ 10GBASE-SR Optical)  
       │  
       ▼  
High-Speed Direct Offload Initiated:  
50 GB Candidate Payload Transferred to Depot NAS in \< 45 Seconds  
       │  
       ▼  
\[If Physical Mating Fails\] ──► Wireless Fallback Activated (Wi-Fi 6 / VFO Link)  
                                │  
                                ▼  
                                Dynamic Offload Prioritization Engine Sheds  
                                Class C Baseline Samples to Protect Storage

To resolve this offload constraint, the architecture establishes a dual-mode ingestion topology combining automated physical coupling with adaptive wireless fallback1:  
The primary transfer path utilizes an automated connection interface integrated directly into stationary service and fueling islands (e.g., Stäubli QCC-5000 series or Cavotec automated systems)8. These interfaces, designed to standard SAE J3105/3 industrial form factors, incorporate high-power contacts alongside an integrated 10GBASE-SR or 25GBASE-SR fiber-optic line within an IP55/IP56 sealed housing8.  
To prevent mine dust from fouling the internal optics, the ground mating arm incorporates a high-pressure compressed air purge nozzle that blasts the vehicle's protective shutter clean immediately before physical coupling occurs8. Operating across a dedicated 10 Gbps optical channel, a 50 GB candidate payload transfers in under 45 seconds, completing well within the 15-minute fueling window1.  
Where mechanical docking infrastructure is not yet installed, directed Free-Space Optical transceivers—termed Virtual Fiber Optics (VFO)—provide a line-of-sight optical alternative that avoids RF spectrum saturation and delivers transfer speeds 50 to 100 times faster than Wi-Fi9.  
If a truck is forced to offload over degraded Wi-Fi 6 links at an auxiliary parking bay, the vehicle's offload agent activates an adaptive shedding protocol1:

* *Class A (Critical Kinematics):* Emergency stop events, chassis limit breaches, and manual overrides are transferred immediately1.  
* *Class B (High Uncertainty):* Model uncertainty clips and vector novelty events are transferred as bandwidth permits1.  
* *Class C (Nominal Baseline):* Stratified operational design domain (ODD) anchor samples are dropped from local queues to protect ring buffer integrity1.

### **3.4 Ruggedized Storage Endurance, Power-Loss Protection, and Thermal Management**

Continuous multi-modal ring buffering imposes high write wear on local storage1. Logging 3 TB to 5 TB per vehicle per 24 hours requires a sustained sequential write throughput between 35 MB/s and 60 MB/s, with transient burst writes reaching 450 MB/s when flushing high-priority multi-camera buffers to disk1.  
In non-air-conditioned vehicle equipment bays, ambient operating temperatures regularly reach 45°C to 50°C1. Heat generated by onboard GPUs, NPUs, and power converters can push internal storage drive cases past 70°C1. Standard commercial solid-state drives (SSDs) begin aggressive thermal throttling above 70°C, cutting write speeds to prevent damage15. This throttling causes write queues to block, dropping incoming frames from the autonomy stack1.

Continuous Sensor Streams (35-60 MB/s Sustained Write Workload)  
                     │  
                     ▼  
Dedicated PCIe Gen4 x4 Controller Bus (Direct Memory Access)  
                     │  
                     ▼  
Industrial U.2/U.3 NVMe SSD (Micron 7450 MAX / Solidigm D7-P5810)  
\[Conduction-Cooled Enclosure Coupled to Vehicle Chassis Heat-Sink\]  
                     │  
                     ▼  
Continuous SMART Controller Telemetry Monitoring (Polling Interval: 5s)  
                     │  
     ┌───────────────┴───────────────┐  
     ▼                               ▼  
Case Temp \< 70°C                Case Temp \> 75°C  
Nominal Operation               Activate Chassis Auxiliary Heat-Pipes  
                                Engage Storage Capacity Protection Rules:  
                                ├─► 80% Full: Drop Filter 5 Nominal Anchors  
                                ├─► 85% Full: Quantize LiDAR to 16-bit Fixed-Point  
                                ├─► 90% Full: Prune Peripheral Camera Frustums  
                                └─► 95% Full: Lock Safety Events, Purge Non-Critical

To prevent data corruption, flash wearout, and thermal write stalls under these operating conditions, the on-vehicle storage subsystem incorporates three protective engineering controls1:

> 1. **Drive Endurance Sizing:** Storage modules mandate enterprise-grade U.2 or U.3 NVMe SSDs rated for ![][image22] Drive Writes Per Day (DWPD) over a 5-year operating warranty (e.g., Micron 7450 MAX or Solidigm D7-P5810)1. Standard datacenter SSDs rated for 1 DWPD under continuous 24/7/365 writes exhaust their Program/Erase (P/E) cycles within 18 months1. In contrast, a 3 DWPD 15.36 TB drive delivers over 84 Petabytes Written (PBW), providing long-term endurance across multi-year mining deployments1.  
> 2. **Level-4 Hardware Power-Loss Protection (PLP):** Drives must incorporate hardware PLP backed by discrete onboard tantalum capacitor arrays46. Industrial haul trucks experience sudden electrical disconnections, emergency master switch trips, and alternator voltage sags1. Hardware PLP delivers sustained hold-up power during unexpected power cuts, giving the SSD controller enough time to flush in-flight DRAM write caches and flash translation layer (FTL) mapping tables into non-volatile NAND blocks46.  
> 3. **Thermal Management and Dynamic Storage Degradation:** Drives are housed in sealed, IP67-rated conduction enclosures mounted directly to the vehicle chassis frame, utilizing high-conductivity thermal interface materials to keep controller junction temperatures below 65°C1.

If operational delays prevent a truck from reaching an offload station and storage capacity exceeds safe margins, the edge storage daemon activates a tiered eviction policy to preserve system stability1:

* *Threshold 1 (Capacity \> 80%):* Purge Filter 5 nominal stratified baseline samples from NVMe staging1.  
* *Threshold 2 (Capacity \> 85%):* Quantize LiDAR point cloud data from 32-bit floats to 16-bit fixed-point representations and crop points beyond 50 meters1.  
* *Threshold 3 (Capacity \> 90%):* Drop peripheral camera frustums entirely, preserving only the forward-facing 8MP camera, primary 128-beam LiDAR, and chassis CAN telemetry1.  
* *Threshold 4 (Capacity \> 95%):* Lock all Filter 1 deterministic safety incidents as immutable records; delete un-offloaded Filter 2 uncertainty snippets to keep real-time operating buffers available1.

## **4\. Open-Source and Standards Technology Matrix**

Rather than creating custom proprietary protocols at every pipeline layer, the triage architecture is built upon mature open standards and high-performance open-source middleware1.

| Architecture Tier | Tool or Open Standard | Licensing Model | Edge / Embedded Suitability | Primary Architectural Functionality | Architectural Limitations and Trade-offs |
| :---- | :---- | :---- | :---- | :---- | :---- |
| **Tier 1: Serialization** | **Foxglove MCAP** | Apache 2.0 | **Native** (C++, Rust, Python, Go)1 | High-performance, row-oriented, append-only container format for multi-modal robotics logs1. | Embedded indexing adds minor file size overhead; requires dedicated decoders for custom message types1. |
| **Tier 1: Intra-Node IPC** | **eProsima Fast DDS** | Apache 2.0 | **Native** (C++, RTPS compliant)19 | Ultra-low latency, deterministic inter-process communication across on-vehicle compute boards19. | Multicast participant discovery triggers packet floods across lossy or routed networks19. |
| **Tier 1 & 2: Edge Transport** | **Eclipse Zenoh** | EPL 2.0 / Apache 2.0 | **Native** (Rust, C, Python; low memory footprint)19 | Unified data plane bridging vehicle networks to depot servers over wireless links without multicast storms19. | Requires running a lightweight routing daemon (zenohd); less prevalent in legacy automotive tooling48. |
| **Tier 1: Embedded Search** | **USearch (Unum)** | Apache 2.0 | **Native** (Header-only C++11, SIMD/NEON optimized)51 | Lightweight HNSW vector engine running real-time novelty checks (![][image1]) on NPUs1. | In-memory index architecture requires explicit serialization to maintain state across reboots51. |
| **Tier 2: Depot Vector DB** | **LanceDB** | Apache 2.0 | **High** (Embedded Rust, Python)52 | Serverless, disk-backed multimodal vector database built on Lance columnar format for depot search52. | Optimized for local NVMe access; distributed multi-server scaling requires custom coordination logic. |
| **Tier 2: Visual Curation** | **FiftyOne (Voxel51)** | Apache 2.0 | **Medium** (Python, MongoDB backend)1 | Evaluates visual uniqueness, detects distribution shifts, and identifies redundant samples7. | Python runtime overhead; requires automated containerization to operate headlessly at the depot1. |
| **Tier 2: Outlier Detection** | **Cleanlab** | AGPLv3 | **Medium** (Python)54 | Confident learning algorithms to detect label noise, estimate out-of-distribution density, and prune data54. | Geared toward classification and tabular data; requires pre-extracted feature vectors for point clouds54. |
| **Tier 3: 4D Auto-Labeling** | **EmerNeRF** | Open Research / Apache 2.0 | **Cloud / Depot GPU Cluster** \[cite: 36, 55\] | Self-supervised 4D neural radiance field decomposing dynamic scenes into static, dynamic, and flow fields36. | High computational requirements (30 to 120 minutes of GPU training per sequence)36. |
| **Tier 3: Scene Splatting** | **Street Gaussians** | Open Research | **Cloud / Depot GPU Cluster** \[cite: 56\] | 4D Gaussian Splatting for driving scenes, modeling dynamic objects and static haul surfaces56. | Emerging research project; relies on accurate bounding-box priors for complex equipment shapes56. |
| **Cross-Tier Simulation** | **ASAM OpenSCENARIO & OpenDRIVE** | ASAM Open Standard57 | **Cross-Platform Standard** \[cite: 29\] | Standardized formats for dynamic scenario behavior and static road surface network definitions29. | Complex XML/UML schema specifications; requires specialized conversion tools for raw telemetry logs29. |

A central architectural decision in distributed robotics is resolving the friction between low-latency onboard inter-process communication (IPC) and volatile vehicle-to-depot networking19.  
While Data Distribution Service (DDS) implementations like eProsima Fast DDS and CycloneDDS provide nanosecond-level shared-memory messaging across isolated on-vehicle compute boards, their discovery mechanisms break down over wireless links19. DDS relies on continuous multicast Simple Participant Discovery Protocol (SPDP) broadcasts19.  
When haul trucks traverse fluctuating wireless coverage zones near depot bays, DDS discovery protocols initiate retransmission floods, saturating wireless bandwidth, exhausting CPU cycles, and dropping telemetry packets19.

\[On-Vehicle Internal Electronics Bus\]  
Cameras, LiDARs, Radars, Planners  
               │  
               ▼ (Low-Latency Shared Memory / RTPS)  
      \[eProsima Fast DDS\]  
               │  
               ▼ (Localhost Topics Only)  
      \[zenoh-bridge-dds Plugin\]  
               │  
═══════════════╪══════════════════════════════════════════════  
\[Vehicle-to-Depot Wireless / Industrial Wi-Fi 6 Link\]  
               │  
               ▼ (Eclipse Zenoh over TCP/QUIC with Gossip Discovery)  
        \[Depot zenohd Router\]  
               │  
═══════════════╪══════════════════════════════════════════════  
\[Site Depot Staging Infrastructure\]  
               │  
               ▼  
   \[Depot Edge NAS Ingestion Pipeline\]

The production pipeline deploys a hybrid transport architecture to resolve this challenge48:

* **On-Vehicle Network:** DDS is restricted to the truck's internal loopback interface, managing real-time sensor processing and control loops in an isolated domain48.  
* **Depot Network:** Eclipse Zenoh handles all external communications between vehicles and the depot infrastructure48.

A zenoh-bridge-dds translation plugin runs on the vehicle's gateway computer48. This plugin subscribes to local DDS candidate topics and forwards them over TCP or QUIC to the depot's zenohd routing daemon19.  
Zenoh replaces multicast broadcasting with set-theoretic resource generalizations and gossip-based scouting, maintaining reliable data flow over lossy wireless links without generating network storms19.

## **5\. Commercial Vendor Landscape and Build vs. Buy Recommendations**

To balance engineering effort against time-to-deployment, commercial platforms across all four pipeline layers are evaluated below1.

| Operational Tier | Vendor / Platform | Primary Product Strengths | Architecture Limitations | Strategic Recommendation |
| :---- | :---- | :---- | :---- | :---- |
| **Tier 1: Edge Ingest** | **AWS IoT FleetWise** | Dynamic declarative scheme deployment, CAN signal parsing, condition-based edge filtering without firmware re-flashing1. | Deeply tied to the AWS cloud ecosystem; lacks native parsing support for high-throughput uncompressed LiDAR point clouds1. | **Hybrid Integration:** Deploy FleetWise for vehicle kinematics, CAN telemetry, and Filter 1/4 rules; wrap it with custom edge agents for raw MCAP sensor buffers1. |
| **Tier 1: Vehicle Diagnostics** | **Vector Informatik (CANape / VP75x1)** | Industry standard for multi-gigabit sensor data capture, microsecond hardware time-stamping, and ASAM compliance57. | High enterprise licensing costs; proprietary hardware dependency; lacks native cloud-native active learning curation capabilities1. | **Selective Buy:** Deploy on specialized engineering prototype trucks; implement lightweight C++/Rust logging agents on production haulers1. |
| **Tier 2: Depot Edge Curation** | **Akridata (DataSense)** | Visual Coreset sampling algorithms, edge deduplication, eliminating 90%+ of redundant video frames before cloud upload1. | Closed-source proprietary software; requires dedicated edge compute nodes at depot NAS installations1. | **Commercial Buy:** Deploy at depot fueling bays to automate visual candidate deduplication prior to WAN transmission1. |
| **Tier 2: Dataset Exploration** | **Voxel51 (FiftyOne Enterprise)** | Centralized visual dataset exploration, FiftyOne Brain similarity indexing, distribution shift detection1. | Geared primarily toward server/cloud curation; requires custom orchestration to automate headless depot pruning1. | **Buy / Integrate:** Adopt as the unified catalog platform for the Depot NAS and Cloud GDS tiers1. |
| **Tier 3: 4D Auto-Labeling** | **Kognic** | Specialized for multi-sensor temporal fusion (LiDAR, Camera, Radar), active learning copilot, and dataset quality assurance1. | Enterprise pricing structure; requires pre-curated candidate data (cannot ingest raw 500 TB/day site feeds directly)1. | **Commercial Buy:** Integrate as the primary platform for generating verified 4D ground-truth labels from curated GDS snippets1. |
| **Tier 3: Telemetry Observability** | **Sift** | High-frequency physical machine observability, sub-second telemetry anomaly triage, Apache Arrow/Parquet data stack35. | Focused on time-series telemetry and system health rather than 3D LiDAR/video point cloud computer vision pipelines35. | **Commercial Buy:** Deploy to unify chassis CAN, PTP timing health, and hardware telemetry triage across the fleet64. |
| **Tier 3: Simulation Coupling** | **Applied Intuition (Strada / Simian)** | Automated scenario extraction from real drive logs, conversion to ASAM OpenSCENARIO, synthetic edge-case permutation1. | Complex enterprise stack with high licensing tiers; requires well-structured input data1. | **Commercial Buy:** The premier solution for closing the active learning loop from real-world edge cases to synthetic simulation1. |

Building custom in-house software across the entire data lifecycle requires significant long-term engineering overhead1. A balanced strategy combines specialized commercial off-the-shelf platforms with focused internal development1:  
At the on-vehicle edge tier, internal development should focus on writing high-performance C++ and Rust agents to manage continuous circular memory buffers using the open Foxglove MCAP format, coupled with the USearch library for local NPU novelty lookups1. Dynamic trigger distribution and vehicle bus telemetry are managed through commercial agents: AWS IoT FleetWise provides declarative rule updates over the air, while Sift's embedded agent ingests high-frequency CAN, IMU, and PTP clock health metrics1.  
At the depot edge server tier, commercial platforms streamline local operations1. The site NAS pairs Akridata DataSense for automated video coreset reduction with Voxel51 FiftyOne Enterprise for cross-fleet similarity indexing and distribution shift detection1. Depot vector embeddings are organized within LanceDB, enabling fast local querying without ongoing infrastructure maintenance52.  
At the central cloud tier, incoming snippets are processed through specialized commercial tools1. Kognic provides multi-modal 4D temporal sensor fusion, auto-labeling verification, and active learning curation1.  
Extracted edge cases and near-miss encounters pass directly into Applied Intuition Strada, where real-world driving snippets are automatically parameterized into ASAM OpenSCENARIO virtual environments for simulation and regression testing across the fleet1.

## **6\. Actionable Revision Items for Architecture v2.0**

### **6.1 Production Metadata Schema Specification (gds\_metadata\_v2.json)**

The production metadata schema is upgraded to track model hashes, directional embedding drift compensation parameters, hardware-backed PTP clock holdover health, and degraded offload transfer states1.

JSON  
{  
  "\$schema": "https\://specs.autonomy-mining.org/v2/gds-metadata.json",  
  "snippet\_id": "SNIP-20261002-TRK042-00941",  
  "truck\_id": "HAUL-TRUCK-042",  
  "site\_id": "MINE-PILBARA-WEST",  
  "timestamp\_utc\_start": "2026-10-02T08:12:10.000000Z",  
  "timestamp\_utc\_trigger": "2026-10-02T08:12:40.000000Z",  
  "timestamp\_utc\_end": "2026-10-02T08:12:55.000000Z",  
  "software\_manifest": {  
    "autonomy\_stack\_version": "v4.14.0-prod",  
    "active\_perception\_hash": "b9e01d5f348a",  
    "previous\_perception\_hash": "a8f90c4e127f",  
    "vector\_space\_version": "v3.2",  
    "active\_harvesting\_campaigns": \["CAMP-2026-BERM-DETECTION"\]  
  },  
  "clock\_synchronization\_telemetry": {  
    "ptp\_profile": "IEEE\_1588\_PTPV2\_BOUNDARY",  
    "master\_oscillator\_type": "MICROCHIP\_SA45S\_CSAC",  
    "gnss\_rtk\_lock\_state": "DENIED",  
    "gnss\_outage\_duration\_seconds": 14280.5,  
    "integrated\_phase\_drift\_microseconds": 0.412,  
    "holdover\_status": "WITHIN\_SUB\_MICROSECOND\_SPEC",  
    "spatial\_registration\_uncertainty\_mm": 0.041  
  },  
  "operational\_context": {  
    "bench\_level\_elevation\_m": \-184.2,  
    "pit\_sector\_geofence": "SECTOR-09-DEEP-SLOPE",  
    "payload\_metric\_tons": 248.6,  
    "speed\_kmh": 26.8,  
    "road\_grade\_percent": \-8.4,  
    "dust\_density\_attenuation\_db": 4.2  
  },  
  "triage\_triggers": \[  
    {  
      "trigger\_tier": "FILTER\_1\_DETERMINISTIC",  
      "source\_subsystem": "chassis.traction\_controller",  
      "metric\_name": "wheel\_slip\_ratio",  
      "threshold": 0.15,  
      "measured\_value": 0.28,  
      "action\_taken": "TORQUE\_DERATE"  
    },  
    {  
      "trigger\_tier": "FILTER\_3\_VECTOR\_NOVELTY",  
      "source\_subsystem": "perception.vision\_encoder",  
      "metric\_name": "cosine\_distance\_compensated",  
      "threshold": 0.72,  
      "measured\_value": 0.89,  
      "drift\_compensation\_applied": true  
    }  
  \],  
  "embedding\_payload": {  
    "dimensions": 128,  
    "model\_backbone\_hash": "b9e01d5f348a",  
    "drift\_compensation\_vector\_norm": 0.0241,  
    "vector\_data": \[0.0381, \-0.1422, 0.8912, 0.0054, \-0.0612\]  
  },  
  "offload\_lifecycle": {  
    "offload\_interface\_used": "PHYSICAL\_OPTICAL\_DOCK\_10G",  
    "transfer\_duration\_seconds": 38.4,  
    "channel\_pruning\_mask": \[  
      "cam\_front\_center\_8mp",  
      "lidar\_128\_beam\_main",  
      "radar\_4d\_imaging\_front",  
      "vehicle\_telemetry\_bus"  
    \],  
    "storage\_capacity\_at\_offload\_percent": 68.2,  
    "depot\_storage\_uri": "mcap://nas01.depot/staging/20261002/SNIP-20261002-TRK042-00941.mcap"  
  }  
}

### **6.2 Hardware Bill of Materials Additions**

The physical equipment specification for autonomous haul trucks and depot installations is updated to include industrial components designed for demanding field conditions1.

| Subsystem Domain | Specific Component Requirement | Engineering Performance Specifications | Operational Rationale |
| :---- | :---- | :---- | :---- |
| **Precision Time Reference** | Microchip SA.45s CSAC or SiTime SiT7111 Rugged MEMS6. | Allan deviation ![][image23] at 1000s; power consumption ![][image24]; holdover timing drift ![][image21] over 24h6. | Eliminates dependency on continuous GNSS RTK lock in deep open-pit benches1. |
| **Rugged Onboard Storage** | Micron 7450 MAX or Solidigm D7-P5810 U.2/U.3 NVMe44. | Endurance ![][image25] DWPD over 5 years; Level-4 Hardware Power-Loss Protection (PLP); operational case temperature up to 85°C44. | Prevents flash wearout and thermal write throttling in high-temperature vehicle electronics bays1. |
| **Depot Physical Ingest** | Stäubli QCC-5000 X Automated Connector or Cavotec Dock8. | SAE J3105/3 compliant docking head; integrated 10GBASE-SR fiber insert; automated compressed air purge nozzle; IP55/IP56 sealed housing8. | Guarantees offloading 50 GB candidate payloads in under 45 seconds during 15-minute fueling stops1. |
| **Wireless Fallback Link** | In A Blink Virtual Fiber Optics (VFO) Transceiver9. | Line-of-sight optical link; throughput of 2.5 to 10 Gbps; operational range of 10 to 50 meters; IP67 outdoor ruggedization9. | Provides high-speed wireless offloading resistant to RF multipath interference and heavy dust scattering1. |

### **6.3 Configuration Adjustments for Storage and Middleware**

#### **Storage Degradation and Eviction Policy (storage\_eviction\_policy.yaml)**

YAML  
storage\_eviction\_manager:  
  monitored\_mount: "/mnt/nvme\_staging"  
  polling\_interval\_seconds: 5  
  thresholds:  
    nominal\_baseline\_drop:  
      trigger\_capacity\_percent: 80.0  
      action: "PURGE\_FILTER\_5\_ODD\_SAMPLES"  
      log\_level: "INFO"  
    pointcloud\_quantization:  
      trigger\_capacity\_percent: 85.0  
      action: "QUANTIZE\_LIDAR\_16BIT\_CROP\_50M"  
      log\_level: "WARNING"  
    frustum\_pruning:  
      trigger\_capacity\_percent: 90.0  
      action: "DROP\_SECONDARY\_CAMERA\_CHANNELS"  
      retained\_channels: \["cam\_front\_center\_8mp", "lidar\_main", "can\_raw"\]  
      log\_level: "WARNING"  
    emergency\_lockout:  
      trigger\_capacity\_percent: 95.0  
      action: "PRESERVE\_FILTER\_1\_ONLY\_DROP\_UNINDEXED"  
      log\_level: "CRITICAL"

#### **Middleware Bridge and Routing Configuration (zenoh\_bridge\_config.json5)**

Code snippet  
{  
  plugins: {  
    dds: {  
      domain: 0,  
      localhost\_only: true,  
      allow: {  
        publishers: \[  
          "/triage/candidate\_metadata",  
          "/chassis/critical\_kinematics",  
          "/sensors/diagnostics"  
        \],  
        subscribers: \[  
          "/fleetwise/dynamic\_schemes",  
          "/depot/vector\_gallery\_update"  
        \]  
      }  
    }  
  },  
  transport: {  
    unicast: {  
      endpoints: \["tcp/10.240.12.1:7447"\],  
      multicast\_scouting: false  
    },  
    link\_loss\_action: "BUFFER\_IN\_LOCAL\_RING"  
  }  
}

Deploying these configuration profiles hardens the overall edge-to-cloud architecture against environmental dust, mechanical vibration, extreme temperatures, and network isolation1.  
By offloading candidate scenarios deterministically at service bays and filtering repetitive driving sequences on the vehicle, the pipeline extracts maximum informational value from multi-modal sensor streams1.  
This transforms an unwieldy 500 TB daily telemetry flood into an active, cost-efficient, high-entropy Golden Data Set that accelerates autonomy development across remote industrial fleets1.

#### **Works cited**

> 1. golden\_data\_set\_architecture.md  
> 2. A Starlink-connected excavator points to the next phase of, [https\://webiano.digital/a-starlink-connected-excavator-points-to-the-next-phase-of-construction-ai/](https://webiano.digital/a-starlink-connected-excavator-points-to-the-next-phase-of-construction-ai/)  
> 3. (PDF) From Active Safety to Autonomous Drive: Design Pathways for, [https\://www\.researchgate.net/publication/403789754\_From\_Active\_Safety\_to\_Autonomous\_Drive\_Design\_Pathways\_for\_Future\_Vehicles](https://www.researchgate.net/publication/403789754_From_Active_Safety_to_Autonomous_Drive_Design_Pathways_for_Future_Vehicles)  
> 4. LeRobot Community Dataset: Curate 50 Embodiments in FiftyOne, [https\://voxel51.com/blog/lerobot-community-dataset-curation-fiftyone](https://voxel51.com/blog/lerobot-community-dataset-curation-fiftyone)  
> 5. Blog \- Axiom Data Science, [https\://www\.axiomdatascience.com/blog/](https://www.axiomdatascience.com/blog/)  
> 6. Chip-Scale Atomic Clocks (CSAC): GPS-Denied Navigation, [https\://theindex26.com/2026/09/15/chip-scale-atomic-clocks-csac-gps-denied/](https://theindex26.com/2026/09/15/chip-scale-atomic-clocks-csac-gps-denied/)  
> 7. FiftyOne Brain, [https\://docs.voxel51.com/brain/](https://docs.voxel51.com/brain/)  
> 8. QCC connectors for fast charging systems \- Stäubli, [https\://www\.staubli.com/cz/en/electrical-connectors/products/multi-pole-connectors/qcc.html](https://www.staubli.com/cz/en/electrical-connectors/products/multi-pole-connectors/qcc.html)  
> 9. In a Blink: Un-Hackable Data Transfer Solutions, [https\://inablink.zone/](https://inablink.zone/)  
> 10. enabling compatibility in continual learning of retrieval embedding, [https\://raw.githubusercontent.com/mlresearch/v330/main/assets/goswami26a/goswami26a.pdf](https://raw.githubusercontent.com/mlresearch/v330/main/assets/goswami26a/goswami26a.pdf)  
> 11. Metric Compatible Training for Online Backfilling in Large-Scale, [https\://arxiv.org/html/2301.03767v2](https://arxiv.org/html/2301.03767v2)  
> 12. Orthogonality Regularization for Compatible Representation Learning, [https\://openreview.net/forum?id=Due3iZPa6u](https://openreview.net/forum?id=Due3iZPa6u)  
> 13. SA.45s Chip Scale Atomic Clock CSAC \- GPS World from Chronos, [https\://gps-world.biz/sa-45s-chip-scale-atomic-clock-csac/](https://gps-world.biz/sa-45s-chip-scale-atomic-clock-csac/)  
> 14. Self-Driving Truck ROI: Costs and Benefits Explained, [https\://heavydutyjournal.com/autonomous-truck-costs-and-self-driving-truck-roi/](https://heavydutyjournal.com/autonomous-truck-costs-and-self-driving-truck-roi/)  
> 15. Highest Endurance M.2 SSD \- ATP Electronics, [https\://www\.atpinc.com/about/news/highest-endurance-industrial-ssd](https://www.atpinc.com/about/news/highest-endurance-industrial-ssd)  
> 16. Public Policy Archives – Southern California Law Review, [https\://southerncalifornialawreview.com/tag/public-policy/](https://southerncalifornialawreview.com/tag/public-policy/)  
> 17. Kodiak Targets Dallas–Houston for Driverless Trucks, [https\://www\.truckinginfo.com/news/kodiak-targets-dallashouston-for-driverless-trucks](https://www.truckinginfo.com/news/kodiak-targets-dallashouston-for-driverless-trucks)  
> 18. Untitled \- Emerald Publishing, [https\://www\.emerald.com/books/book-pdf/10743035/979-8-88730-285-0en.pdf](https://www.emerald.com/books/book-pdf/10743035/979-8-88730-285-0en.pdf)  
> 19. Zenoh vs MQTT vs DDS for Robotics Middleware (2026), [https\://iotdigitaltwinplm.com/zenoh-vs-mqtt-vs-dds-robotics-middleware-2026/](https://iotdigitaltwinplm.com/zenoh-vs-mqtt-vs-dds-robotics-middleware-2026/)  
> 20. Kodiak AI bringing autonomous trucks to Canada's forestry sector, [https\://www\.trucknews.com/technology/kodiak-ai-bringing-autonomous-trucks-to-canadas-forestry-sector/1003214689/](https://www.trucknews.com/technology/kodiak-ai-bringing-autonomous-trucks-to-canadas-forestry-sector/1003214689/)  
> 21. O\&m Payload Meter Ii PDF | PDF | Truck | Calibration \- Scribd, [https\://www\.scribd.com/document/460465310/O-M-PAYLOAD-METER-II-PDF](https://www.scribd.com/document/460465310/O-M-PAYLOAD-METER-II-PDF)  
> 22. News Reports | M21 \- Mobility21 \- Carnegie Mellon University, [https\://mobility21.cmu.edu/news-reports/](https://mobility21.cmu.edu/news-reports/)  
> 23. Senior Software Quality Simulation Specialist @ Kodiak Robotics, [https\://jobs.tusk.vc/companies/kodiak-robotics/jobs/83360814-senior-software-quality-simulation-specialist](https://jobs.tusk.vc/companies/kodiak-robotics/jobs/83360814-senior-software-quality-simulation-specialist)  
> 24. Autonomous Cars Could Drive a Deluge of Data Center Demand, [https\://www\.datacenterfrontier.com/connected-cars/article/11430754/autonomous-cars-could-drive-a-deluge-of-data-center-demand](https://www.datacenterfrontier.com/connected-cars/article/11430754/autonomous-cars-could-drive-a-deluge-of-data-center-demand)  
> 25. Jobs at Kodiak Robotics: Explore current Opportunities \- Wellfound, [https\://wellfound.com/company/kodiak-robotics/jobs](https://wellfound.com/company/kodiak-robotics/jobs)  
> 26. Daily Papers \- Hugging Face, [https\://huggingface.co/papers?q=Unity+Engine](https://huggingface.co/papers?q=Unity+Engine)  
> 27. (PDF) Downtime priorities, Jack-knife diagrams and the business cycle, [https\://www\.researchgate.net/publication/43518210\_Downtime\_priorities\_Jack-knife\_diagrams\_and\_the\_business\_cycle](https://www.researchgate.net/publication/43518210_Downtime_priorities_Jack-knife_diagrams_and_the_business_cycle)  
> 28. THE 2025 EDGE AI TECHNOLOGY REPORT, [https\://www\.ceva-ip.com/wp-content/uploads/2025-Edge-AI-Technology-Report.pdf](https://www.ceva-ip.com/wp-content/uploads/2025-Edge-AI-Technology-Report.pdf)  
> 29. A New Approach to AD/ADAS Test Sce- nario Generation ... \- Gupea, [https\://gupea.ub.gu.se/bitstreams/c85f7f2a-7cac-4069-adf8-2ade93637fb8/download](https://gupea.ub.gu.se/bitstreams/c85f7f2a-7cac-4069-adf8-2ade93637fb8/download)  
> 30. Earnings call transcript: Kodiak Robotics Q2 2026 revenue jumps 91, [https\://www\.investing.com/news/transcripts/earnings-call-transcript-kodiak-robotics-q2-2026-revenue-jumps-91-as-loss-narrows-focus-93CH-4844665](https://www.investing.com/news/transcripts/earnings-call-transcript-kodiak-robotics-q2-2026-revenue-jumps-91-as-loss-narrows-focus-93CH-4844665)  
> 31. Clear lanes. Full tanks. Can't wait\! | Kodiak Robotics | \- Medium, [https\://medium.com/kodiak-robotics/kodiak-is-coming-to-texas-101599ca79d3](https://medium.com/kodiak-robotics/kodiak-is-coming-to-texas-101599ca79d3)  
> 32. Hot-Refresh Model Upgrades with Regression-Free Compatible, [https\://openreview.net/forum?id=HTp-6yLGGX](https://openreview.net/forum?id=HTp-6yLGGX)  
> 33. Track: San Diego Poster Session 5 \- NeurIPS 2026, [https\://neurips.cc/virtual/2025/loc/san-diego/session/128335](https://neurips.cc/virtual/2025/loc/san-diego/session/128335)  
> 34. Privacy-Preserving Model Upgrades with Bidirectional Compatible, [https\://arxiv.org/pdf/2204.13919](https://arxiv.org/pdf/2204.13919)  
> 35. The data problem no one solved \- Sift Stack, [https\://www\.siftstack.com/mission-critical/the-data-problem-no-one-solved](https://www.siftstack.com/mission-critical/the-data-problem-no-one-solved)  
> 36. emernerf: emergent spatial-temporal scene \- ICLR Proceedings, [https\://proceedings.iclr.cc/paper\_files/paper/2024/file/47fc64d05a394955b1ae2487bfef1ab0-Paper-Conference.pdf](https://proceedings.iclr.cc/paper_files/paper/2024/file/47fc64d05a394955b1ae2487bfef1ab0-Paper-Conference.pdf)  
> 37. A Review of Contemporary Atomic Frequency Standards \- arXiv, [https\://arxiv.org/pdf/2004.09987](https://arxiv.org/pdf/2004.09987)  
> 38. Precision Timing in Defense Open Systems Architecture | SiTime, [https\://www\.sitime.com/company/newsroom/blog/precision-timing-heart-defense-open-architecture-systems](https://www.sitime.com/company/newsroom/blog/precision-timing-heart-defense-open-architecture-systems)  
> 39. Synchronizing 5G Mobile Networks (Converted) 9780136836193, [https\://ebin.pub/synchronizing-5g-mobile-networks-converted-9780136836193-9780136836254-0136836259-e-2042142.html](https://ebin.pub/synchronizing-5g-mobile-networks-converted-9780136836193-9780136836254-0136836259-e-2042142.html)  
> 40. NPL Report TQE 32 Holdover Atomic Clock Landscape Review, [https\://eprintspublications.npl.co.uk/9987/1/TQE32.pdf](https://eprintspublications.npl.co.uk/9987/1/TQE32.pdf)  
> 41. Fast Synchronization Algorithm of High-Stability Oscillators to GNSS, [https\://multimedia.edu.pl/publications/Fast-Synchronization-Algorithm-of-High-Stability-Oscillators-to-GNSS-Signals.pdf](https://multimedia.edu.pl/publications/Fast-Synchronization-Algorithm-of-High-Stability-Oscillators-to-GNSS-Signals.pdf)  
> 42. Mining & Tunnelling \- Cavotec, [https\://www\.cavotec.com/industry/mining-tunnelling](https://www.cavotec.com/industry/mining-tunnelling)  
> 43. Stäubli charging solutions for the mining industry, [https\://www\.staubli.com/us/en/electrical-connectors/industries/electric-and-hybrid-vehicles/charging-solutions/mining-charging.html](https://www.staubli.com/us/en/electrical-connectors/industries/electric-and-hybrid-vehicles/charging-solutions/mining-charging.html)  
> 44. Micron 7450 MAX \- SSD \- Enterprise, Mixed Use \- 800 GB \- CDW, [https\://www\.cdw.com/product/micron-7450-max-ssd-enterprise-mixed-use-800-gb-pcie-4.0-x4-nvme/7585311](https://www.cdw.com/product/micron-7450-max-ssd-enterprise-mixed-use-800-gb-pcie-4.0-x4-nvme/7585311)  
> 45. Corsair Force MP510 SSD Review: A Force to Be Reckoned With, [https\://www\.tomshardware.com/reviews/corsair-force-mp510-ssd,5848.html](https://www.tomshardware.com/reviews/corsair-force-mp510-ssd,5848.html)  
> 46. Industrial PCIe® Gen 4 x4 | M.2 NVMe 1.4 SSD | 4TB \- ATP Electronics, [https\://www\.atpinc.com/products/industrial-gen4-nvme-M.2-ssd](https://www.atpinc.com/products/industrial-gen4-nvme-M.2-ssd)  
> 47. Z-Drive 6000 Series \- Enterprise PCIe NVMe SFF SSD, [https\://tiscom.ru/sites/default/files/additional/zdrive\_6000\_series\_datasheet.pdf](https://tiscom.ru/sites/default/files/additional/zdrive_6000_series_datasheet.pdf)  
> 48. ROS 2 DDS vs Zenoh: Robotics Middleware Compared (2026), [https\://iotdigitaltwinplm.com/ros2-dds-vs-zenoh-robotics-middleware-comparison-2026/](https://iotdigitaltwinplm.com/ros2-dds-vs-zenoh-robotics-middleware-comparison-2026/)  
> 49. Comparison of Middlewares in Edge-to-Edge and Edge-to-Cloud, [https\://arxiv.org/html/2309.07496v4](https://arxiv.org/html/2309.07496v4)  
> 50. The Evolution of the Robot Operating System Communication, [https\://www\.mdpi.com/2079-9292/15/12/2632](https://www.mdpi.com/2079-9292/15/12/2632)  
> 51. Projects in Awesome Lists tagged with vector-search | Ecosyste.ms, [https\://awesome.ecosyste.ms/projects?keyword=vector-search](https://awesome.ecosyste.ms/projects?keyword=vector-search)  
> 52. SeekStorm — Rust database // Lib.rs, [https\://lib.rs/crates/seekstorm](https://lib.rs/crates/seekstorm)  
> 53. Voxel51 and ORI Partner to Accelerate Visual AI Innovation in U.S., [https\://voxel51.com/blog/voxel51-and-ori-partner-to-accelerate-visual-ai-innovation-in-u-s-government](https://voxel51.com/blog/voxel51-and-ori-partner-to-accelerate-visual-ai-innovation-in-u-s-government)  
> 54. NeurIPS 2021 \- Bird's-eye views of conference proceedings, [https\://www\.confviews.com/neurips2021/](https://www.confviews.com/neurips2021/)  
> 55. EmerNeRF: Emergent Spatial-Temporal Scene Decomposition via, [https\://openreview.net/forum?id=ycv2z8TYur](https://openreview.net/forum?id=ycv2z8TYur)  
> 56. Large 4D Gaussian Reconstruction Model For Autonomous Driving, [https\://openreview.net/forum?id=0PcJAHbSmc](https://openreview.net/forum?id=0PcJAHbSmc)  
> 57. Vector Informatik GmbH \- ASAM e.V., [https\://www\.asam.net/members/detail/vector-informatik/](https://www.asam.net/members/detail/vector-informatik/)  
> 58. Applied Intuition: Software Solutions for Autonomous Vehicles, [https\://startuptalky.com/applied-intuition-success-story/](https://startuptalky.com/applied-intuition-success-story/)  
> 59. Comparison of Middlewares in Edge-to-Edge and Edge-to-Cloud, [https\://www\.researchgate.net/publication/385738397\_Comparison\_of\_Middlewares\_in\_Edge-to-Edge\_and\_Edge-to-Cloud\_Communication\_for\_Distributed\_ROS\_2\_Systems](https://www.researchgate.net/publication/385738397_Comparison_of_Middlewares_in_Edge-to-Edge_and_Edge-to-Cloud_Communication_for_Distributed_ROS_2_Systems)  
> 60. Indy Autonomous Challenge (IAC): Experiences from the Trenches, [https\://zenoh.io/blog/2021-09-28-iac-experiences-from-the-trenches/](https://zenoh.io/blog/2021-09-28-iac-experiences-from-the-trenches/)  
> 61. Minimizing Discovery Overhead in ROS2 \- Zenoh, [https\://zenoh.io/blog/2021-03-23-discovery/](https://zenoh.io/blog/2021-03-23-discovery/)  
> 62. CANape for ECU Measurement, Calibration and Logging \- Vector, [https\://www\.vector.com/en/product/canape/](https://www.vector.com/en/product/canape/)  
> 63. Staff Software Engineer, Data in San Francisco at Sift \- Talents by Vaia, [https\://talents.vaia.com/companies/sift/san-francisco/staff-software-engineer-data-113314383/](https://talents.vaia.com/companies/sift/san-francisco/staff-software-engineer-data-113314383/)  
> 64. The Case for Unified Observability in Complex Machine Development, [https\://www\.siftstack.com/mission-critical/observability-white-paper](https://www.siftstack.com/mission-critical/observability-white-paper)  
> 65. Staff Software Engineer, Data \- Sift Stack | Built In San Francisco, [https\://www\.builtinsf.com/job/staff-software-engineer-data/7080551](https://www.builtinsf.com/job/staff-software-engineer-data/7080551)  
> 66. Software Engineer, Full Stack \- Sift Stack | Built In, [https\://builtin.com/job/software-engineer-full-stack/7080554](https://builtin.com/job/software-engineer-full-stack/7080554)

[image1]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAF0AAAAWCAYAAACi7pBsAAADWElEQVR4Xu2YaaiMURjH/2QXkiX7RVJEJEWRe1NCEWXNkg/WfLBliZSLL8QnSpYiJFtCyVpC2SKR4gNJylaSJYTE8/ect/fMc++8c995Z8bczK/+3Tn/58zMe557znPOGaBEiRKZGSCqZ80iopc1ajvLRAdR3Ek/K5ptzWJmseiS6IrodWroLw9ETayZQ/jd1Wml30mY68UCLXexVqLnotGuXfT0Fy0R/RZ9M7GBosHGyzVM3h3o91MvnJcu6U9Et9zrIOlkquidqKXnFTULoQOu9LwhzisUmxAmfoqJBZQj+plmin5YMw39RL2tWUhYszmY4cZ75bXzTUfRd+hzcOZXxwnRV2t61Bf9tGYauMJviI7aQD7hxshTSV3RW2hpaeRi9D6Jjrm2T4VRsME2N342+8ABhLN9qIl1E/0S7TC+5aY1IqgDXVXnReNcOy9cF90Vlbl2MMjKoIMw3nkTPS+ADxe8h/KTvki0HtknnQSfywQz0aSZ6KPoZNApgqXQ0pgNzAnL3GZRJxNLhD8YEmxifmmZ47wRnudzHGFyfPaKmhovLv4/dJvzmEi2K1w7Ch4dx1gzJhtE70X7RT1MLDYTULVkfIBuPkFpIauhgxzkeT59ECamsfPaQ2tyUh4i/GyWOB4Hn4pu+50imATdUJPSQrQC+t1dTCwWF6BHKx8OjscvH5YI+qz56TgN7bPAtbkkOTuSMh+ps32N+zvD7xQBZzlXai5oCB1fpfFrTF/ow1uCZctNZJbzOED6XBnpYP/H0H73ULVsJWEjUhO/KjUcCS97I60ZgzbQkst7AU9DiWiHqklvK/oCLS3DEJaeUdC+ma7W8xAm5pCJBUyDnkq6Gj8KPitLXvDZcS4860TdrVkDuKr3QMtb4mT7XEP4gZ2hM/S+a+8UTXavW0MHu8W109EAYWJY56sjiJ+ygQzsRvjeOBy2Rga4Yq+KHkFXes5/Y+Ix6IhoF/QqXS56KdouOoPUcyovDjXZvKJmOeHseQa9vsehp+gzdKOPwxtrRDAW+tsSj8Z1Teyf0AFaenIBy1XcGZgNW0UXrVnbWAstIUngcr0smm4DOYYlkUdMzt5aDes/b2hJ4PHzHPJ4xXbwN5RCrKaCUAbdZIui5qVhH/TEU+J/5w8CVcJ/HOSSHAAAAABJRU5ErkJggg==>

[image2]: <data:image/png;base64,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>

[image3]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAHsAAAAaCAYAAACXbyOAAAAEFUlEQVR4Xu2aV4gUQRCGy/Rgxow5Z4yIoCiYFRUxC4JyiuFBBUUxgIIZAyJifvDlRBQjGFDMWTChPhgwIAhmBAUF8UHrt7qlp7zb3dmb2ds9+oOf6amec3a7uquqeyXyeDw5QWXWHdYa3eEpmQxiVdfGdCjPaqSNnqxitTakyzLWDG3MYqqx8libWceCXX9ZQGKfrTsyTHPWddYj1lfWL9Zn1itjP07yWRvYP1CcYe1grWPdUn1pc4nVXhuzmOesp6y3rN+sDsFu+mTs75W9uJhsrp1JHFiP1YN1l2RCwvlLzDOWZqyJpt2X5PsUmYokg5ZLbGBVYvUiGQQdlTCAsO9V9uJimLn2J/nsllGseazarBOOHRx02vj7SJy9iTVLG3MIrI7tzv141h6SyRA181lttTEFhpsrnL3esZdlXXbuLV0o6NybrI0kaaFI3GaNZZXWHTkCVsQBVh1zjTNKzaH/w20quCvbdTZqj8OmjSLZUpP107S7k+T6MayW/54IQWuSlz5mvWFdJclzKAQyyWDWFyraRMtnvWR9JFnhGMC4qMV6wiqnO5IwxFy1s0ewFpNMVB3GEUVQnKF4vkDyPUOzimSm7CYJSQh5oA1J4ZNJ8G6EqybKHoadJI7uqjtiYiZJSA0DJjWwzsYhyVzWB5IJigW31Tzj0spcsRjauR2p0Jt1SNnsPwgGUPIvgi3Ed200bGH90MYYQF7GasbWC2EVEybsagONWX3SEKpjrDYUiKmgV3YLknw9iWTlxgJyGnKABTPMZSolf/k0KtzZYK02RExDklBqt1sjSZwNe1iwus6lKbzzNKsqJWeoubph3OZ+hG+cjkUO9p0ICRYbXiwXWQOVTTOBEjsbOSgOSrGmk+T4Ko7dbr+6Oba46cTqp40JKKgav0GSRnGggvRZ39gjAyHYBfnbgpyAQUN4SQSqwkTOXqgNEbGN5PNhNbqg2IR9tLLHBSJK2NOsgqpxHGIhFWAS47MjWkQKZs8+kvBdgaQax0txgnPF9FvOshaZdh7rvGlrZ2OGu3vPMAcZqDbhqLq6Q3GK5LlvJPlSgz4I3y3OmgGnXke0MQXsSVhP1i7HjjoDW9+mpr3U6YsEnMfifHY/SVjHPi+PgisaBQUGD/s9gO0M7jFDtbP1jFyh7hOBwcOxZzIwCHj/SQqGcAsmLfoRuewEjQM4CqdeqYLUco1kz4xxwoLC57znPIMj1PumH30rnb5IwEw6SoUXY8tJXmwrXGz4cY9B185+57RBGGfnGh1JjpdzjgdU+PEbqnI41/5+ij047qewxlHQ2Q+dNijJzs5JarBea6MD8vkLkvAO8EPDM5Jcr6tx/ETnnkPnO21PFoCzcLsdSEYqWwLkdBzelyH/nyA8Ho/H4/F4PJ4gfwA9NNL1vPcNLQAAAABJRU5ErkJggg==>

[image4]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAIAAAAAaCAYAAAB/w1TuAAAERUlEQVR4Xu2YW6iUVRTHl5Z3w/CClCgHTbBeDAkUzDioYPriBUQr9eGooVAZaV4yDCwDA40ERfGGSKkg5SUvJT5o5SXDe5CXEEoMNcwQE/Uh14+1P2fPZo7OfM44fsf9gz/ub+1xzszstddNJBKJNDhWqg6FxsjjQzPVuNCYhuaqmtAYeeSpVXUJjWmY6pR12qgWqjar3g324G3VB6HxIdNE9bXqsOp31W3VVdWfql9Vu1TzVX2S/xCwSrVR7HuuDfZSs03q/4NZ4RnVKdV51f9O/bz9GtUFZ2/s2atFJ9VOt8YZXlK1Vi0Tc4AfxBzFB+dZ7tYtVZe9vdSQRy6pngw3MsZY1QJVT8k5QBjVRqu+C2zVgrT7o1vjAAlPqb4Vc9JZnh3eEjt4aKW66e2l5mPVjNCYcfaIOUASIl9VnVN9c/cV5WOCpIueLVT73Dqs5Leq2rv1EM/ORU34RHVUNcCzpQIvfEP1RLiRYTaIOcAO1WqxUFmX94ry8bpY5CkVIkB9DrBbcmnqOc/+s/sX56BeWKp6J7ddPN1Vn6pOqv4SKzz+Vi3yX1QliEYURh+GGyWwRMwBKKxwgI7522WFm0wxR/4uBfJ5IQd4WixNkZJnenZ4Raw+WCxWBHJ52+W9ogjmqm6pVojly/XO3k3MIRq552pBIcfhEbLTwo3kPf4NNyrECCm9IueAEwfgZuMQL4gd6na3RyQI6e2te3jronhZtSWwveiteXPajKwyXOz2vye5QrBU6KtrU4pIOliKgwPf69ZEAJ45fP4+3UFFivKvVH29Z/JQY+95pKTLZ9XmWdUmsegBAyW9A5BTOcg0IoL+pOos94fuy3cA6CUWgSerPne2skIf7B94rbcGogNOkCXqxOoXhiPkT+CHTOsAaaFYOxYa7wG1Q+gAwLAKKGBHefay8E/wPNtbdxX7wYgKWYLP/H5g6+TsD8sBqJ9+ESuui4XfOXGApLoHIkiNWFT7zbOXBd50ndjIlBxDyORDn1EdkPy5Mv3tDe/5omqoWAvC+jVnx6nIvdBXLPzCJLGpHMwRG8r40ac+josdXDFfnoh1TdU/3FC+F3sf0h7FIFVzJeDwmTuUCp0JtxxOSH7xTRomsgHfo62398AwDCFkfil2kDyPF8tJPoQf/wbhJBRXE519mFgK2S/57SMDCpin+s+tCc8UOcXAZ/lD9Wa4UQAiGC0TDh1Ch3NEdV31kVRuzkE7XcxnTeB35lA5A9pUagcclDXtHTDtS+oKOjaiS1O3VxZqxIYlyWEVglrAd4DTqmlik0PsgyRX/frtyFkxb14jdvCE4y+8/YbG85KrPTLFQbG+sz4KOcB0sdCEnZqhEOwxw+ZWjFFNkXSj0kgFIWQyAbwXYQrgZjOlIzxRO3zm7ORAHCOBsHVF7FYwHUsKncgjBMVcUrg9CBQnYW6i0OvgPWetq4hEIpFIJBKJRBoGdwAJyeKGsEvK0QAAAABJRU5ErkJggg==>

[image5]: <data:image/png;base64,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>

[image6]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAFQAAAAZCAYAAACvrQlzAAADNUlEQVR4Xu2YWchNURTHly8ZMmUqczJEKSEPHqQvY3iQB08oLx4ICQ/GhJBCMitFiRdFeTB/T0KmJMr0LEPKFIXE/3/X2c46y7333PN9um7u+dW/u/de59y7zzprr732FcnJaSY/oGt+MAO3oJ/QNm+oVz5Ds/xgBsaLvpRu3lCvMLq6m3570yYdoUVuzLIWuucHi9FV9MfS1AQtgBoKd1WHNtBF6B10JdJb6LXE87oBrQ43GLpAR6FT0F7oQdIsB6EOps9re5o+GQGdgQ5Bd6B9SXNx+KY2QFclnuTHaCxou7HxoToX7qwefUz7sWg09YKOQFtE5zfaXENuQkujNp/xsLERRusxUSdyGXtnDoJeSfy9fPa5sTmdzRI77aWzETrSOjwrK6BzEkcatT5xRWlsJN01bXJBdNWchyaa8dOmPRXqbfoBOpGBxHl5+JzLTP+RaVdEmkPvS2x/4WzlYDSfgPZAy6H50AyoERoSX1aWdqZ927TJWaiH6PynmPF1pk0bsQ5nhF4WnQPvt/mV8DknmP4BqC80zIyVhUsnOIyh7gk2aqGzlYKTfSbqyJbQ2rS9QxnptF8STQOBJdEnHfUQGivJiGNEDzf9/ZLcwb9CI6M2l/080VU26vcVKViH+gidHI1/EU3mrZLmonAZcsOY6Q3NoJRDufEwypgjGUEW/vYOUUftFs2hNgr96mBeti9+pWgq4EbE1HRS9Hsqxi557qSNTmGcO2Y/See56C75N7AO5RxYZHOzvC5aaA819pohLYfulNjul10x3sifL8VrsFSGj1D2p0H9RTcla68Z0hw6XZJ5NI1Pkiy9iqnSMoT1aCC8zKeiS535PNNSrBblcigZKNkcyge2m0RLKLbLbxKtPwmL/5ojLULnSDaHboXW+MFmYuvQ4FBGLWtS7ros/GvmjB1OSk0SO8uflDYa23doUuHOdFhQc3Ma5w0ZsScllkANpr8LWgytEs2nPEr/U1hK2MgrJR7lWErYh6sE/kvzBJoNjYEGQG0TV5SGL5tlEXf2cLr6IMmDRSfRudH2TfQPDJtz/0tYL/K0xDKHufW96Es6bq7JycnJycnJycmpH34BL2bYnbj02xQAAAAASUVORK5CYII=>

[image7]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAFEAAAAZCAYAAABJhMI3AAACNklEQVR4Xu2XT0hVQRTGDxZiGIKIEIELDcLEjdDGjVTLIAjFnRq1EDeZK3eCGyEXitQiqE1RCLlxJSiKCw2EIPdSuFGM2iQtlALR892ZYeadN+/dq/cxL2J+8MG955tz577v3X9DFPknuMdaLaMhOzTio4H10dn/wPrOqtH746xua0d89LMe6m0E95P1ztr0glTQ/z2NrNMMWmMNkr3KJF2kxj2RhgZhy2NKnbC+shZ0TzUYpuLzMsKd5uUKa4K1Tnbwoa4ZPXe8JVZ90lnIU1L+TWlobpE93i6psdtODXrF+qO9yaQrPLfJno/5zX/1fp8zzssU2aY94YFNsv6B8MAP1ntZLMEGqeP4xuNPNfPMCy805jyOpFGKtBB3yPrYlqD+SBZLUC7EFrLzvBFeaHKFuC88YDxoQHgA9RuyWAITou8ZY55Jx6w24YUmV4jySnyg679Zs069jrVM6nsQPm55bLc6Y3z4rsTLrGesX9p77HjVIleIeL7dcXTXqc+wrqEhBybEFSqc5z7rs/ZGWbXJ6PJ0UuEx0pT1bgG5QpRXInhJ1kcIeTAh+p6Jl1hfSPnTwgtNxUPE6934UB7KhQjmyM7TLryQVDzEDgoX4gjZebBdLSoeIlYroUJ8TXaetA/cLSo8rzS9TbqyYXpSQ8yyYpl0PKwoetB4TrKsWPDmx6cNvG+s5qQzLBdasTRR8b/l0yfWGOu6ajs3vVR8TJ8Q4iLrqmoLzoXWzpFIJBKJRCKRiOQMrH4RgIFGyB4AAAAASUVORK5CYII=>

[image8]: <data:image/png;base64,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>

[image9]: <data:image/png;base64,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>

[image10]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAEMAAAAWCAYAAACbiSE3AAAA0klEQVR4Xu2WIQpCQRBANxg0CGIwmESwiMnqAcQmFkEMXsEkGD2NF1BMNg+gglnwGAZ9y+fLMgjCbhr/PHhhZtpjwzpnGEYkI7koIl3c4kseikQNn3hyWYhCx8gpOYvxISbGEA9YkQco4w6X8qCBmBieKR7lEva4kUstxMbwTLARzP5VrIJZHSkxPDdsYdV9fymqSI1RxyveXRZFNakxfIgZ9vEsbupIidHBRTAPsBnM6oiN0cOHXMIF23KpgTyC9BdzHMtlgP+HrOXSMAzDMP6TN8TTLX9u3efGAAAAAElFTkSuQmCC>

[image11]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAFEAAAAWCAYAAAC40nDiAAABPElEQVR4Xu2Wr0sEURSFr24RNa5GtRkEwaLBYhEM/ogGwXX/gc0Wm01BMCmoiCD+A6JBrBYRLBaNRrtVz/VOmD37mB1ekHnM/eBjh3P2lbM7zIg4jlMDmnCewz7MwCkO68wKPOGwgH34Dbe4qDOr8JTDAE/wB35mnz5ijnV4xmEB9+Ij9rAGLzgsIGbEO7EfK8QifIeTXKTEf4w4Ch/hJhdiA85yWGUm4BK5C28DuTonvcSMqAyLnc2zAKcpqzwd+EC+iD0sOFev7VgXsSMqQ/AIDsBl+NFdp0vs7bzNRUla8AteUp40sSPqGDG8wnGx16pj6pIldsQdysuwB8eya72lz3Nd0sSO2OaiD4fwmbJBsX+jDpoMB2IDlPXNjv1xE+jVjdx3QuhAV3CEi4yG2MMmqdccx3Ecx3GqwC954VBc3D3YfgAAAABJRU5ErkJggg==>

[image12]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAFUAAAAWCAYAAACxOdCYAAAAl0lEQVR4Xu3SIQoCQRxG8QExCCaDyS54AsETiBewbzEIHsADmDyEgqfQqmizmwWP4YPd4j/pjknfDx7MzFcnJUmS9L+a8UH5GjSjBx2qu76kQ0u60YJar7NyTOlCd5qHTZnGdErlr22HTZkGtKdrdVamIe1oFAd9bpLK37mJg+o50pb6cdD7CjrTmnphU00r6sZHSZL0Y54Z7hCR8GLoaQAAAABJRU5ErkJggg==>

[image13]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAEkAAAAWCAYAAACMq7H+AAABPUlEQVR4Xu2WvytGURjHjyiF/MjCZpPBInZlsShSvINSTMJqY/E/2PwoyqxMREnEZDdalIFMRj5P59K939739W461/Opz/B8n3PP8HTvOTcEx3H+gE6pu3BUsn/PB17ieeY7ThdWOOFT9LeoCju4iYs4Ij0nY0KDBunHOw1zrOOVhqkyiSt4hLvS+41BHNYQlvEWu7WRKq94hku4hnvYWlhRnwccz9U2cNuvI5clz5bUdngfSlaPAXzEmay+wLafbkl5C3FQdqY0ShPu44s2ysA8ViR7CnFIduM1QkuIb94B9uBUoVsCrvFGMvu5tCHNSl6L0xCH1JzVdmCXalD2iYxJZgOyz6ZX8mq0h7jH94AMe+4e53JZ8thATkL8qXzG1WK7JkO4rWGOPjzWMFXsHLGbaQMXpOc4juM46fAF0h4zlBm6wEwAAAAASUVORK5CYII=>

[image14]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAFcAAAAWCAYAAAC1zAClAAABPUlEQVR4Xu2XvUoDQRSFx4A2gTQqBCxSxDQqiLVNyBOIwehjhIC1voA/IIiNjZUkbYiCRdIFk0LbkMLeF7DUc7MJbM4O2d0phAz3g49lzt1pDssMa4yiKEpi8vCAwxj24RaHSpQqvOJwARvwBx7xQIlyCq85tNCHv3A0fWq5CZBybzmMQco95lCJIuXecRhD2nIHsMhhiA4HvvAf5e7CD7jDA9CAWQ6XkQIskxewZcnFPWPH5cwtmaDgw1B2Dtuh9VJTh2/kJ/yy5OJ9sC1C2i93xjYcwxV4A1/h2twbnuF6LJxwmBAp9hvWeOAjruW6lLMKn+E6HMLK/Ng/XMuVfWmQS+sFPk7Xm/DdeF6wa7lnHC4gB7vwAWZCufx6yyXnBfInJsUktTfZFdC0zGfGcckB8cSBoiiKoiiKP/wB4ChKuP9udyMAAAAASUVORK5CYII=>

[image15]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAACcAAAAWCAYAAABDhYU9AAACDklEQVR4Xu2Wz0tVQRTHT1ZaqYvEXxC1CX8R4h+QgrhRBBWKiPZBCzfSrqCFrgI3QW1STDeiC0ERxIUuBI02KeqicGPRJkRBXVRURH6/zsz13OPtPgNfCPmFD2/me85978zcM8MTOdV/pFZwxppQGzhrvBpQZrysqBaMgd/gnIlR9DfAjGcZLEmWi7sMfoLX4gpIK07DheTHMrKoQkkv7ht45Gk3sawrU3FfrXFE8buuW/MPugqq5HBvZyzuCygB3WDCj4+iYXFtc1551WAdNPt5MZgG78Ek+OD9SAWSXtwvsAlegltgB9yLZRzWJXGFrRm/V9zvNPn5OJiLoiL1aryvTDvHk9qo5iPicsPqk9QiLqfP+Ivgh7jiqS0wJfHdjUkXl2diSeJ9GPK560laEBcvV94d7/Uo7wb46H2yq2L70sVdMDGK9xp7JahRDvKvKV+LrbBqvBeSvOPs4cfinmE8Jl3cRRML/fhEeR3e21aeFeOvjMdi+Ur5nUXeY8/l+jFb6qEfR9LFhV7QYo/xVAWxUOYOKM+K8WdqftN7837e6T9ZLBcblKPGUVEaHgCtUfAZ9Itb6TtQF8uIi6+Ju/odzIp7jvkPwCcwBJ76XOYMghXwRtyt8NeqAPdBl7idTtNt8BxcEdeful/5ShvUnJcvxT8SlZJwCR+3+DrvWvOk6C0oteZJUDhcp/rn2gNk5n65DvOFegAAAABJRU5ErkJggg==>

[image16]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAACcAAAAWCAYAAABDhYU9AAACdElEQVR4Xu2WS4iOURjH/67llmLIJCaU22Tkkg0iKSxQLs3GaixM2c1sUFOyIhaKyGjGbIgslJIFRVFSlGuSMrLRRImNkPj/v+ecd5734ZOFD2l+9W/e5/LOOe85z3nOBwzwnzOJaqF2UeuoieVwwXBqBdVOjQuxmvGMukIdoK5SX6mhpQxgGizvEXWIekktLWXUgDGwFcsMpm5SHc4nnlPnqGHJPkG9oRqKjBqwGbZSC53vIPXa2UI5S5w9Nfm6nK8mzAv2beqIs6dTn52d0WrGSUdUHjOiswpTqFnUkBjIrIUNONb5VuH7lRQPYbnbYsBxGvZhuRzEbNiHrUl2HXWZekJdpHqTv4Imoho7Rn2izvsg2UD1BZ/Ik9seA4mRsIk9DX6Vjd7TR4sL1PUiCixzzxgBayWa4FnYVw1y8U3UK2dn7sEGaY2BRN6FzuC/C1sETV7oYF1CeXWrosnony5OdhN+vHKPYXmrYyChU6+4+mhma/Ltc75G6kXyS+9yYALK9SXmwpL2Jnsy9bGI9pMPxIIYSHyhHgTfUdg7ud4ymsce2DuKV1BjvZaNhE6vElQbQlsse1SRYXyg3qL6duid7uDTZLWlo9F/y6jmdPsIne42PWjQ97DW4cm1ssX5ZC9ydkPyHXe+iOKHna0bRb4byd6Z/mqyG9Oz0EVQYTysTZyh9sNOjZZWTdajurlF9cBOrw7Iep8Q0DZpVVUOuhJPUvOpHbCrrwc2nlDOKeo+bIxS29L+66Tuppqpeh8MqEn+ysWvm0eNXPW6EtbbMtrS5c5W8xVzqJn4SRP+XWg79aH/JHdQ/afXX0W/dIp2MMCf5BsCkoFxRfvragAAAABJRU5ErkJggg==>

[image17]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAFcAAAAWCAYAAAC1zAClAAABoklEQVR4Xu2XuyuFYRzHf+RSlEVKUQYsKFmUUGKxGYSs/gIpg+SymdxLFotJjK5lQEm5lEs2AzMGk5Xv7/zOcZ7313Oc54xev099hvf7PO/y7bm8L5FhGEYwlbBFhx46YLXKimCnygyHfjivQw8L8AtewOOkH3DSnWREGSIpLhsrJOWm/CR51/gFLmhJhx6W4S6cgm2wNDps+OByV3XogVf3tA4DuYK1OnQ40EFcyKVcXrV9cAsOw7zIjMw0wlvYoAfAGMVkF9TALuUM3PHkbBOl4UvvHd7DAXgDz0m+NkKoJym43cnG4Z7z/KcZpfRNn/IOPntydk1eSzBBcuaWJJ+rSC62x58Z2amDTyQrfhEekXzOxZbQY8HHPknBucDFvsJBPRBHQspthg9wTuXblFu5hSTndTm8ht3R4fgRUi6Xmvq+LXByPjpCy+VL6xBuJJ8r4CXFvOCQckfgG0W3MpfM2zuk3DJ4AtdhvpPzZciXXCxI/cKGepp4S+iBL/CM5BLjcf6xKHbmZGJWB4pNHfxH+MzsJVnJrWrMMAzDMIy/zDc8LlwHYcgv3wAAAABJRU5ErkJggg==>

[image18]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAADoAAAAWCAYAAACR1Y9lAAACWUlEQVR4Xu2X26uMURjGXzmmCLkg50OuRCSFZLhDJHK4EH+AG6JwIaUockzJqZSkcCFxIYfs3ChSbhRSbhR3Dru2UuJ5vN/a+51nvplvZmo2TfOrX7PXs75v9a1Za971bbMOHdqOcXCehgXMhRM0LGAEXAl3w6HS1y9sgCc0rMFY+AOu044arIDd8Ak8Dl/AGWVX9AOb4UkNc3gGf8O32WcjE+2B+0L7AXwNh4es5XCipzUsgBNdr2ENuJpDQnuV+Rh7QtZyONGzGhbQyES3wceSjTYf4xccJX2RgVb/Fl8NF2oYafVED8C7kg0zH4MukL7IZfNrRoaMRfBNaA+AR+EVeDWFU2BJPAhv5eR0tuXTyG/0GLwjWZzoUulLDIbf4CfJud15X2In/B7aveFD8RX8kJPTc35bBY2sKAvdbckGWd9EWZHzKJn3X5P8fpYnbsLPoV2VZrfuRg2rsMMqV5TVNk10kvQlHpn3zwzZ8iy7GDKez1yUNF5Vmp3oJg2rsMX8QSJjrO/BuI3z+Ak/SnbI/J7tkrNoXYdfJC+j2YnyvnqYCF9KNst8jOeSR9jPh490ZflUuDXLDltBtU00O1GuVB574TTJeI6yuCTWmI+xK2QK+1l1E3PMV/l91k714x48k/3dCwtD2jL12PX3Loc/eu1PRi5Y5ZGxBL6DR+Ba87ei+WVXlMOt/dX8jeopPA8XmS8KtzPbCR5dN8y/FC1c/wSed4vhfit+qefRdQmON6++XM0E710W2pOzz5LV/vL+S05ZZcFpS/jfzXQN2w2ei3wH7tAB/AGsyJR0vtYXLAAAAABJRU5ErkJggg==>

[image19]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAEkAAAAWCAYAAACMq7H+AAAA50lEQVR4Xu2WMQrCQBBFR7RSEcVGOzux8A5WdhY2XsDKwlN4EAULL2AVsBBEtLL3CB5BEf3DrroOgZBtQpZ58AjzJ9Vns4RIUZSMGcpA+dGFa/iSC4WoCp/wYJ9aUgIP0pISSVtSG55k6DCHexnmnbQlMXyX9WUIpvAI63KRd+6UviTmAgfOPIMRmfsuOHxOEtOBVzi28w6Wv9vA8C2JKcAlvMlFaPiWVCLzj7WCDTj62waGb0lbMiUV7cwXdrBF+ZRUIfOZfQpimvAMJ06We7iYOGvuSzH04EKGDi24kaGiKIqiKFnyBqIXLnzUKAowAAAAAElFTkSuQmCC>

[image20]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAFwAAAAWCAYAAABNLPtSAAAByElEQVR4Xu2YzStEYRSHj69YEMIKSyWSbHyFREmyIgtfyYoFsWGDlCxEkWIhdlKyoiwl5WNBslAUG6V8LfAPiN/pvcY7pztz74yxmOt96ql5f+c2izN3zj0zRAaDwRA11MAROACTRM0QYabgHVyH8/AVNukXGCLLI8zWzp/wAxZomcEF1TBXhjZwg/e085uVLWmZwYZMOAvnYI6oBaMWpmtnbjbLc92JMRloZMEzGXqBIrgKr+CQqIVKDKlmT8tCENZgrMhS4SnsFXnU0whvYR9MELVQaIAT8AgOipoTk3ALJlrnDHgC231XRDlxsBtekGp2vH85LArhKKmm8zzn+R8K4/CA1J19CVv9qlEMf+V5q2izXv8FO6TGyjWpD9ct+fCeVNM9RQncJTWz+0UtHOrEeYZ+HpzFohaIUngDy+AxTPYve4NKuElqhvLcDIdOUo1t0TLedL4bXq7lgaiHD7DKOnfAfZjiu8JjLMAnuALzRM2JYVKN7dKyDSvjfdxN055hhcj4/fhOTxO55+D17Bwekvs5/05qhVuGi/CF1MNTrnp2OK2PPTLwKrzmbcNmWbCBf6Dwn1bcZN7jf7NeGgwGg8Fg+G98AV3GSvwLVTEvAAAAAElFTkSuQmCC>

[image21]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAD8AAAAWCAYAAAB3/EQhAAAAn0lEQVR4Xu3UsQkCQRRF0S8qBoKYa2oHBsZagLIYCoL2YBtGBubmYgEbbAeCViAIluEdNpD9Fcj8d+FELxp2Zs2UUkopXwsr9P2QayOc8MbQbdk2wwV37NBrznmWrvYST2zQbs551sHe6kM/LMihU128UFj95cM1RWm/Nx6yOa44YOC2MJ3xwRFjt4Uq/RO2uGHhtjCtUWHiB6WUUn/cF/ueETsUeRESAAAAAElFTkSuQmCC>

[image22]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAACAAAAAZCAYAAABQDyyRAAABUElEQVR4Xu2VQShEURSGf5JkiGRhsp6iSbGxsbOzsGKlJiWhKEV2SonCTspaUbJgynaWxsZmNrOwV0qJbMZK/LfzGvcdZtz7Xiz0vvoW9/zvdebde94bIOGfM0rX6BJtUVmIBshFrTqIwTm9pnN0lj7R8dAVimN6T1doh8qiUKa91vqdvtEBq1aTNH2hF3C84RtMwwNr/RrUNq1aXTrpOmRXTlXmQkatTXNjVtV/JEWXIUfUpzJXzIyZ5ls68GEGcq552q+yWozRM3pHp1XmTDtdhQxnm8p8eKAVyKvpRDfdpiU6r7IoXEKO4ZY2qewLXZDtXqDNKnNFP+kuPgdxSGVVeugOvYHDr6zDFKTRpFXbC2rGEate5Yhe0QnaGI68WYQ0ylm1k6D2DJmrX6cI2clDuk8f6QbiP5wXg5D/AfMdiTpLf0fBw+HgnoSEhNh8AIGMQMwHOk+hAAAAAElFTkSuQmCC>

[image23]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAFwAAAAWCAYAAABNLPtSAAABUUlEQVR4Xu2WvytGURjHH7+y+FXYGJXFYCFiUjLY3gxEMojNxkBZTAzKJv4AmQxmKTGQDMpAWZQf5X/gczq3t/c+ofeeew339nzqU/d8nzN9O51zRQzDMHJHiw6M/6EBF/FZD4zs+cJPvI++jUBGsVuHf7AmVngiOnAbd7BLzaohpPB1HVTQiTc6LAJ9eIAPuKJmSQgp3HGItSprxWtcUHnumcAnXBL/8KVhVcIK38RjbIzW7XiF0+UdOacO5/BOfNn18XEwoSfcsYHn4k+2e3xLsWmOqcE3nIq+syRN4Y5efBFfeqHox1Pxd/aymqUhTeED+IiDeIlN8XExGMYj8XeouzfTElr4GL7iSLSewTNsLu8oGLv4jvvYo2ZJCC38A4dUNiv+pLepvHC437NbvJDq73lX8k/uVW76hS0dKOZ1UFTG8QQn9cAwDMMwDCNTvgE2/zs6I2RoswAAAABJRU5ErkJggg==>

[image24]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAFUAAAAWCAYAAACxOdCYAAAAoklEQVR4Xu3UsQ1BURhH8SssoJFoLaDR6agoJXoNjREsoNFIVBYwgGitQKJiAMZwXqi+Rp6rkZxfcor3/t1X3JQkSZI+6VMj/lQ5xQFXtKRm2FRSm7Z0oXnY9IUhXWlKtbCphOJ4EzrT7f2tDMUB7zSmStiUoUOH9HpDZ2FTpi7taEH1sCnTmh60oVbY9ANVOtGRRsl396cGtKdeHCRJ0p94As2NEXFt9QdWAAAAAElFTkSuQmCC>

[image25]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAACoAAAAWCAYAAAC2ew6NAAAAqUlEQVR4Xu3UMQ7BYBjG8Q+LBIMFCWHp5BIcwAEs4iQ2MbJjM7hBByaTGMQFbAaJU/g3uvSdunmavP/klzR98i39kobgecWogqF9qdoRMeaom02uCDu8MTCbbG2s8MEW/eysVxMLvNA1m2Q1PLFH1WxSNXDHMn2WKbnmDW6YopydNWrhgVn4/WPl6mGNaxD9gkkHXDCxg+eJdM7phE565i+NcxqhFLyC9wVbLBuRjCs9swAAAABJRU5ErkJggg==>