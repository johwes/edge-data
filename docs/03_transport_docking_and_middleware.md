# Specification 03: Edge Transport, Docking & Middleware Subsystem

**Document Version:** 2.1  
**Status:** Approved Architecture Specification  
**Parent Document:** [Master System Architecture & Site Infrastructure Overview](./golden_data_set_architecture.md)  
**Target Audience:** Network Architects, Depot Automation Engineers, Embedded Systems Leads

---

## 1. Operational Compartments & Natural Duty-Cycle Dwell Times

Rather than forcing haul trucks to interrupt active production for data transfers, the architecture leverages the natural operational rhythm of open-pit mining. The site is partitioned into **operational compartments** where haul trucks naturally dwell:

```mermaid
flowchart TD
    subgraph Circuit ["Active Pit Circuit & Operational Compartments"]
        Pit["Pit Face / Loading Bench<br>(Active Production)"]
        Crusher["Compartment 1: Primary Crusher / Hopper<br>• Dwell: 60–90s (Dump Cycle)<br>• Offload: Burst Telemetry & Critical Triggers"]
        FuelBay["Compartment 2: Fueling & Lube Island<br>• Dwell: 15–20 min (Mid-Shift)<br>• Offload: Batch Candidate Bags / Drive Swap"]
        Parkup["Compartment 3: Shift Change / Park-up<br>• Dwell: 30–60 min (2x Daily)<br>• Offload: Bulk Ingest & Diagnostics"]
        
        Pit -->|"Haul Loaded (15–25 min)"| Crusher
        Crusher -->|"Return Empty (12–20 min)"| Pit
        Pit -.->|"Scheduled Fuel Dispatch"| FuelBay
        FuelBay -.->|"Return to Production"| Pit
        Pit -.->|"Shift Handover"| Parkup
    end

    subgraph Pods ["Modular Edge Station Pod Ingestion"]
        Crusher -->|"High-Speed mmWave / Optical Burst"| Pod1["Crusher Edge Station Pod<br>(40 TB NVMe, 1x NVIDIA L4)"]
        FuelBay -->|"10G Robotic Optical Dock / Umbilical"| Pod2["Fuel Island Edge Station Pod<br>(80 TB NVMe, 1x NVIDIA L40S)"]
        Parkup -->|"Depot Fiber / Drive Sled Swaps"| Pod3["Depot Maintenance Pod<br>(80 TB NVMe, High-Capacity NAS)"]
    end
```

### 1.1 Sharded Ingestion Architecture
To prevent single-depot bottlenecks and eliminate multi-kilometer data runs, ingestion is sharded across distributed Edge Station Pods:
1. **Compartment Ingestion:** Trucks offload high-priority candidate snippets at the nearest station pod during scheduled stops.
2. **Inter-Pod Vector Sync:** Pods broadcast lightweight metadata packets over the local pit LAN (combining 128-D embeddings, GPS geohash tiles, and timestamp bounds; **<50 MB total per day** across the site).
3. **Global Coreset Resolution:** Using a distributed LanceDB or USearch index, each pod cross-checks its candidate snippets against the global site registry. If Pod B finds that Pod A already staged a near-identical event (`d(v_A, v_B) < 0.10` within the same lighting/weather window), Pod B suppresses its local snippet from WAN upload.
4. **Consolidated Uplink:** Only the globally deduplicated Golden Data Set (**<15–30 GB/day** for a 10-truck site) is transmitted over satellite/WAN to the central cloud.

---

## 2. Dual-Mode Depot Offload Interface & Throughput Sizing

In active mining environments, RF wireless offloads suffer from severe dust attenuation, multipath reflections off massive steel haul bodies, and concurrent channel contention, dropping real-world Wi-Fi 6 throughput to **150–300 Mbps**. At 200 Mbps, offloading a 50 GB candidate bag requires over 33 minutes—exceeding fueling dwell times and overflowing vehicle storage.

To eliminate this bottleneck, the offload topology uses a **hybrid dual-interface**:

