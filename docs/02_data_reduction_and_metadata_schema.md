# Specification 02: Data Reduction & Metadata Schema

**Document Version:** 2.1  
**Status:** Approved Architecture Specification  
**Parent Document:** [Master System Architecture & Site Infrastructure Overview](file:///home/jwesterl/Downloads/opencode/edge-data/docs/golden_data_set_architecture.md)  
**Target Audience:** Data Engineers, Tooling Developers, Autonomy Infrastructure Teams

---

## 1. Temporal Ring Buffering

Every haul truck maintains a circular rolling buffer in high-speed RAM and local high-endurance NVMe storage:
* **Duration:** 45 seconds total (T - 30s pre-trigger, T + 15s post-trigger).
* **Engineering Rationale:** An autonomous disengagement, traction slip, or emergency stop (E-Stop) is the *downstream consequence* of an environmental anomaly or perception failure that manifested 10 to 20 seconds earlier (e.g., an unmapped rock on a haul ramp, a misclassified windrow berm, or progressive lens mud splatter). The 30-second pre-event buffer captures the upstream root cause, while the 15-second post-event buffer captures the vehicle's dynamic avoidance response and stabilized stopping state.

---

## 2. Spatial Frustum & Channel Pruning

When a triage filter flags an anomaly, the recording pipeline strips non-informative sensory streams:

| Channel / Sensor Stream | Retention Decision | Resolution & Processing Handling |
| :--- | :--- | :--- |
| **Front-Center 8MP Camera** | **KEEP** (High Resolution) | Full frame retained for forward visual obstacle verification. |
| **Primary Forward 128-Beam LiDAR** | **KEEP** (High Resolution) | Full-density point cloud retained across forward azimuth. |
| **Forward 4D Imaging Radar** | **KEEP** (High Resolution) | Full Doppler elevation and velocity tracks preserved. |
| **High-Rate IMU & Steer/Brake CAN** | **KEEP** (High Resolution) | Dynamic telemetry bus recorded at native 100 Hz frequency. |
| **Rear Perimeter Cameras** | **DROP** *(Forward)* / **KEEP** *(Reversing)* | Pruned during nominal forward haul; dynamically retained at high resolution if in reverse gear or tipping at crusher/dump. |
| **Cabin Driver-Facing Camera** | **DROP** | Completely excluded from perception training sets. |
| **Blind-Spot Side Radars** | **DROP** | Lateral radar clusters dropped to conserve storage during forward haul. |
| **Surrounding Auxiliary Channels** | **DROP / HEAVILY COMPRESS** | Stripped before staging to onboard NVMe (saves 70%–85% overall). |

* **Bandwidth Savings:** Eliminating unnecessary camera and sensor angles reduces individual snippet size by **70% to 85%**.

> **Reversing & Hopper Maneuvering Frustum Exception:** Unconditionally dropping rear and side views creates unacceptable blindness during high-risk maneuvers. Haul truck reverse maneuvers at the primary crusher hopper or dump edge account for significant collision hazards. If a trigger occurs while the CAN powertrain indicates reverse gear or geofencing locates the truck within a dump/crusher pocket, the pruning mask dynamically flips: rear-facing vision, perimeter LiDAR beams, and rear radars are promoted to **KEEP** at native resolution, while forward channels are decimated.

---

## 3. Decimation & Perceptual Compression

Following frustum pruning, the staged snippet undergoes perceptual decimation:
* **Frame Decimation:** For heavy haul trucks operating at open-pit speeds (15–35 km/h), vehicle displacement between consecutive frames at 30 FPS provides high redundancy. Camera feeds are decimated from 30 FPS down to 10 FPS without degrading spatial training utility for 3D bounding-box perception models.
* **LiDAR Quantization:** Point clouds outside the operational design domain (e.g., high sky points or returns beyond 100m) are cropped. Spatial coordinates (X, Y, Z) are converted from 32-bit floating-point coordinates to 16-bit fixed-point representations, saving an additional 50% in point cloud memory footprints.

---

## 4. Metadata Schema Specification (`gds_metadata_v2.json`)

The architecture enforces a **metadata-first paradigm**: rather than moving gigabytes of raw MCAP bags over constrained links, each snippet produces a standardized, low-overhead JSON record (<5 KB). Central cloud curation engines query these metadata records to select specific surgical blobs for WAN uplink.

```json
{
  "$schema": "https://specs.autonomy-mining.org/v2/gds-metadata.json",
  "snippet_id": "SNIP-20261002-TRK042-00941",
  "truck_id": "HAUL-TRUCK-042",
  "site_id": "MINE-PILBARA-WEST",
  "timestamp_utc_start": "2026-10-02T08:12:10.000000Z",
  "timestamp_utc_trigger": "2026-10-02T08:12:40.000000Z",
  "timestamp_utc_end": "2026-10-02T08:12:55.000000Z",
  "software_manifest": {
    "autonomy_stack_version": "v4.14.0-prod",
    "active_perception_hash": "b9e01d5f348a",
    "previous_perception_hash": "a8f90c4e127f",
    "vector_space_version": "v3.2",
    "active_harvesting_campaigns": ["CAMP-2026-BERM-DETECTION"]
  },
  "clock_synchronization_telemetry": {
    "ptp_profile": "IEEE_1588_PTPV2_BOUNDARY",
    "master_oscillator_type": "MICROCHIP_SA45S_CSAC",
    "gnss_denial_duration_seconds": 14280.4,
    "estimated_phase_drift_nanoseconds": 342,
    "sync_status": "PTP_LOCKED_HOLDOVER_NOMINAL"
  },
  "geospatial_telemetry": {
    "geohash_sector": "q3g8p2m",
    "pit_sector": "BENCH_04_SOUTH_RAMP",
    "elevation_amsl_meters": 312.4,
    "road_grade_percent": -7.8,
    "ground_speed_kph": 24.2,
    "payload_state": "LOADED_IRON_ORE_380T"
  },
  "triage_evaluations": [
    {
      "filter_id": "FILTER_1_KINEMATIC",
      "triggered": false,
      "lateral_acceleration_g": 0.12,
      "longitudinal_deceleration_g": 0.08,
      "time_to_collision_seconds": 6.8
    },
    {
      "filter_id": "FILTER_2_UNCERTAINTY",
      "triggered": true,
      "epistemic_entropy_score": 0.78,
      "bounding_box_jitter_variance": 0.042,
      "sensor_divergence_flag": "LIDAR_VISION_DISAGREEMENT"
    },
    {
      "filter_id": "FILTER_3_VECTOR_NOVELTY",
      "triggered": true,
      "metric_name": "cosine_distance_compensated",
      "threshold": 0.72,
      "measured_value": 0.89,
      "drift_compensation_applied": true
    }
  ],
  "embedding_payload": {
    "dimensions": 128,
    "model_backbone_hash": "b9e01d5f348a",
    "drift_compensation_vector_norm": 0.0241,
    "vector_data": [0.0381, -0.1422, 0.8912, 0.0054, -0.0612]
  },
  "offload_lifecycle": {
    "offload_interface_used": "PHYSICAL_OPTICAL_DOCK_10G",
    "raw_optical_transfer_duration_seconds": 38.4,
    "total_berth_occupancy_seconds": 224.6,
    "berth_breakdown_seconds": {
      "spotting_and_robotic_alignment": 58.2,
      "pneumatic_purge_and_latch": 31.0,
      "raw_optical_data_payload_transfer": 38.4,
      "manifest_verify_and_unlatch": 37.0,
      "bay_departure_and_clearance": 60.0
    },
    "channel_pruning_mask": [
      "cam_front_center_8mp",
      "lidar_128_beam_main",
      "radar_4d_imaging_front",
      "vehicle_telemetry_bus"
    ],
    "storage_capacity_at_offload_percent": 68.2,
    "depot_storage_uri": "mcap://nas01.depot/staging/20261002/SNIP-20261002-TRK042-00941.mcap"
  }
}
```

---

## 5. Subsystem References

* **Foxglove Technologies:** [MCAP: High-Performance Open Container Format for Robotics](https://mcap.dev/) – *Append-only, serialization-agnostic log container optimized for high-frequency multi-modal sensor streaming.*
* **IEEE Standards Association:** [IEEE 1588-2019: Standard for a Precision Clock Synchronization Protocol for Networked Measurement and Control Systems (PTPv2)](https://standards.ieee.org/ieee/1588/6825/) – *Sub-microsecond hardware timestamping across automotive Ethernet and GMSL2 sensor gateways.*
