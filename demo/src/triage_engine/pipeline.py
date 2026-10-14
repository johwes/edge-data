import os
import math
import time
import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple

try:
    from usearch.index import Index
    USEARCH_AVAILABLE = True
except ImportError:
    USEARCH_AVAILABLE = False

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

class TriagePipeline:
    def __init__(self, policy: TriagePolicy):
        self.policy = policy
        self.cell_id = policy.cell_id
        self.total_ingested_bytes = 0
        self.total_curated_bytes = 0
        
        # Initialize USearch CPU-accelerated index (128-D Cosine)
        self.vector_dim = policy.filter_3_novelty.vector_dim
        if USEARCH_AVAILABLE:
            logger.info("Initializing USearch SIMD-accelerated HNSW index on CPU (128-D, metric=cos)...")
            self.usearch_index = Index(ndim=self.vector_dim, metric="cos")
            # Populate with a synthetic nominal baseline centroid
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
        start_time = time.time()
        file_size = mcap_path.stat().st_size
        self.total_ingested_bytes += file_size
        BYTES_INGESTED.labels(cell_id=self.cell_id).inc(file_size)
        EVENTS_INGESTED.labels(cell_id=self.cell_id).inc()

        logger.info(f"Processing MCAP package {mcap_path.name} ({file_size / (1024*1024):.2f} MB)...")

        # 1. Read MCAP channels
        can_data: Dict[str, Any] = {}
        uncertainty_data: Dict[str, Any] = {}
        embedding: List[float] = []
        meta: Dict[str, Any] = {}
        payload_messages = []

        try:
            with open(mcap_path, "rb") as f:
                reader = make_reader(f)
                for schema, channel, message in reader.iter_messages():
                    if channel.topic == "/vehicle/can_bus":
                        can_data = json.loads(message.data.decode("utf-8"))
                    elif channel.topic == "/perception/uncertainty":
                        uncertainty_data = json.loads(message.data.decode("utf-8"))
                    elif channel.topic == "/perception/embedding_128d":
                        embedding = json.loads(message.data.decode("utf-8"))
                    elif channel.topic == "/metadata":
                        meta = json.loads(message.data.decode("utf-8"))
                    else:
                        # Non-telemetry channels (e.g. high-bandwidth camera streams)
                        payload_messages.append((schema, channel, message))
        except Exception as e:
            logger.error(f"Corrupt or unreadable MCAP file {mcap_path}: {e}")
            EVENTS_DISCARDED.labels(cell_id=self.cell_id, filter_reason="corrupt_mcap").inc()
            mcap_path.unlink(missing_ok=True)
            return None

        event_id = meta.get("event_id", mcap_path.stem)
        grade = can_data.get("grade_pitch_pct", 0.0)
        lat_g = abs(can_data.get("lateral_accel_g", 0.0))
        ttc = can_data.get("forward_ttc_seconds", 99.0)
        aeb = can_data.get("aeb_triggered", False)

        # ---------------------------------------------------------
        # Filter 1: Deterministic Safety & CAN Dynamics
        # ---------------------------------------------------------
        f1_cfg = self.policy.filter_1_deterministic
        is_downhill = grade < -abs(f1_cfg.downhill_grade_adjustment.grade_threshold_pct)
        thresh_g = f1_cfg.downhill_grade_adjustment.lateral_accel_g if is_downhill else f1_cfg.baseline.lateral_accel_g
        thresh_ttc = f1_cfg.downhill_grade_adjustment.ttc_seconds if is_downhill else f1_cfg.baseline.ttc_seconds

        f1_fired = aeb or (lat_g >= thresh_g) or (ttc <= thresh_ttc)

        # ---------------------------------------------------------
        # Filter 2: Perception Model Uncertainty
        # ---------------------------------------------------------
        f2_cfg = self.policy.filter_2_uncertainty
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
        novelty_dist = 0.0
        if embedding and len(embedding) == self.vector_dim:
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
        f4_fired = meta.get("inside_campaign_geofence", False)

        # ---------------------------------------------------------
        # Filter 5: Statistical & Anchor Sampling
        # ---------------------------------------------------------
        f5_fired = meta.get("is_shift_anchor", False)

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
        if tier in ["TIER_2_MODEL_UNCERTAINTY", "TIER_3_FEATURE_NOVELTY"]:
            ts = meta.get("timestamp_epoch", time.time())
            coords = tuple(meta.get("gps_coordinates", [0.0, 0.0]))
            
            # Check window (2 hours) and spatial radius (100 meters)
            for prev_ts, prev_coords, prev_emb in self.coreset_buffer[-50:]:
                if abs(ts - prev_ts) <= f3_cfg.vector_dim: # 7200s window
                    dist_m = math.sqrt(
                        (coords[0] - prev_coords[0])**2 + (coords[1] - prev_coords[1])**2
                    ) * 111000
                    if dist_m <= self.policy.filter_6_dedup.spatial_radius_meters:
                        sim = cosine_similarity(embedding, prev_emb)
                        if sim >= self.policy.filter_6_dedup.cosine_similarity_min:
                            logger.info(
                                f"[-] Event {event_id}: Suppressed by Filter 6 (Duplicate haul @ {dist_m:.1f}m, sim: {sim:.3f})."
                            )
                            DEDUP_SUPPRESSIONS.labels(cell_id=self.cell_id).inc()
                            EVENTS_DISCARDED.labels(cell_id=self.cell_id, filter_reason="dedup_filter6").inc()
                            mcap_path.unlink(missing_ok=True)
                            self._update_reduction_ratio()
                            return None

            # Add to coreset buffer and USearch index
            self.coreset_buffer.append((ts, coords, embedding))
            if USEARCH_AVAILABLE and self.usearch_index is not None and embedding:
                self.usearch_index.add(len(self.coreset_buffer), embedding)

        # ---------------------------------------------------------
        # Curation & Decimation: Write Output MCAP
        # ---------------------------------------------------------
        logger.info(f"[+] Event {event_id}: ACCEPTED under {tier}. Curation & decimation in progress...")
        output_dir.mkdir(parents=True, exist_ok=True)
        curated_mcap_path = output_dir / f"gds_curated_{mcap_path.name}"

        with open(curated_mcap_path, "wb") as out_f:
            writer = Writer(out_f)
            writer.start(profile="gds-curated-v2", library="edge-triage-2.0")

            # Register channels
            schema_id = writer.register_schema(name="gds.json", encoding="jsonschema", data=b"{}")
            ch_can = writer.register_channel(topic="/vehicle/can_bus", message_encoding="json", schema_id=schema_id)
            ch_unc = writer.register_channel(topic="/perception/uncertainty", message_encoding="json", schema_id=schema_id)
            ch_emb = writer.register_channel(topic="/perception/embedding_128d", message_encoding="json", schema_id=schema_id)
            ch_meta = writer.register_channel(topic="/metadata", message_encoding="json", schema_id=schema_id)

            now_ns = int(time.time() * 1e9)
            meta["assigned_tier"] = tier
            meta["triage_summary"] = {
                "f1_fired": f1_fired,
                "f2_fired": f2_fired,
                "f3_fired": f3_fired,
                "f4_fired": f4_fired,
                "f5_fired": f5_fired,
                "dedup_passed": True
            }

            writer.add_message(channel_id=ch_can, log_time=now_ns, data=json.dumps(can_data).encode("utf-8"), publish_time=now_ns)
            writer.add_message(channel_id=ch_unc, log_time=now_ns, data=json.dumps(uncertainty_data).encode("utf-8"), publish_time=now_ns)
            writer.add_message(channel_id=ch_emb, log_time=now_ns, data=json.dumps(embedding).encode("utf-8"), publish_time=now_ns)
            writer.add_message(channel_id=ch_meta, log_time=now_ns, data=json.dumps(meta).encode("utf-8"), publish_time=now_ns)
            writer.finish()

        curated_size = curated_mcap_path.stat().st_size
        self.total_curated_bytes += curated_size

        BYTES_CURATED.labels(cell_id=self.cell_id).inc(curated_size)
        EVENTS_CURATED.labels(cell_id=self.cell_id, tier=tier).inc()
        duration = time.time() - start_time
        PROCESSING_LATENCY.labels(cell_id=self.cell_id).observe(duration)

        mcap_path.unlink(missing_ok=True)
        self._update_reduction_ratio()

        logger.info(
            f"[Done] Curated {curated_mcap_path.name} ({curated_size/1024:.1f} KB). Duration: {duration*1000:.1f}ms."
        )
        return curated_mcap_path

    def _update_reduction_ratio(self):
        if self.total_ingested_bytes > 0:
            ratio = (1.0 - (self.total_curated_bytes / self.total_ingested_bytes)) * 100.0
            REDUCTION_PERCENTAGE.labels(cell_id=self.cell_id).set(ratio)