```mermaid
flowchart LR
    Truck["Haul Truck Gateway"]
    
    subgraph Primary ["Primary High-Throughput Layer"]
        Truck -->|"Automated Mating (5–10 Gbps)<br>SAE J3105/3 Envelope + Air Purge"| OptDock["Robotic Optical Dock<br>(Stäubli QCC / Cavotec)"]
        Truck -.->|"Line-of-Sight Wireless (2.5–10 Gbps)<br>10–50m Beam Range"| VFO["Virtual Fiber Optics (VFO)<br>/ 60 GHz mmWave Bridge"]
    end

    subgraph Fallback ["Secondary Fallback Layer"]
        Truck -.->|"Constrained Wireless (<300 Mbps)<br>Dynamic Priority Queue Shedding"| WiFi["Industrial Wi-Fi 6<br>(Auxiliary Parking Bays)"]
    end

    OptDock --> EdgeNAS["Edge Station Pod Ingest NAS"]
    VFO --> EdgeNAS
    WiFi --> EdgeNAS
```

1. **Primary Physical Dock (5–10 Gbps Nominal):** Automated robotic coupling interface integrated into stationary fueling and maintenance islands:
   * **Mechanical Standard & Form-Factor Reuse:** Adapts the mechanical pin-and-socket envelope of **SAE J3105/3** (originally for EV conductive charging) to house ruggedized expanded-beam multi-mode optical ferrules alongside auxiliary power contacts. Representative industrial implementations include **Stäubli QCC series** and **Cavotec automated systems**.
   * **Second-Source Architecture:** To avoid single-vendor lock-in, the dock receiver bay can interchangeably mount modular industrial connectors (e.g., Harting Han-Modular with expanded-beam fiber inserts or Amphenol industrial optical assemblies) or automated push-pull pneumatic carriages.
   * **Dust Mitigation:** The mating arm incorporates an automated **high-pressure compressed air purge nozzle** that blasts the vehicle's protective optical shutter clean immediately before physical mating.
   * **Throughput:** An integrated 10GBASE-SR / 25GBASE-SR optical line transfers a standard 50 GB candidate payload in **45–80 seconds** under nominal conditions.
2. **Line-of-Sight Optical Wireless (Virtual Fiber Optics / VFO):** Where mechanical docking arms are unfeasible, directed Free-Space Optical transceivers (e.g., In A Blink VFO) provide 2.5 to 10 Gbps line-of-sight wireless optical transfer over 10 to 50 meters, immune to RF spectrum saturation and metal multipath interference. As a secondary wireless backup, 60 GHz V-band mmWave bridges (e.g., Peraso / Siklu) provide gigabit-rate wireless handoffs.
3. **Empirical Pilot Validation Requirement:** Nominal vendor specifications (5–10 Gbps transfer, 45–80s duration, VFO beam maintenance) are theoretical maximums. Heavy dust deposition, thermal shimmering in open pits, and haul truck engine vibration during idle require rigorous pilot verification before finalizing dock provisioning.
4. **Wireless Fallback (Industrial Wi-Fi 6 / mmWave):** Engaged at auxiliary parking bays or mobile service trucks.
5. **Dynamic Offload Prioritization Engine:** When operating over constrained wireless links (<300 Mbps), the vehicle's edge agent automatically sheds lower-priority queues:
   * **Priority 1 (Mandatory):** Filter 1 (Deterministic/E-Stops/Interventions) and Filter 2 (High Uncertainty).
   * **Priority 2 (Deferred):** Filter 4 (Targeted Campaigns).
   * **Priority 3 (Suppressed):** Filter 5 (Nominal Stratified Baselines) are dropped from queues to preserve buffer headroom.

---

## 3. Dock Capacity Planning Under Fleet-Scale Contention ($M/M/c$ Queuing Model)

