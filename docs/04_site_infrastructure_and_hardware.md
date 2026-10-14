# Specification 04: Site Infrastructure, Hardware Hardening & Storage Lifecycle

**Document Version:** 2.1  
**Status:** Approved Architecture Specification  
**Parent Document:** [Master System Architecture & Site Infrastructure Overview](./golden_data_set_architecture.md)  
**Target Audience:** Hardware Engineers, Electrical & Packaging Teams, Infrastructure Operations Leads

---

## 1. On-Truck Storage Endurance, Hardware PLP & Thermal Contention

Continuous raw multi-sensor streaming on heavy haulers generates sustained write workloads between **35 and 60 MB/s per truck**, accumulating **3.0 to 5.2 TB of raw sensor data per 24-hour production shift**. In rugged open-pit mining environments, off-the-shelf commercial storage systems fail rapidly due to write exhaustion, thermal throttling, and sudden power cutoffs.

The architecture enforces four strict hardware storage standards:
* **Drive Endurance Specification:** Mandate enterprise-grade U.2/U.3 NVMe SSDs rated for **≥ 3 Drive Writes Per Day (DWPD)** over a 5-year operating warranty:
  * **Bulk Storage Tier (≥ 3 DWPD):** Deploy high-endurance enterprise drives such as the **Micron 7450 MAX (12.8 TB @ 3 DWPD ≈ 70 PBW random / 119 PBW sequential)**, **Solidigm D7-P5620 (12.8 TB @ 3 DWPD ≈ 70 PBW)**, or **Kioxia CM7-V (12.8 TB @ 3 DWPD ≈ 70 PBW)**. (Note: standard 15.36 TB enterprise drives such as the Micron 7450 PRO are rated for only 1 DWPD, which risks premature wearout within 18–24 months under continuous recording).
  * **Extreme-Endurance SLC Write Buffer (Optional Acceleration Tier):** High-write burst tiers can optionally integrate a dedicated **Solidigm D7-P5810 (800 GB to 1.6 TB SLC, rated for 50–65 DWPD, >73 PBW)** as a ring buffer cache to absorb high-frequency raw sensor streams before flushing to bulk flash.
  * Across a 12.8 TB bulk drive rated for 3 DWPD, cumulative endurance reaches **~70 PBW**, easily absorbing continuous 35–60 MB/s logging over 5+ years.
* **Hardware Power-Loss Protection (Level-4 PLP):** Mining haul trucks frequently experience ungraceful master battery isolator trips during servicing. All onboard NVMe SSDs must incorporate discrete onboard tantalum capacitor arrays (e.g., ATP Level-4 Industrial PLP) providing sufficient holdup power to flush volatile DRAM cache and the Flash Translation Layer (FTL) to non-volatile flash, preventing filesystem corruption.
* **Thermal Management & Vibration Resilience:** Storage enclosures must be shock-mounted (MIL-STD-810H compliant) and utilize conduction cooling blocks tied to the vehicle chassis. Drives must maintain sustained full-rate writes without thermal throttling up to **+55°C ambient cabin air temperatures**.
* **PCIe Bus Isolation:** Direct Memory Access (DMA) and storage write queues are isolated on dedicated PCIe Gen4 x4 lanes separate from the safety-critical autonomy and path-planning buses.

---

## 2. Hardware-Backed PTP Holdover Circuitry (GNSS Outage Protection)

Deep open-pit benches frequently experience complete GNSS RTK dropouts, carrier-phase cycle slips, and satellite constellation shadowing from highwalls. If the vehicle relies solely on GNSS-derived 1PPS clock signals, loss of lock causes rapid phase drift across the sensor suite. At 36 km/h (10.0 m/s), a timing desynchronization of just **10 milliseconds** between an 8MP camera exposure and a 10 Hz LiDAR sweep produces a **10-centimeter spatial registration error**, causing bounding-box jitter, distorting 3D occupancy grids, and corrupting 4D auto-labeling reconstructions.

To maintain sub-millimeter multi-modal sensor alignment, timing drift must remain strictly below **1.0 µs over a continuous 24-hour GNSS denial window** (IEEE 1588 PTPv2):

