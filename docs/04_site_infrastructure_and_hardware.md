# Specification 04: Site Infrastructure, Hardware Hardening & Storage Lifecycle

**Document Version:** 2.1  
**Status:** Approved Architecture Specification  
**Parent Document:** [Master System Architecture & Site Infrastructure Overview](./golden_data_set_architecture.md)  
**Target Audience:** Hardware Engineers, Electrical & Packaging Teams, Infrastructure Operations Leads

---

## 1. On-Truck Storage Endurance, Hardware PLP & Thermal Contention

Continuous raw multi-sensor streaming on heavy haulers generates sustained write workloads between **35 and 60 MB/s per truck**, accumulating **3.0 to 5.2 TB of raw sensor data per 24-hour production shift**. In rugged open-pit mining environments, off-the-shelf commercial storage systems fail rapidly due to write exhaustion, thermal throttling, and sudden power cutoffs.

The architecture enforces four strict hardware storage standards:
* **Drive Endurance Specification:** Mandate enterprise-grade U.2/U.3 NVMe SSDs rated for **≥ 3 Drive Writes Per Day (DWPD)** over a 5-year operating warranty (e.g., **Micron 7450 MAX or Solidigm D7-P5810**). A 15.36 TB drive at 3 DWPD provides **>84 Petabytes Written (PBW)** of endurance. Standard consumer or datacenter SSDs (<1 DWPD) will exhaust their Program/Erase (P/E) cycles within 12–18 months.
* **Hardware Power-Loss Protection (Level-4 PLP):** Mining haul trucks frequently experience ungraceful master battery isolator trips during servicing. All onboard NVMe SSDs must incorporate discrete onboard tantalum capacitor arrays (e.g., ATP Level-4 Industrial PLP) providing sufficient holdup power to flush volatile DRAM cache and the Flash Translation Layer (FTL) to non-volatile flash, preventing filesystem corruption.
* **Thermal Management & Vibration Resilience:** Storage enclosures must be shock-mounted (MIL-STD-810H compliant) and utilize conduction cooling blocks tied to the vehicle chassis. Drives must maintain sustained full-rate writes without thermal throttling up to **+55°C ambient cabin air temperatures**.
* **PCIe Bus Isolation:** Direct Memory Access (DMA) and storage write queues are isolated on dedicated PCIe Gen4 x4 lanes separate from the safety-critical autonomy and path-planning buses.

---

## 2. Hardware-Backed PTP Holdover Circuitry (GNSS Outage Protection)

Deep open-pit benches frequently experience complete GNSS RTK dropouts, carrier-phase cycle slips, and satellite constellation shadowing from highwalls. If the vehicle relies solely on GNSS-derived 1PPS clock signals, loss of lock causes rapid phase drift across the sensor suite. At 36 km/h (10.0 m/s), a timing desynchronization of just **10 milliseconds** between an 8MP camera exposure and a 10 Hz LiDAR sweep produces a **10-centimeter spatial registration error**, causing bounding-box jitter, distorting 3D occupancy grids, and corrupting 4D auto-labeling reconstructions.

To maintain sub-millimeter multi-modal sensor alignment, timing drift must remain strictly below **1.0 µs over a continuous 24-hour GNSS denial window** (IEEE 1588 PTPv2):

| Timing Reference Technology | Frequency Stability (σ_y at τ = 1000s) | Typical Daily Frequency Drift | Maximum Time Error after 24h Outage | Sub-Microsecond Holdover Duration | Operational Viability in Deep Pits |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Standard Quartz TCXO** | ~1 × 10⁻⁸ | ~1 × 10⁻⁷ / day | ~5.0 ms | < 30 seconds | **Unacceptable:** Causes severe spatial registration errors within minutes. |
| **Stratum 3E Quartz OCXO** | ~1 × 10⁻¹⁰ | ~1 × 10⁻⁹ / day | ~10 to 50 µs | ~ 2 to 4 hours | **Marginal:** Requires recurring surface fixes between pit haulage cycles. |
| **Ruggedized MEMS Super-TCXO (SiTime SiT7111)** | ~5 × 10⁻¹¹ | ~5 × 10⁻¹⁰ / day | ~40 to 50 µs | ~ 4 to 8 hours | **Marginal-to-High:** Superior resistance to heavy vehicle shock, vibration, and thermal transients, but linear drift extrapolation still exceeds sub-µs budget well before 24h; viable only with mid-shift PTP re-lock opportunities. |
| **Chip-Scale Atomic Clock (Microchip SA.45s / SA.65)** | **< 1.5 × 10⁻¹¹** | **< 3 × 10⁻¹⁰ / month** | **< 0.8 µs over 24h** | **> 24 to 48 hours** | **Mission-Critical:** Guarantees sub-microsecond IEEE 1588 PTP alignment throughout continuous deep-bench operations. |

