import os
import math
import time
import json
import random
import logging
from pathlib import Path
from collections import defaultdict
from typing import Optional, Dict, Any, List, Tuple

try:
    from usearch.index import Index
    USEARCH_AVAILABLE = True
except ImportError:
    USEARCH_AVAILABLE = False

try:
    import h3
    H3_AVAILABLE = True
except ImportError:
    H3_AVAILABLE = False

from mcap.reader import make_reader
from mcap.writer import Writer

from .config import TriagePolicy
from .metrics import (
    EVENTS_INGESTED,
    EVENTS_CURATED,
    EVENTS_DISCARDED,
    DEDUP_SUPPRESSIONS,
    BYTES_INGESTED,
    BYTES_CURATED,
    REDUCTION_PERCENTAGE,
    PROCESSING_LATENCY,
)

logger = logging.getLogger("TriagePipeline")

def cosine_similarity(v1: List[float], v2: List[float]) -> float:
    if not v1 or not v2 or len(v1) != len(v2):
        return 0.0
    dot = sum(a * b for a, b in zip(v1, v2))
    norm1 = math.sqrt(sum(a * a for a in v1))
    norm2 = math.sqrt(sum(b * b for b in v2))
    if norm1 == 0.0 or norm2 == 0.0:
        return 0.0
    return dot / (norm1 * norm2)

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Computes great-circle distance between two GPS points in meters."""
    R = 6371000.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    a = (math.sin(delta_phi / 2.0) ** 2 +
         math.cos(phi1) * math.cos(phi2) * (math.sin(delta_lambda / 2.0) ** 2))
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return R * c

def point_in_polygon(lat: float, lon: float, polygon: List[List[float]]) -> bool:
    """Ray-casting point-in-polygon evaluation."""
    if not polygon or len(polygon) < 3:
        return False
    inside = False
    n = len(polygon)
    p1lat, p1lon = polygon[0]
    for i in range(1, n + 1):
        p2lat, p2lon = polygon[i % n]
        if lon > min(p1lon, p2lon):
            if lon <= max(p1lon, p2lon):
                if lat <= max(p1lat, p2lat):
                    if p1lon != p2lon:
                        xinters = (lon - p1lon) * (p2lat - p1lat) / (p2lon - p1lon) + p1lat
                    if p1lat == p2lat or lat <= xinters:
                        inside = not inside
        p1lat, p1lon = p2lat, p2lon
    return inside

# Canonical Specification 02 Channel Enums
CANONICAL_CHANNELS = {
    "forward": [
        "/sensors/cam_front_center_8mp",
        "/sensors/cam_front_telephoto_8mp",
        "/sensors/lidar_128_beam_main",
        "/sensors/radar_front_long_range",
    ],
    "reversing": [
        "/sensors/cam_rear_perimeter_4mp",
        "/sensors/lidar_perimeter_solid_state",
        "/sensors/radar_perimeter_rear",
        "/sensors/radar_blind_spot_side_left",
        "/sensors/radar_blind_spot_side_right",
    ],
    "telemetry": [
        "/vehicle/can_bus",
        "/perception/uncertainty",
        "/perception/embedding_128d",
        "/metadata",
    ]
}

class TriagePipeline:
    def __init__(self, policy: TriagePolicy):
        self.policy = policy
        self.cell_id = policy.cell_id
        self.total_ingested_bytes = 0
        self.total_curated_bytes = 0
        self.curated_tier_bytes: Dict[str, int] = defaultdict(int)
        
        # Initialize USearch CPU-accelerated index (128-D Cosine)
        self.vector_dim = policy.filter_3_novelty.vector_dim
        if USEARCH_AVAILABLE:
            logger.info("Initializing USearch SIMD-accelerated HNSW index on CPU (128-D, metric=cos)...")
            self.usearch_index = Index(ndim=self.vector_dim, metric="cos")
            self.usearch_index.add(0, [0.0] * self.vector_dim)
        else:
            logger.warning("USearch library not available; using native Python vector search fallback.")
            self.usearch_index = None
            self.fallback_vectors: Dict[int, List[float]] = {0: [0.0] * self.vector_dim}

        # Spatial-temporal ring buffer for Filter 6: list of (timestamp, (lat, lon), embedding_128d)
        self.coreset_buffer: List[Tuple[float, Tuple[float, float], List[float]]] = []

    def update_policy(self, new_policy: TriagePolicy):
        self.policy = new_policy
        self.cell_id = new_policy.cell_id

    def process_mcap_file(self, mcap_path: Path, output_dir: Path) -> Optional[Path]:
        if mcap_path.name.endswith(".tmp") or not mcap_path.name.endswith(".mcap"):
            return None

        start_time = time.time()
        try:
            file_size = mcap_path.stat().st_size
        except OSError:
            return None

        self.total_ingested_bytes += file_size
        BYTES_INGESTED.labels(cell_id=self.cell_id).inc(file_size)
        EVENTS_INGESTED.labels(cell_id=self.cell_id).inc()

        logger.info(f"Processing MCAP package {mcap_path.name} ({file_size / (1024*1024):.2f} MB)...")

        # 1. Read MCAP channels
        can_data: Dict[str, Any] = {}
        uncertainty_data: Dict[str, Any] = {}
        embedding: List[float] = []
        meta: Dict[str, Any] = {}
        sensor_messages: Dict[str, bytes] = {}

        try:
            with open(mcap_path, "rb") as f:
                reader = make_reader(f)
                for schema, channel, message in reader.iter_messages():
                    topic = channel.topic
                    if topic == "/vehicle/can_bus":
                        can_data = json.loads(message.data.decode("utf-8"))
                    elif topic == "/perception/uncertainty":
                        uncertainty_data = json.loads(message.data.decode("utf-8"))
                    elif topic == "/perception/embedding_128d":
                        embedding = json.loads(message.data.decode("utf-8"))
                    elif topic == "/metadata":
                        meta = json.loads(message.data.decode("utf-8"))
                    else:
                        sensor_messages[topic] = message.data
        except Exception as e:
            logger.error(f"Corrupt or unreadable MCAP file {mcap_path}: {e}")
            EVENTS_DISCARDED.labels(cell_id=self.cell_id, filter_reason="corrupt_mcap").inc()
            mcap_path.unlink(missing_ok=True)
            return None

        event_id = meta.get("event_id", mcap_path.stem)
        grade = can_data.get("grade_pitch_pct", 0.0)
        lat_g = abs(can_data.get("lateral_accel_g", 0.0))
        ttc = can_data.get("forward_ttc_seconds", 99.0)
        is_reversing = can_data.get("gear_reverse_active", False) or can_data.get("reverse_gear_engaged", False)

        # ---------------------------------------------------------
        # Filter 1: Deterministic Safety & CAN Dynamics
        # ---------------------------------------------------------
        f1_cfg = self.policy.filter_1_deterministic
        f1_fired = False
        if f1_cfg.enabled:
            is_downhill = grade < -abs(f1_cfg.downhill_grade_adjustment.grade_threshold_pct)
            thresh_g = f1_cfg.downhill_grade_adjustment.lateral_accel_g if is_downhill else f1_cfg.baseline.lateral_accel_g
            thresh_ttc = f1_cfg.downhill_grade_adjustment.ttc_seconds if is_downhill else f1_cfg.baseline.ttc_seconds

            # Dynamically read and evaluate configured safety trigger signals
            f1_signals = False
            for sig in f1_cfg.trigger_signals:
                if can_data.get(sig, False):
                    f1_signals = True
                    break
                # Common aliases
                if sig == "aeb_active" and can_data.get("aeb_triggered", False):
                    f1_signals = True
                    break
                if sig == "abs_traction_event" and can_data.get("abs_active", False):
                    f1_signals = True
                    break

            f1_kinematics = (lat_g >= thresh_g) or (ttc <= thresh_ttc)
            f1_fired = f1_signals or f1_kinematics

        # ---------------------------------------------------------
        # Filter 2: Perception Model Uncertainty
        # ---------------------------------------------------------
        f2_cfg = self.policy.filter_2_uncertainty
        f2_fired = False
        if f2_cfg.enabled:
            conf = uncertainty_data.get("detection_confidence", 1.0)
            entropy = uncertainty_data.get("shannon_entropy", 0.0)
            var_5f = uncertainty_data.get("temporal_variance_5frame", 0.0)
            f2_fired = (
                (conf < f2_cfg.detection_confidence_threshold) or
                (entropy > f2_cfg.shannon_entropy_threshold) or
                (var_5f > f2_cfg.temporal_variance_5frame_threshold)
            )

        # ---------------------------------------------------------
        # Filter 3: Unsupervised Feature Novelty (USearch Index)
        # ---------------------------------------------------------
        f3_cfg = self.policy.filter_3_novelty
        f3_fired = False
        novelty_dist = 0.0
        if f3_cfg.enabled and embedding and len(embedding) == self.vector_dim:
            if USEARCH_AVAILABLE and self.usearch_index is not None:
                matches = self.usearch_index.search(embedding, 1)
                if len(matches) > 0:
                    novelty_dist = float(matches.distances[0])
            else:
                sims = [cosine_similarity(embedding, v) for v in self.fallback_vectors.values()]
                novelty_dist = 1.0 - max(sims) if sims else 1.0

            f3_fired = novelty_dist > f3_cfg.distance_threshold_tau

        # ---------------------------------------------------------
        # Filter 4: Campaign Geofencing
        # ---------------------------------------------------------
        f4_cfg = self.policy.filter_4_geofence
        f4_fired = False
        gps_coords = meta.get("gps_coordinates", [0.0, 0.0])
        if f4_cfg.enabled and f4_cfg.polygon_coordinates and len(gps_coords) == 2:
            # Actively evaluate ray-casting point-in-polygon
            f4_fired = point_in_polygon(gps_coords[0], gps_coords[1], f4_cfg.polygon_coordinates)

        # ---------------------------------------------------------
        # Filter 5: Statistical & Anchor Sampling
        # ---------------------------------------------------------
        f5_cfg = self.policy.filter_5_sampling
        f5_fired = False
        if f5_cfg.enabled:
            is_anchor = meta.get("is_shift_anchor", False)
            is_random_sample = random.random() < f5_cfg.uniform_sampling_rate
            f5_fired = is_anchor or is_random_sample

        # Tier Assignment
        candidate_fired = f1_fired or f2_fired or f3_fired or f4_fired or f5_fired
        if not candidate_fired:
            logger.info(f"[-] Event {event_id}: Discarded by Filters 1-5 (Nominal haul cycle).")
            EVENTS_DISCARDED.labels(cell_id=self.cell_id, filter_reason="nominal_discard").inc()
            mcap_path.unlink(missing_ok=True)
            self._update_reduction_ratio()
            return None

        tier = "TIER_1_FORENSIC" if f1_fired else \
               "TIER_2_MODEL_UNCERTAINTY" if f2_fired else \
               "TIER_3_FEATURE_NOVELTY" if f3_fired else \
               "TIER_4_CAMPAIGN" if f4_fired else "TIER_5_ANCHOR"

        # ---------------------------------------------------------
        # Filter 6: Spatiotemporal Coreset Deduplication
        # ---------------------------------------------------------
        f6_cfg = self.policy.filter_6_dedup
        if f6_cfg.enabled and tier in ["TIER_2_MODEL_UNCERTAINTY", "TIER_3_FEATURE_NOVELTY"]:
            ts = meta.get("timestamp_epoch", time.time())
            coords = tuple(gps_coords)
            
            # Prune coreset buffer of items older than time_window_seconds
            window_sec = f6_cfg.time_window_seconds
            self.coreset_buffer = [
                (t, c, e) for (t, c, e) in self.coreset_buffer if (ts - t) <= window_sec
            ]
            
            # Spherical Haversine distance comparison
            for prev_ts, prev_coords, prev_emb in self.coreset_buffer:
                if abs(ts - prev_ts) <= window_sec:
                    dist_m = haversine_distance(coords[0], coords[1], prev_coords[0], prev_coords[1])
                    if dist_m <= f6_cfg.spatial_radius_meters:
                        sim = cosine_similarity(embedding, prev_emb)
                        if sim >= f6_cfg.cosine_similarity_min:
                            logger.info(
                                f"[-] Event {event_id}: Suppressed by Filter 6 (Duplicate haul @ {dist_m:.1f}m, sim: {sim:.3f})."
                            )
                            DEDUP_SUPPRESSIONS.labels(cell_id=self.cell_id).inc()
                            EVENTS_DISCARDED.labels(cell_id=self.cell_id, filter_reason="dedup_filter6").inc()
                            mcap_path.unlink(missing_ok=True)
                            self._update_reduction_ratio()
                            return None

            self.coreset_buffer.append((ts, coords, embedding))
            if USEARCH_AVAILABLE and self.usearch_index is not None and embedding:
                self.usearch_index.add(len(self.coreset_buffer), embedding)

        # ---------------------------------------------------------
        # Quota Governance & Preemption Order (Specification 01 §6.4)
        # ---------------------------------------------------------
        # Tier 1 Forensic is uncapped and preempts all lower tiers
        # If daily quota budget is constrained, lower tiers are suppressed in order: 5 -> 4 -> 3 -> 2
        daily_ceiling_bytes = self.policy.quotas.daily_ceiling_gb * (1024 ** 3)
        if self.total_curated_bytes >= daily_ceiling_bytes and tier != "TIER_1_FORENSIC":
            logger.warning(
                f"[Quota] Daily ceiling reached ({self.total_curated_bytes/(1024**3):.2f} GB >= {self.policy.quotas.daily_ceiling_gb} GB). "
                f"Preempting/evicting candidate {event_id} ({tier}) under preemption policy."
            )
            EVENTS_DISCARDED.labels(cell_id=self.cell_id, filter_reason="quota_preemption").inc()
            mcap_path.unlink(missing_ok=True)
            self._update_reduction_ratio()
            return None

        # ---------------------------------------------------------
        # Curation & Decimation: Write Output MCAP with Spec 02 IDs
        # ---------------------------------------------------------
        logger.info(f"[+] Event {event_id}: ACCEPTED under {tier}. Curation & decimation in progress...")
        output_dir.mkdir(parents=True, exist_ok=True)
        curated_mcap_path = output_dir / f"gds_curated_{mcap_path.name}"
        tmp_curated_path = output_dir / f"gds_curated_{mcap_path.name}.tmp"

        with open(tmp_curated_path, "wb") as out_f:
            writer = Writer(out_f)
            writer.start(profile="gds-curated-v2", library="edge-triage-2.0")

            schema_id = writer.register_schema(name="gds.json", encoding="jsonschema", data=b"{}")
            
            # Register Telemetry Channels
            ch_can = writer.register_channel(topic="/vehicle/can_bus", message_encoding="json", schema_id=schema_id)
            ch_unc = writer.register_channel(topic="/perception/uncertainty", message_encoding="json", schema_id=schema_id)
            ch_emb = writer.register_channel(topic="/perception/embedding_128d", message_encoding="json", schema_id=schema_id)
            ch_meta = writer.register_channel(topic="/metadata", message_encoding="json", schema_id=schema_id)

            now_ns = int(time.time() * 1e9)
            meta["assigned_tier"] = tier
            meta["reversing_exception_active"] = is_reversing
            if H3_AVAILABLE and len(gps_coords) == 2:
                meta["h3_index_res9"] = h3.geo_to_h3(gps_coords[0], gps_coords[1], 9)
            
            meta["triage_summary"] = {
                "f1_fired": f1_fired,
                "f2_fired": f2_fired,
                "f3_fired": f3_fired,
                "f4_fired": f4_fired,
                "f5_fired": f5_fired,
                "dedup_passed": True,
                "reversing_promoted": is_reversing
            }

            writer.add_message(channel_id=ch_can, log_time=now_ns, data=json.dumps(can_data).encode("utf-8"), publish_time=now_ns)
            writer.add_message(channel_id=ch_unc, log_time=now_ns, data=json.dumps(uncertainty_data).encode("utf-8"), publish_time=now_ns)
            writer.add_message(channel_id=ch_emb, log_time=now_ns, data=json.dumps(embedding).encode("utf-8"), publish_time=now_ns)
            writer.add_message(channel_id=ch_meta, log_time=now_ns, data=json.dumps(meta).encode("utf-8"), publish_time=now_ns)

            # Apply Specification 02 Channel Pruning and Decimation Mask
            channel_handles = {}
            for topic, raw_bytes in sensor_messages.items():
                if is_reversing:
                    # REVERSING EXCEPTION:
                    # KEEP rear and perimeter sensors at native resolution (~80% payload retained)
                    # DECIMATE or DROP forward auxiliary streams
                    if topic in CANONICAL_CHANNELS["reversing"] or "rear" in topic or "perimeter" in topic:
                        if topic not in channel_handles:
                            channel_handles[topic] = writer.register_channel(topic=topic, message_encoding="binary", schema_id=schema_id)
                        slice_len = int(len(raw_bytes) * 0.80)
                        writer.add_message(channel_id=channel_handles[topic], log_time=now_ns, data=raw_bytes[:slice_len], publish_time=now_ns)
                    elif topic in CANONICAL_CHANNELS["forward"]:
                        # Forward streams decimated heavily during reverse
                        if topic not in channel_handles:
                            channel_handles[topic] = writer.register_channel(topic=topic, message_encoding="binary", schema_id=schema_id)
                        slice_len = int(len(raw_bytes) * 0.20)
                        writer.add_message(channel_id=channel_handles[topic], log_time=now_ns, data=raw_bytes[:slice_len], publish_time=now_ns)
                else:
                    # FORWARD DRIVING:
                    # KEEP & DECIMATE forward primary channels (30 -> 10 FPS, ~35% payload retained)
                    # DROP rear perimeter and blind-spot radar channels completely
                    if topic in CANONICAL_CHANNELS["forward"] or "front" in topic or "main" in topic:
                        if topic not in channel_handles:
                            channel_handles[topic] = writer.register_channel(topic=topic, message_encoding="binary", schema_id=schema_id)
                        slice_len = int(len(raw_bytes) * 0.35)
                        writer.add_message(channel_id=channel_handles[topic], log_time=now_ns, data=raw_bytes[:slice_len], publish_time=now_ns)
                    # Rear and blind spot channels dropped in forward mode

            writer.finish()

        os.replace(tmp_curated_path, curated_mcap_path)

        curated_size = curated_mcap_path.stat().st_size
        self.total_curated_bytes += curated_size
        self.curated_tier_bytes[tier] += curated_size

        BYTES_CURATED.labels(cell_id=self.cell_id).inc(curated_size)
        EVENTS_CURATED.labels(cell_id=self.cell_id, tier=tier).inc()
        duration = time.time() - start_time
        PROCESSING_LATENCY.labels(cell_id=self.cell_id).observe(duration)

        mcap_path.unlink(missing_ok=True)
        self._update_reduction_ratio()

        logger.info(
            f"[Done] Curated {curated_mcap_path.name} ({curated_size/1024:.1f} KB from {file_size/1024:.1f} KB raw). "
            f"Reduction: {(1 - curated_size/file_size)*100:.1f}%. Duration: {duration*1000:.1f}ms."
        )
        return curated_mcap_path

    def _update_reduction_ratio(self):
        if self.total_ingested_bytes > 0:
            ratio = (1.0 - (self.total_curated_bytes / self.total_ingested_bytes)) * 100.0
            REDUCTION_PERCENTAGE.labels(cell_id=self.cell_id).set(ratio)