| Timing Reference Technology | Frequency Stability (σ_y at τ = 1000s) | Typical Daily Frequency Drift | Maximum Time Error after 24h Outage | Sub-Microsecond Holdover Duration | Operational Viability in Deep Pits |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Standard Quartz TCXO** | ~1 × 10⁻⁸ | ~1 × 10⁻⁷ / day | **~8.64 ms** | < 10 to 30 seconds | **Unacceptable:** Causes severe spatial registration errors within minutes. |
| **Stratum 3E Quartz OCXO** | ~1 × 10⁻¹⁰ | ~1 × 10⁻⁹ / day | **~86.4 µs** | ~ 15 to 30 minutes | **Marginal:** Requires recurring surface fixes between pit haulage cycles. |
| **Ruggedized MEMS Super-TCXO (SiTime SiT7111)** | ~5 × 10⁻¹¹ | ~5 × 10⁻¹⁰ / day | **~43.2 µs** | ~ 1 to 2 hours | **Marginal-to-High:** Superior resistance to heavy vehicle shock, vibration, and thermal transients, but linear drift extrapolation exceeds sub-µs budget well before 24h; viable only with mid-shift PTP re-lock opportunities. |
| **Chip-Scale Atomic Clock (Microchip SA.45s / SA.65)** | **< 1.5 × 10⁻¹¹** | **< 3 × 10⁻¹⁰ / month** | **< 0.8 µs over 24h** | **> 24 to 48 hours** | **Mission-Critical:** Guarantees sub-microsecond IEEE 1588 PTP alignment throughout continuous deep-bench operations. |

* **Hardware Implementation:** The primary on-vehicle network switch incorporates an integrated **Microchip SA.45s Chip-Scale Atomic Clock (CSAC)**. Consuming under 120 mW and occupying less than 17 cm³, the CSAC's coherent population trapping (CPT) rubidium physics package maintains clock drift <0.8 µs over 24 hours of total GNSS denial, constraining spatial registration error below 0.01 mm at haul speeds.
* **Thermal Operating Envelopes (SA.45s vs. SA.65):** The ultra-low-power SA.45s (<120 mW) is specified for standard industrial operating ranges (-10°C to +70°C). For extreme cold or desert installations requiring a wide-temperature envelope (-40°C to +85°C), the ruggedized **Microchip SA.65 CSAC** is selected (at the trade-off of higher operating power, ~1.0W).
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
  dry_run: true                        # Default true for safe commissioning; set false in production
  deactivation_hysteresis_percent: 5.0 # Capacity must fall 5.0% below threshold to release policy
  escalation_dwell_seconds: 30         # Capacity must exceed threshold continuously for 30s before triggering
  default_retention_days: 14           # Standard local storage retention before hard eviction
  thresholds:
    nominal_baseline_drop:
      trigger_capacity_percent: 80.0
      action: "PURGE_FILTER_5_ODD_SAMPLES"
      dwell_seconds: 30
      log_level: "INFO"
    pointcloud_quantization:
      trigger_capacity_percent: 85.0
      action: "QUANTIZE_LIDAR_16BIT_CROP_50M"
      dwell_seconds: 45
      log_level: "WARNING"
    frustum_pruning:
      trigger_capacity_percent: 90.0
      action: "DROP_SECONDARY_CAMERA_CHANNELS"
      retained_channels:
        - "cam_front_center_8mp"
        - "lidar_128_beam_main"
        - "radar_4d_imaging_front"
        - "vehicle_telemetry_bus"
      dwell_seconds: 60
      log_level: "WARNING"
    emergency_lockout:
      trigger_capacity_percent: 95.0
      action: "PRESERVE_FILTER_1_ONLY_DROP_UNINDEXED"
      dwell_seconds: 15
      log_level: "CRITICAL"
