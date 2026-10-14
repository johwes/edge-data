import os
import time
import json
import random
import logging
from pathlib import Path
from mcap.writer import Writer

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [Simulator] %(message)s"
)
logger = logging.getLogger("Simulator")

def generate_benchmark_events(output_dir: Path, total_events: int = 100, payload_kb_per_event: int = 1024):
    output_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"Generating {total_events} realistic MCAP telemetry packages into {output_dir}...")
    logger.info(f"Simulating ~{payload_kb_per_event} KB sensor payload per raw package...")

    now = time.time()
    events = []

    # 1. Filter 1 Trigger: AEB Near-miss on loaded downhill haul (-9% grade)
    events.append({
        "event_id": "EVT_F1_AEB_DOWNHILL_001",
        "timestamp_epoch": now - 300,
        "truck_id": "HT_402_400T",
        "can_data": {
            "lateral_accel_g": 0.34,
            "forward_ttc_seconds": 2.6,
            "grade_pitch_pct": -9.0,
            "aeb_triggered": True,
            "gear_reverse_active": False
        },
        "uncertainty": {
            "detection_confidence": 0.52,
            "shannon_entropy": 0.78,
            "temporal_variance_5frame": 0.045
        },
        "embedding": [random.uniform(-0.1, 0.1) for _ in range(128)],
        "gps": [-22.3182, 119.8251],
        "is_shift_anchor": False,
        "inside_campaign_geofence": False
    })

    # 2. Filter 2 Trigger: Heavy dust cloud with unclassified obstacle detection
    events.append({
        "event_id": "EVT_F2_DUST_UNCERTAINTY_002",
        "timestamp_epoch": now - 240,
        "truck_id": "HT_405_400T",
        "can_data": {
            "lateral_accel_g": 0.12,
            "forward_ttc_seconds": 7.5,
            "grade_pitch_pct": -2.0,
            "aeb_triggered": False,
            "gear_reverse_active": False
        },
        "uncertainty": {
            "detection_confidence": 0.48,
            "shannon_entropy": 0.82,
            "temporal_variance_5frame": 0.065
        },
        "embedding": [random.uniform(-0.1, 0.1) for _ in range(128)],
        "gps": [-22.3190, 119.8260],
        "is_shift_anchor": False,
        "inside_campaign_geofence": False
    })

    # 3. Filter 3 Trigger: Novel road condition / spillage (USearch novelty > 0.72)
    novel_vector = [0.6] * 128
    events.append({
        "event_id": "EVT_F3_NOVEL_HAUL_ROAD_003",
        "timestamp_epoch": now - 180,
        "truck_id": "HT_408_400T",
        "can_data": {
            "lateral_accel_g": 0.08,
            "forward_ttc_seconds": 9.0,
            "grade_pitch_pct": 0.5,
            "aeb_triggered": False,
            "gear_reverse_active": False
        },
        "uncertainty": {
            "detection_confidence": 0.85,
            "shannon_entropy": 0.25,
            "temporal_variance_5frame": 0.010
        },
        "embedding": novel_vector,
        "gps": [-22.3201, 119.8275],
        "is_shift_anchor": False,
        "inside_campaign_geofence": False
    })

    # 4 & 5. Filter 6 Pair: Two trucks encountering the same obstacle 3 minutes and 15m apart
    common_vector = [0.35] * 128
    events.append({
        "event_id": "EVT_F6_INTERSECTION_DUPLICATE_004A",
        "timestamp_epoch": now - 120,
        "truck_id": "HT_410_400T",
        "can_data": {
            "lateral_accel_g": 0.05,
            "forward_ttc_seconds": 12.0,
            "grade_pitch_pct": 0.0,
            "aeb_triggered": False,
            "gear_reverse_active": False
        },
        "uncertainty": {
            "detection_confidence": 0.60,
            "shannon_entropy": 0.72,
            "temporal_variance_5frame": 0.042
        },
        "embedding": common_vector,
        "gps": [-22.3210, 119.8280],
        "is_shift_anchor": False,
        "inside_campaign_geofence": False
    })

    events.append({
        "event_id": "EVT_F6_INTERSECTION_DUPLICATE_004B",
        "timestamp_epoch": now - 60,
        "truck_id": "HT_412_400T",
        "can_data": {
            "lateral_accel_g": 0.05,
            "forward_ttc_seconds": 11.5,
            "grade_pitch_pct": 0.0,
            "aeb_triggered": False,
            "gear_reverse_active": False
        },
        "uncertainty": {
            "detection_confidence": 0.61,
            "shannon_entropy": 0.71,
            "temporal_variance_5frame": 0.041
        },
        "embedding": common_vector,
        "gps": [-22.3211, 119.8281], # ~15m away
        "is_shift_anchor": False,
        "inside_campaign_geofence": False
    })

    # 6. Filter 5 Trigger: Mandatory Shift Anchor
    events.append({
        "event_id": "EVT_F5_MANDATORY_SHIFT_ANCHOR_005",
        "timestamp_epoch": now - 30,
        "truck_id": "HT_401_400T",
        "can_data": {
            "lateral_accel_g": 0.02,
            "forward_ttc_seconds": 20.0,
            "grade_pitch_pct": 1.0,
            "aeb_triggered": False,
            "gear_reverse_active": False
        },
        "uncertainty": {
            "detection_confidence": 0.98,
            "shannon_entropy": 0.05,
            "temporal_variance_5frame": 0.002
        },
        "embedding": [random.uniform(-0.02, 0.02) for _ in range(128)],
        "gps": [-22.3160, 119.8220],
        "is_shift_anchor": True,
        "inside_campaign_geofence": False
    })

    # 7 to 100: Nominal Haul Segments
    for i in range(7, total_events + 1):
        events.append({
            "event_id": f"EVT_NOMINAL_HAUL_{i:03d}",
            "timestamp_epoch": now - (total_events - i) * 10,
            "truck_id": f"HT_{400 + (i % 15):03d}_400T",
            "can_data": {
                "lateral_accel_g": random.uniform(0.01, 0.15),
                "forward_ttc_seconds": random.uniform(6.0, 25.0),
                "grade_pitch_pct": random.uniform(-4.0, 4.0),
                "aeb_triggered": False,
                "gear_reverse_active": False
            },
            "uncertainty": {
                "detection_confidence": random.uniform(0.85, 0.99),
                "shannon_entropy": random.uniform(0.05, 0.40),
                "temporal_variance_5frame": random.uniform(0.001, 0.020)
            },
            "embedding": [random.uniform(-0.05, 0.05) for _ in range(128)],
            "gps": [-22.3150 + random.uniform(0, 0.01), 119.8210 + random.uniform(0, 0.01)],
            "is_shift_anchor": False,
            "inside_campaign_geofence": False
        })

    # Generate dummy binary sensor stream (~1024 KB)
    dummy_sensor_bytes = os.urandom(payload_kb_per_event * 1024)

    for idx, evt in enumerate(events, 1):
        mcap_file_path = output_dir / f"{evt['event_id']}.mcap"
        with open(mcap_file_path, "wb") as f:
            writer = Writer(f)
            writer.start(profile="raw-ingest-v2", library="fleet-simulator-2.0")

            schema_id = writer.register_schema(name="sensor_data.json", encoding="jsonschema", data=b"{}")
            ch_can = writer.register_channel(topic="/vehicle/can_bus", message_encoding="json", schema_id=schema_id)
            ch_unc = writer.register_channel(topic="/perception/uncertainty", message_encoding="json", schema_id=schema_id)
            ch_emb = writer.register_channel(topic="/perception/embedding_128d", message_encoding="json", schema_id=schema_id)
            ch_meta = writer.register_channel(topic="/metadata", message_encoding="json", schema_id=schema_id)
            ch_raw = writer.register_channel(topic="/sensors/camera_compressed", message_encoding="binary", schema_id=schema_id)

            now_ns = int(evt["timestamp_epoch"] * 1e9)
            meta = {
                "event_id": evt["event_id"],
                "truck_id": evt["truck_id"],
                "timestamp_epoch": evt["timestamp_epoch"],
                "gps_coordinates": evt["gps"],
                "is_shift_anchor": evt["is_shift_anchor"],
                "inside_campaign_geofence": evt["inside_campaign_geofence"]
            }

            writer.add_message(channel_id=ch_can, log_time=now_ns, data=json.dumps(evt["can_data"]).encode("utf-8"), publish_time=now_ns)
            writer.add_message(channel_id=ch_unc, log_time=now_ns, data=json.dumps(evt["uncertainty"]).encode("utf-8"), publish_time=now_ns)
            writer.add_message(channel_id=ch_emb, log_time=now_ns, data=json.dumps(evt["embedding"]).encode("utf-8"), publish_time=now_ns)
            writer.add_message(channel_id=ch_meta, log_time=now_ns, data=json.dumps(meta).encode("utf-8"), publish_time=now_ns)
            writer.add_message(channel_id=ch_raw, log_time=now_ns, data=dummy_sensor_bytes, publish_time=now_ns)
            writer.finish()

        if idx % 20 == 0 or idx == len(events):
            logger.info(f"Generated {idx}/{len(events)} MCAP telemetry files...")

    logger.info(f"Finished generating all {len(events)} MCAP files in {output_dir}.")

def main():
    raw_path = Path(os.getenv("RAW_INGEST_PATH", "/mnt/raw_ingest")) / "incoming"
    total = int(os.getenv("SIMULATOR_EVENT_COUNT", "100"))
    payload_kb = int(os.getenv("SIMULATOR_PAYLOAD_KB", "1024"))
    generate_benchmark_events(raw_path, total, payload_kb)

if __name__ == "__main__":
    main()