* **Hardware Implementation:** The primary on-vehicle network switch incorporates an integrated **Microchip SA.45s Chip-Scale Atomic Clock (CSAC)**. Consuming under 120 mW and occupying less than 17 cm³, the CSAC's coherent population trapping (CPT) rubidium physics package maintains clock drift <0.8 µs over 24 hours of total GNSS denial, constraining spatial registration error below 0.01 mm at haul speeds.
* **Empirical Holdover Pilot Validation Note:** While the SA.45s datasheet rates holdover at <0.8 µs / 24h under controlled bench conditions, severe continuous harmonic vibration from 4,000 HP diesel-electric drivetrains and extreme diurnal temperature swings (-20°C to +55°C) can induce accelerated crystal stress and phase jitter. True field holdover performance must be empirically benchmarked during initial site pilot testing.

---

## 3. Graceful Storage Degradation Policy (Queue-Overflow Management)

If a haul truck is delayed in returning to the fueling depot or experiences temporary docking offload failures, onboard NVMe storage will reach capacity. To prevent buffer overflows or uncommanded dropped frames, the vehicle edge agent enforces a strict **Priority-Based Dynamic Pruning Sequence**:

| Degradation Tier | NVMe Capacity | Triggered Action | Operational Rationale |
| :--- | :--- | :--- | :--- |
| **Threshold 1** | **>80%** | **Purge Nominal Stratified Baseline Samples (Filter 5)** | Discard redundant nominal anchors; non-critical. |
| **Threshold 2** | **>85%** | **Quantize LiDAR Point Clouds on Candidate Snippets** | Crop points >50m, quantize 32-bit floats to 16-bit fixed-point. |
| **Threshold 3** | **>90%** | **Drop Secondary / Perimeter Camera Views** | Prune frustums to forward-facing 8MP camera only; saves 75% frame volume. |
| **Threshold 4** | **>95%** | **Lock Safety-Critical & E-Stop Snippets (Filter 1 - Immutable)** | Drop un-indexed Filter 2 uncertainty clips to guarantee storage for mandatory E-Stop logs. |

### 3.1 Storage Eviction Configuration (`storage_eviction_policy.yaml`)

```yaml
storage_eviction_manager:
  monitored_mount: "/mnt/nvme_staging"
  polling_interval_seconds: 5
  hysteresis_percent: 3.0       # Requires capacity to fall 3% below trigger before de-escalating
  dwell_time_seconds: 30        # Capacity must remain above threshold for 30s before triggering
  dry_run: false                # When true, logs eviction actions without modifying files
  thresholds:
    nominal_baseline_drop:
      trigger_capacity_percent: 80.0
      action: "PURGE_FILTER_5_ODD_SAMPLES"
      log_level: "INFO"
    pointcloud_quantization:
      trigger_capacity_percent: 85.0
      action: "QUANTIZE_LIDAR_16BIT_CROP_50M"
      log_level: "WARNING"
    frustum_pruning:
      trigger_capacity_percent: 90.0
      action: "DROP_SECONDARY_CAMERA_CHANNELS"
      retained_channels: ["cam_front_center_8mp", "lidar_main", "can_raw"]
      log_level: "WARNING"
    emergency_lockout:
      trigger_capacity_percent: 95.0
      action: "PRESERVE_FILTER_1_ONLY_DROP_UNINDEXED"
      log_level: "CRITICAL"
```

> **Anti-Flapping Hysteresis & Dwell:** To prevent rapid oscillation between degradation tiers when storage hovers around trigger boundaries (e.g. fluctuating at 79.9%–80.2%), the manager enforces a 30-second dwell window before escalation and a 3.0% hysteresis margin before relaxing an active pruning policy. The `dry_run` mode enables harmless verification during initial commissioning.

---

## 4. Modular Skid-Mounted Edge Compute Pods

To accommodate dynamic open-pit topography and eliminate the single-depot bottleneck, site edge compute is packaged into **standardized, modular Edge Station Pods** sized for 5 to 10 vehicles:
* **Physical Form Factor:** 4U shock-mounted chassis housed inside an outdoor NEMA 4X / IP66 weather-sealed enclosure with closed-loop HVAC (-20°C to +55°C). The entire unit is integrated onto a ruggedized steel skid with fork pockets and lifting eyes, allowing it to be winched onto a flatbed and relocated as mining benches advance.
* **Compute & Acceleration Footprint:** Single-socket AMD EPYC / Intel Xeon (16–32 cores) paired with **1x enterprise GPU (NVIDIA L4 for crusher pods; NVIDIA L40S for fuel-bay triage pods)** with 24–48 GB VRAM to execute Filter 2–3 active learning and Filter 6 coreset deduplication.
* **Storage Sizing:** 40 TB to 80 TB Enterprise U.3 NVMe flash storage per pod, providing 5–7 days of local candidate staging buffer.
* **Truck-to-Station Ingestion Interfaces:** Supports three handoff options matching site operational constraints:
  1. **Hot-Swappable NVMe Sleds (Option A - Zero Vehicle Software Impact):** Operators swap the vehicle's ruggedized U.2/U.3 caddy into the pod's front-loading high-speed ingest bay during scheduled fueling stops (30-second swap; bus-speed transfer).
  2. **Parasitic Flight-Recorder Offload (Option B):** Vehicles equipped with isolated secondary logging PCs offload over directed mmWave or optical links without touching primary autonomy compute.
  3. **Automated Optical Docking (Option C):** Stationary fuel islands utilize Stäubli QCC / Cavotec robotic arms with 10G/25G optical transceivers and air-purge dust nozzles.