```

> **Anti-Flapping Hysteresis & Dwell:** To prevent rapid oscillation between degradation tiers when storage hovers around trigger boundaries (e.g. fluctuating at 79.9%–80.2%), the manager enforces a 30-to-60 second dwell window before escalation and a 5.0% hysteresis margin before relaxing an active pruning policy. The `dry_run: true` default prevents accidental file deletion during commissioning.

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

* **Encryption in Transit:** All vehicle-to-depot links (optical dock, VFO, Wi-Fi 6 fallback) and depot-to-cloud WAN uplinks enforce authenticated, encrypted transport (TLS 1.3 over the Zenoh TCP/QUIC transport) rather than relying on physical/RF link obscurity as a security boundary — dust and multipath are availability concerns, not confidentiality controls.
* **Encryption at Rest & Vault KEK/DEK Unseal Sequence:**
  * On-vehicle NVMe staging and depot NAS storage utilize hardware-encrypted Self-Encrypting Drives (SEDs) with AES-256-XTS.
  * Internal Data Encryption Keys (DEKs) are protected by Key Encryption Keys (KEKs) managed by on-site HashiCorp Vault clusters running on Edge Pods or hardware-backed PKCS#11 HSMs.
  * *Cryptographic Unseal Sequence:* At boot or pod docking, the vehicle's TPM 2.0 generates a cryptographically signed PCR measurement quote proving firmware integrity (UEFI, kernel, bootloader). The quote is submitted to the Vault agent over TLS 1.3 to release the KEK. If an NVMe drive caddy is physically extracted from a truck without authorized PCR measurements, the DEK remains locked and all stored blocks remain cryptographically inaccessible. Automated quarterly KEK re-wrapping and instant crypto-shredding (purging DEKs via ATA/NVMe cryptographic erase) are enforced during decommission.
* **Docking Authentication & Intermediate CA PKI:**
  * Physical optical docks and VFO links enforce hardware-rooted mutual TLS (mTLS) authentication. Both the truck gateway and the depot docking berth present X.509 certificates anchored in on-chip TPM 2.0 security modules prior to opening Zenoh middleware channels.
  * *Offline Resiliency:* Certificates are issued by an enterprise Intermediate CA with pre-distributed offline Certificate Revocation Lists (CRLs) and cached Online Certificate Status Protocol (OCSP) responses stored locally on the Edge Pod. This enables full cryptographic handshake validation even during complete satellite WAN blackouts, while instantly denying dock access to revoked or compromised vehicles.
* **Chain of Custody & Ed25519 Sneakernet Manifests (Tier 4):**
  * Physical NVMe storage shuttles (transporting 15–30 TB batches of raw forensic data) are housed in ruggedized, tamper-evident locking cases with serialized tamper-evident barcode seals.
  * Prior to shuttle ejection from the Edge Station Pod, an automated pipeline hashes every MCAP log file using SHA-256 and compiles an authoritative cryptographic manifest (`manifest.json` containing file paths, byte sizes, timestamps, and SHA-256 digests).
  * The manifest is cryptographically signed using the Edge Pod's TPM-backed Ed25519 private key, producing `manifest.sig`.
  * Upon physical arrival at the central hyperscaler or cloud intake facility, the ingestion daemon verifies the Ed25519 signature against the known Edge Pod public key and re-computes all file digests prior to cloud lakehouse admission, guaranteeing an unbroken, legally defensible chain of custody.
* **Config/Firmware Integrity:** OTA-delivered triage thresholds, harvesting campaign definitions, and drift-compensation vectors are safety- and evidence-relevant configurations and must be cryptographically signed by autonomy engineering and verified against local hardware TPMs upon receipt.

---

## 6. Subsystem References

* **Microchip Technology:** [SA.45s Chip-Scale Atomic Clock (CSAC) Technical Specification](https://www.microchip.com/en-us/product/sa45s) – *Physics package consuming <120 mW with <0.8 µs holdover time drift over 24-hour GNSS denial (-10°C to +70°C).*
* **Microchip Technology:** [SA.65 Chip-Scale Atomic Clock for Extreme Environments](https://www.microchip.com/en-us/product/sa65) – *Wide-temperature CSAC (-40°C to +85°C) for extreme open-pit climatic conditions.*
* **SiTime Corporation:** [Precision Timing in Defense and Autonomous Open Systems Architecture](https://www.sitime.com/company/newsroom/blog/precision-timing-heart-defense-open-architecture-systems) – *Ruggedized MEMS oscillators (SiT7111) resistant to mechanical shock and heavy vehicle vibration.*
* **IEEE Standards Association:** [IEEE 1588-2019: Standard for a Precision Clock Synchronization Protocol for Networked Measurement and Control Systems (PTPv2)](https://standards.ieee.org/ieee/1588/6825/) – *Sub-microsecond hardware timestamping across automotive Ethernet and GMSL2 sensor gateways.*
* **Micron Technology:** [Micron 7450 MAX Enterprise NVMe SSD with 3 DWPD Endurance](https://www.micron.com/products/ssd/product-lines/7450) – *High-endurance enterprise storage specification (12.8 TB @ 3 DWPD ≈ 70 PBW) engineered for 24/7 continuous writes.*
* **Solidigm:** [Solidigm D7-P5620 & D7-P5810 Storage Architectures](https://www.solidigm.com/products/data-center/d7.html) – *High-endurance NVMe drives built for sustained write-heavy edge buffer and SLC caching applications.*
* **ATP Electronics:** [Hardware Power-Loss Protection (PLP) and Level-4 Industrial SSD Reliability](https://www.atpinc.com/about/news/highest-endurance-industrial-ssd) – *Onboard tantalum capacitor hold-up circuitry ensuring DRAM and FTL cache safety during sudden power cuts.*