A per-truck transfer time of 45–80 seconds represents raw optical pipe time. Real-world berth occupancy includes vehicle maneuvering, robotic alignment, compressed air purging, and mating disengagement:
* **Effective Berth Service Time (T_s):** ~240s (4.0 minutes) per truck (60s positioning + 30s air purge/latch + 60s data transfer + 30s verify/unmate + 60s clearance). This yields an individual dock service rate μ = 15 trucks/hour/berth.
* **Shift-Change Arrival Burst (λ):** During a 90-minute shift change in a 25-truck compartment, peak arrival rates reach λ = 15 to 20 trucks/hour.
* **$M/M/c$ Queuing Analysis:**
  * **Single Bay (c=1):** Offered load ρ = λ / μ = 18 / 15 = 1.20. System is unstable (ρ > 1.0), generating severe truck queues that stall mine production.
  * **Dual Bay (c=2):** System capacity μ_total = 30 trucks/hour; utilization ρ = 18 / 30 = 0.60. Average wait time in queue W_q ≈ 2.5–3.8 minutes.
  * **Triple Bay (c=3):** System capacity μ_total = 45 trucks/hour; utilization ρ = 18 / 45 = 0.40. Average wait time W_q < 0.5 minutes, absorbing unexpected re-mate retries without queue buildup.
* **Sizing Rule:** Sites provision a minimum of **c=2 parallel docking berths** per 10–20 truck operational cell, and **c=3 to 4 berths** for complexes exceeding 25 trucks, supplemented by crusher burst offloads.

> **Analytical Approximation & Pilot Validation Note:** The $M/M/c$ formulation provides an analytical baseline and sizing bound, but real-world mining shift-change arrivals are batched and dispatch-coordinated rather than memoryless Poisson processes. Furthermore, 60-second spotting and alignment for a 400-tonne hauler in night-time mud or dust conditions is an aggressive estimate that may vary with driver skill or robotic positioning precision. Exact berth occupancy (T_s) and empirical arrival distributions must be measured and validated during Phase 1/2 pilot trials to tune bay sizing.

---

## 4. Quantitative Reduction Funnel across Scale Tiers

| Tier | Transmission Medium | Volume (10-Truck Cell) | Volume (100-Truck Site) | Latency / Frequency | Architectural Purpose |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Tier 1: Immediate Telemetry** | Private 5G / Starlink Satellite | **~1–2 GB / day** | **~10–20 GB / day** | Real-time (<500ms) | Fleet safety alerts, disengagement coordinates, and JSON metadata catalog. |
| **Tier 2: Sharded Edge Ingestion** | 10 Gbps Optical Dock + mmWave / Wi-Fi 6 | **~30–50 TB / day** (raw) or **~0.5–1.0 TB** (pruned) | **~300–500 TB / day** (raw) or **~5–10 TB** (pruned) | Hourly / Shift-change | Ingestion of raw shift logs or candidate snippets into local Edge Pods. |
| **Tier 3: Cloud GDS Ingestion** | Cloud-directed pull over night-time WAN / Sat | **~10–20 GB / day** | **~20–50 GB / day** | 12–24 hours | Highest-priority deduplicated GDS snippets and auto-labeled training cases. |
| **Tier 4: Physical Archive (Sneakernet)** | Rugged U.2/U.3 NVMe storage shuttles | **5–10 TB / month** (on demand) | **20–50 TB / batch** (bi-weekly) | 7–14 days transit | Regulatory compliance, catastrophic incident replays, and long-term cold archives. |

---

## 5. Hybrid Transport Middleware: Resolving the DDS Wireless Dilemma

A major operational failure mode in distributed vehicle-to-depot robotics is relying on standard Data Distribution Service (DDS) protocols across wireless boundaries:
* **The Problem:** eProsima Fast DDS and CycloneDDS provide nanosecond-level shared-memory IPC on-vehicle, but rely on continuous multicast Simple Participant Discovery Protocol (SPDP) broadcasts. When haul trucks enter intermittent wireless zones around depot bays, DDS discovery initiates packet storms, saturating wireless bandwidth, exhausting CPU cycles, and dropping telemetry.
* **The Architecture:** The system decouples internal vehicle IPC from external fleet transport:

```mermaid
flowchart TD
    subgraph Vehicle ["On-Vehicle Sensor & Autonomy Bus"]
        Sensors["Cameras, LiDARs, Radars, Planners, Safety Nodes"]
        Sensors -->|"Low-Latency Shared Memory / RTPS"| FastDDS["eProsima Fast DDS"]
        FastDDS -->|"Localhost Domain 0 Only"| ZenohBridge["zenoh-bridge-dds Plugin"]
    end

    subgraph Network ["Vehicle-to-Depot Network (Optical Dock / Wi-Fi 6)"]
        ZenohBridge -->|"Eclipse Zenoh over TCP/QUIC (Gossip Discovery)"| DepotRouter["Depot zenohd Router"]
    end

    subgraph Depot ["Site Depot Staging Infrastructure"]
        DepotRouter --> NAS["Depot Edge NAS Ingestion Pipeline"]
    end
```

* **Eclipse Zenoh** bridges the vehicle to the depot server. By replacing multicast discovery with set-theoretic resource keys and gossip-based scouting, Zenoh maintains deterministic, low-overhead data transport over lossy or intermittent wireless channels without network flooding.

### 5.1 Vehicle-to-Depot Middleware Configuration (`zenoh_bridge_config.json5`)

```json5
{
  plugins: {
    dds: {
      domain: 0,
      localhost_only: true,
      allow: {
        publishers: [
          "/triage/candidate_metadata",
          "/chassis/critical_kinematics",
          "/sensors/diagnostics"
        ],
        subscribers: [
          "/fleetwise/dynamic_schemes",
          "/depot/vector_gallery_update"
        ]
      }
    }
  },
  transport: {
    unicast: {
      endpoints: ["tcp/10.240.12.1:7447"],
      multicast_scouting: false
    },
    link_loss_action: "BUFFER_IN_LOCAL_RING",
    buffer_management: {
      max_buffer_size_mb: 2048,
      overflow_action: "DROP_LOWEST_PRIORITY_TIER_5", // Aligned directly with storage degradation tiers
      priority_shedding_order: [
        "DROP_FILTER_5_ODD_SAMPLES",
        "DROP_FILTER_4_CAMPAIGNS",
        "DROP_FILTER_2_UNCERTAINTY",
        "PRESERVE_FILTER_1_IMMUTABLE"
      ]
    }
  }
}
```

---

## 6. Subsystem References

* **Stäubli International AG:** [QCC Automatic Quick Charging and Multi-Pole Connectors for Industrial Vehicles](https://www.staubli.com/en/electrical-connectors/products/multi-pole-connectors/qcc.html) – *Automated industrial coupling interface with high-pressure air purge for heavy dust environments.*
* **Cavotec SA:** [Automated Connection Systems for Mining & Heavy Industry](https://www.cavotec.com/industry/mining-tunnelling) – *Robotic mating systems engineered for open-pit and underground mobile equipment.*
* **SAE International:** [SAE J3105/3: Recommended Practice for Electric Vehicle Automated Conductive Connection (Enclosed Pin and Socket)](https://www.sae.org/standards/content/j3105/3_202001/) – *Industrial automated connection practice; referenced for mechanical form-factor and pin-and-socket envelope reuse to house expanded-beam optical contacts alongside DC power.*
* **In A Blink:** [Virtual Fiber Optics (VFO) Free-Space Optical Wireless Data Transfer](https://inablink.zone/) – *Line-of-sight optical wireless communications (2.5–10 Gbps) immune to RF multipath interference.*
* **eProsima:** [Fast DDS (Fast RTPS): High-Performance OMG DDS Implementation](https://www.eprosima.com/index.php/products-all/eprosima-fast-dds) – *Real-time publish-subscribe middleware for deterministic in-vehicle intra-node IPC.*
* **Eclipse Foundation:** [Eclipse Zenoh: Zero Overhead Pub/Sub, Store, and Query Protocol](https://zenoh.io/) – *Gossip-scouting and unicast transport resolving DDS discovery storms across lossy wireless links.*