* **Automated Retention Lifecycle:**
  * **Day 0–3:** Full uncompressed candidate snippets preserved in high-speed NVMe flash tier.
  * **Day 4–7:** If not requested for cloud pull, downsample point clouds and compress imagery by 50% into secondary tier.
  * **Day 14:** Hard eviction of unrequested candidate snippets.
* **Edge Vector Re-Indexing Daemon:** Runs background batch embedding jobs across local baseline datasets whenever an OTA update introduces a new vision backbone model hash.

---

## 5. Data Security, Chain of Custody & Access Control

Every tier in this architecture — on-vehicle staging, physical docking, depot NAS, and sneakernet shuttles — moves or holds safety-relevant and potentially commercially sensitive operational data (haul routes, payload volumes, production cadence, incident footage):

* **Encryption in Transit:** All vehicle-to-depot links (optical dock, VFO, Wi-Fi 6 fallback) and depot-to-cloud WAN uplinks must use authenticated, encrypted transport (TLS 1.3 or equivalent over the Zenoh TCP/QUIC transport) rather than relying on physical/RF link obscurity as a security boundary — dust and multipath are availability concerns, not confidentiality controls.
* **Encryption at Rest, SED Key Management & Rotation:** On-vehicle NVMe staging and the depot NAS utilize Self-Encrypting Drives (SEDs) with hardware AES-256-XTS. Key Encryption Keys (KEKs) are managed via on-site Hardware Security Modules (HSMs) or enterprise HashiCorp Vault instances running on Edge Pods, enforcing automated quarterly key rotation and instant cryptographic erasure ("crypto-shredding") for decommissioned or compromised drives.
* **Docking Authentication & PKI:** The physical optical dock and VFO links enforce hardware-rooted mutual TLS (mTLS) authentication. Both the vehicle gateway and the depot docking berth present X.509 certificates anchored in on-chip TPM 2.0 security modules prior to opening Zenoh data channels, preventing rogue endpoints from exfiltrating data or injecting forged vector baselines.
* **Chain of Custody for Sneakernet Shuttles (Tier 4):** Physical NVMe shuttles carrying 20–50 TB of raw archive data for forensic investigations or regulatory audits require strict evidentiary custody: tamper-evident enclosures with serialized seals, accompanied by an Ed25519-signed manifest (containing SHA-256 digests of every MCAP block) generated at the depot pod before dispatch. Upon delivery at the central cloud ingestion facility, automated checksum verification validates file integrity against the signed manifest before ingest admission, closing the custody gap.
* **Config/Firmware Integrity:** OTA-delivered triage thresholds, harvesting campaign definitions, and drift-compensation vectors are safety- and evidence-relevant configurations and must be cryptographically signed by autonomy engineering and verified against local hardware TPMs upon receipt.

---

## 6. Subsystem References

* **Microchip Technology:** [SA.45s Chip-Scale Atomic Clock (CSAC) Technical Specification](https://www.microchip.com/en-us/product/sa45s) – *Physics package consuming <120 mW with <0.8 µs holdover time drift over 24-hour GNSS denial.*
* **SiTime Corporation:** [Precision Timing in Defense and Autonomous Open Systems Architecture](https://www.sitime.com/company/newsroom/blog/precision-timing-heart-defense-open-architecture-systems) – *Ruggedized MEMS oscillators (SiT7111) resistant to mechanical shock and heavy vehicle vibration.*
* **IEEE Standards Association:** [IEEE 1588-2019: Standard for a Precision Clock Synchronization Protocol for Networked Measurement and Control Systems (PTPv2)](https://standards.ieee.org/ieee/1588/6825/) – *Sub-microsecond hardware timestamping across automotive Ethernet and GMSL2 sensor gateways.*
* **Micron Technology:** [Micron 7450 MAX Enterprise NVMe SSD with 3 DWPD Endurance](https://www.micron.com/products/ssd/product-lines/7450) – *High-endurance enterprise storage specification (>84 PBW for 15.36 TB) engineered for 24/7 continuous writes.*
* **Solidigm:** [Solidigm D7-P5810 High-Endurance PCIe 4.0 Storage](https://www.solidigm.com/products/data-center/d7.html) – *Extreme endurance NVMe drives built for sustained write-heavy edge buffer applications.*
* **ATP Electronics:** [Hardware Power-Loss Protection (PLP) and Level-4 Industrial SSD Reliability](https://www.atpinc.com/about/news/highest-endurance-industrial-ssd) – *Onboard tantalum capacitor hold-up circuitry ensuring DRAM and FTL cache safety during sudden power cuts.*
