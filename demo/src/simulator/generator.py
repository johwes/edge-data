import os
import time
import json
import random
import shutil
import logging
import subprocess
from pathlib import Path
from typing import Optional
from mcap.writer import Writer

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [Simulator] %(message)s"
)
logger = logging.getLogger("Simulator")

# Seed random for deterministic, repeatable test runs
random.seed(42)

CANONICAL_SPEC02_SENSOR_TOPICS = [
    "/sensors/cam_front_center_8mp",
    "/sensors/cam_front_telephoto_8mp",
    "/sensors/lidar_128_beam_main",
    "/sensors/radar_front_long_range",
    "/sensors/cam_rear_perimeter_4mp",
    "/sensors/lidar_perimeter_solid_state",
    "/sensors/radar_perimeter_rear",
    "/sensors/radar_blind_spot_side_left",
    "/sensors/radar_blind_spot_side_right",
]

def find_ffmpeg_executable() -> Optional[str]:
    """Finds FFmpeg executable via PATH or imageio-ffmpeg bundled binary."""
    exe = shutil.which("ffmpeg")
    if exe:
        return exe
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return None

def generate_synthetic_video_stream(output_path: Path, duration_sec: int = 30, asset_name: Optional[str] = None) -> bool:
    """
    Provisions a rolling 30 FPS camera video stream into output_path.
    Uses a pre-packaged realistic camera asset from simulator/assets/ when available,
    falling back to FFmpeg synthetic testsrc generation.
    """
    tmp_path = output_path.with_suffix(".mp4.tmp")
    if asset_name:
        asset_path = Path(__file__).parent / "assets" / asset_name
        if asset_path.exists():
            try:
                shutil.copyfile(asset_path, tmp_path)
                os.replace(tmp_path, output_path)
                logger.info(
                    f"Loaded realistic {duration_sec}s camera video buffer: {output_path.name} "
                    f"({output_path.stat().st_size / 1024:.1f} KB @ 30 FPS, H.264)."
                )
                return True
            except Exception as e:
                tmp_path.unlink(missing_ok=True)
                logger.warning(f"Failed to copy bundled video asset {asset_path.name}: {e}; falling back to synthetic stream.")

    ffmpeg_exe = find_ffmpeg_executable()
    if not ffmpeg_exe:
        logger.warning("FFmpeg executable not available; skipping raw video stream generation.")
        return False

    # Try browser-native H.264 (libx264 / libopenh264) with faststart first, fallback to mpeg4
    for codec, extra_opts in [
        ("libx264", ["-preset", "ultrafast", "-tune", "zerolatency"]),
        ("libopenh264", ["-b:v", "800k"]),
        ("mpeg4", ["-q:v", "5"])
    ]:
        cmd = [
            ffmpeg_exe, "-y",
            "-f", "lavfi",
            "-i", f"testsrc=duration={duration_sec}:size=640x360:rate=30",
            "-c:v", codec,
            *extra_opts,
            "-pix_fmt", "yuv420p",
            "-movflags", "+faststart",
            "-f", "mp4",
            str(tmp_path)
        ]
        try:
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
            os.replace(tmp_path, output_path)
            logger.info(
                f"Generated rolling {duration_sec}s camera video buffer: {output_path.name} "
                f"({output_path.stat().st_size / 1024:.1f} KB @ 30 FPS, codec={codec})."
            )
            return True
        except Exception as e:
            tmp_path.unlink(missing_ok=True)
            if codec in ("libx264", "libopenh264"):
                logger.debug(f"{codec} unavailable ({e}); retrying with fallback codec.")
                continue
            logger.error(f"Failed to generate synthetic video stream via ffmpeg: {e}")
            return False
    return False

def generate_benchmark_events(output_dir: Path, total_events: int = 100, payload_kb_per_event: int = 1024):
    output_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"Generating {total_events} realistic MCAP telemetry packages into {output_dir}...")
    logger.info(f"Distributing ~{payload_kb_per_event} KB across {len(CANONICAL_SPEC02_SENSOR_TOPICS)} canonical sensor streams...")

    now = time.time()
    events = []

    # 1. Filter 1 Trigger: AEB Near-miss on loaded downhill haul (-9% grade) with rolling video buffer
    vid_f1 = "EVT_F1_AEB_DOWNHILL_001_raw_camera_30s_30fps.mp4"
    events.append({
        "event_id": "EVT_F1_AEB_DOWNHILL_001",
        "timestamp_epoch": now - 600,
        "truck_id": "HT_402_400T",
        "can_data": {
            "lateral_accel_g": 0.34,
            "forward_ttc_seconds": 2.6,
            "grade_pitch_pct": -9.0,
            "aeb_active": True,
            "aeb_triggered": True,
            "e_stop_active": False,
            "operator_takeover": False,
            "abs_traction_event": False,
            "rollover_warning": False,
            "gear_reverse_active": False
        },
        "uncertainty": {
            "detection_confidence": 0.52,
            "shannon_entropy": 0.78,
            "temporal_variance_5frame": 0.045
        },
        "embedding": [1.0 + random.uniform(-0.05, 0.05) for _ in range(128)],
        "gps": [-22.3300, 119.8100],
        "is_shift_anchor": False,
        "raw_video_filename": vid_f1,
        "video_trigger_second": 15.0 # Event occurs at second 15 of 30
    })

    # 2. Filter 2 Trigger: Heavy dust cloud with unclassified obstacle detection
    events.append({
        "event_id": "EVT_F2_DUST_UNCERTAINTY_002",
        "timestamp_epoch": now - 500,
        "truck_id": "HT_405_400T",
        "can_data": {
            "lateral_accel_g": 0.12,
            "forward_ttc_seconds": 7.5,
            "grade_pitch_pct": -2.0,
            "aeb_active": False,
            "e_stop_active": False,
            "operator_takeover": False,
            "abs_traction_event": False,
            "rollover_warning": False,
            "gear_reverse_active": False
        },
        "uncertainty": {
            "detection_confidence": 0.48,
            "shannon_entropy": 0.82,
            "temporal_variance_5frame": 0.065
        },
        "embedding": [1.0 + random.uniform(-0.05, 0.05) for _ in range(128)],
        "gps": [-22.3310, 119.8110],
        "is_shift_anchor": False
    })

    # 3. Filter 3 Trigger: Novel road condition / spillage (USearch cosine distance ~0.79 > 0.72)
    novel_vector = [1.0 if i % 2 == 0 else -0.65 for i in range(128)]
    events.append({
        "event_id": "EVT_F3_NOVEL_HAUL_ROAD_003",
        "timestamp_epoch": now - 400,
        "truck_id": "HT_408_400T",
        "can_data": {
            "lateral_accel_g": 0.08,
            "forward_ttc_seconds": 9.0,
            "grade_pitch_pct": 0.5,
            "aeb_active": False,
            "e_stop_active": False,
            "operator_takeover": False,
            "abs_traction_event": False,
            "rollover_warning": False,
            "gear_reverse_active": False
        },
        "uncertainty": {
            "detection_confidence": 0.85,
            "shannon_entropy": 0.25,
            "temporal_variance_5frame": 0.010
        },
        "embedding": novel_vector,
        "gps": [-22.3320, 119.8120],
        "is_shift_anchor": False
    })

    # 4 & 5. Filter 6 Pair: Two trucks encountering the same obstacle 3 minutes and 15m apart
    common_vector = [1.0 + (0.05 if i % 3 == 0 else -0.02) for i in range(128)]
    events.append({
        "event_id": "EVT_F6_INTERSECTION_DUPLICATE_004A",
        "timestamp_epoch": now - 300,
        "truck_id": "HT_410_400T",
        "can_data": {
            "lateral_accel_g": 0.05,
            "forward_ttc_seconds": 12.0,
            "grade_pitch_pct": 0.0,
            "aeb_active": False,
            "e_stop_active": False,
            "operator_takeover": False,
            "abs_traction_event": False,
            "rollover_warning": False,
            "gear_reverse_active": False
        },
        "uncertainty": {
            "detection_confidence": 0.60,
            "shannon_entropy": 0.72,
            "temporal_variance_5frame": 0.042
        },
        "embedding": common_vector,
        "gps": [-22.3330, 119.8130],
        "is_shift_anchor": False
    })

    events.append({
        "event_id": "EVT_F6_INTERSECTION_DUPLICATE_004B",
        "timestamp_epoch": now - 120, # 180s later (< 7200s window)
        "truck_id": "HT_412_400T",
        "can_data": {
            "lateral_accel_g": 0.05,
            "forward_ttc_seconds": 11.5,
            "grade_pitch_pct": 0.0,
            "aeb_active": False,
            "e_stop_active": False,
            "operator_takeover": False,
            "abs_traction_event": False,
            "rollover_warning": False,
            "gear_reverse_active": False
        },
        "uncertainty": {
            "detection_confidence": 0.61,
            "shannon_entropy": 0.71,
            "temporal_variance_5frame": 0.041
        },
        "embedding": common_vector,
        "gps": [-22.3331, 119.8131], # ~15m away (< 100m radius)
        "is_shift_anchor": False
    })

    # 6. Reversing & Dump Hopper Safety Exception (Flips channel mask to KEEP rear) with rolling rear camera
    vid_rev = "EVT_REVERSING_HOPPER_MANEUVER_006_raw_rear_camera_30s_30fps.mp4"
    events.append({
        "event_id": "EVT_REVERSING_HOPPER_MANEUVER_006",
        "timestamp_epoch": now - 90,
        "truck_id": "HT_415_400T",
        "can_data": {
            "lateral_accel_g": 0.24,
            "forward_ttc_seconds": 4.0,
            "grade_pitch_pct": -8.5,
            "aeb_active": False,
            "e_stop_active": False,
            "operator_takeover": True,
            "abs_traction_event": False,
            "rollover_warning": False,
            "gear_reverse_active": True # Reversing exception active!
        },
        "uncertainty": {
            "detection_confidence": 0.70,
            "shannon_entropy": 0.50,
            "temporal_variance_5frame": 0.020
        },
        "embedding": [1.0 + random.uniform(-0.05, 0.05) for _ in range(128)],
        "gps": [-22.3340, 119.8140],
        "is_shift_anchor": False,
        "raw_video_filename": vid_rev,
        "video_trigger_second": 15.0
    })

    # 7. Filter 4 Trigger: Campaign Geofence Entry (Tested via GPS point-in-polygon)
    events.append({
        "event_id": "EVT_F4_CAMPAIGN_GEOFENCE_007",
        "timestamp_epoch": now - 60,
        "truck_id": "HT_418_400T",
        "can_data": {
            "lateral_accel_g": 0.05,
            "forward_ttc_seconds": 15.0,
            "grade_pitch_pct": 1.0,
            "aeb_active": False,
            "e_stop_active": False,
            "operator_takeover": False,
            "abs_traction_event": False,
            "rollover_warning": False,
            "gear_reverse_active": False
        },
        "uncertainty": {
            "detection_confidence": 0.90,
            "shannon_entropy": 0.15,
            "temporal_variance_5frame": 0.005
        },
        "embedding": [1.0 + random.uniform(-0.05, 0.05) for _ in range(128)],
        "gps": [-22.3180, 119.8250], # Inside the polygon
        "is_shift_anchor": False
    })

    # 8. Filter 1 Trigger: Emergency Stop & Rollover Warning
    events.append({
        "event_id": "EVT_F1_ESTOP_ROLLOVER_008",
        "timestamp_epoch": now - 45,
        "truck_id": "HT_420_400T",
        "can_data": {
            "lateral_accel_g": 0.18,
            "forward_ttc_seconds": 8.0,
            "grade_pitch_pct": -1.0,
            "aeb_active": False,
            "e_stop_active": True,
            "operator_takeover": False,
            "abs_traction_event": True,
            "rollover_warning": True,
            "gear_reverse_active": False
        },
        "uncertainty": {
            "detection_confidence": 0.88,
            "shannon_entropy": 0.20,
            "temporal_variance_5frame": 0.010
        },
        "embedding": [1.0 + random.uniform(-0.05, 0.05) for _ in range(128)],
        "gps": [-22.3350, 119.8150],
        "is_shift_anchor": False
    })

    # 9. Filter 5 Trigger: Mandatory Shift Anchor
    events.append({
        "event_id": "EVT_F5_MANDATORY_SHIFT_ANCHOR_009",
        "timestamp_epoch": now - 30,
        "truck_id": "HT_401_400T",
        "can_data": {
            "lateral_accel_g": 0.02,
            "forward_ttc_seconds": 20.0,
            "grade_pitch_pct": 1.0,
            "aeb_active": False,
            "e_stop_active": False,
            "operator_takeover": False,
            "abs_traction_event": False,
            "rollover_warning": False,
            "gear_reverse_active": False
        },
        "uncertainty": {
            "detection_confidence": 0.98,
            "shannon_entropy": 0.05,
            "temporal_variance_5frame": 0.002
        },
        "embedding": [1.0 + random.uniform(-0.02, 0.02) for _ in range(128)],
        "gps": [-22.3360, 119.8160],
        "is_shift_anchor": True
    })

    # 10 to 100: Nominal Haul Segments
    for i in range(10, total_events + 1):
        events.append({
            "event_id": f"EVT_NOMINAL_HAUL_{i:03d}",
            "timestamp_epoch": now - (total_events - i) * 10,
            "truck_id": f"HT_{400 + (i % 15):03d}_400T",
            "can_data": {
                "lateral_accel_g": random.uniform(0.01, 0.15),
                "forward_ttc_seconds": random.uniform(6.0, 25.0),
                "grade_pitch_pct": random.uniform(-4.0, 4.0),
                "aeb_active": False,
                "e_stop_active": False,
                "operator_takeover": False,
                "abs_traction_event": False,
                "rollover_warning": False,
                "gear_reverse_active": False
            },
            "uncertainty": {
                "detection_confidence": random.uniform(0.85, 0.99),
                "shannon_entropy": random.uniform(0.05, 0.40),
                "temporal_variance_5frame": random.uniform(0.001, 0.020)
            },
            "embedding": [1.0 + random.uniform(-0.05, 0.05) for _ in range(128)],
            "gps": [-22.3400 + random.uniform(0, 0.01), 119.8000 + random.uniform(0, 0.01)],
            "is_shift_anchor": False
        })

    # Provision 30s camera video buffers for the incident events
    generate_synthetic_video_stream(
        output_dir / vid_f1,
        duration_sec=30,
        asset_name="EVT_F1_AEB_DOWNHILL_001_raw_30s.mp4"
    )
    generate_synthetic_video_stream(
        output_dir / vid_rev,
        duration_sec=30,
        asset_name="EVT_REVERSING_HOPPER_MANEUVER_006_raw_30s.mp4"
    )

    # Divide the total payload evenly among the canonical sensor channels
    bytes_per_channel = int((payload_kb_per_event * 1024) / len(CANONICAL_SPEC02_SENSOR_TOPICS))
    sensor_dummy_payloads = {
        topic: os.urandom(bytes_per_channel)
        for topic in CANONICAL_SPEC02_SENSOR_TOPICS
    }

    for idx, evt in enumerate(events, 1):
        mcap_final_path = output_dir / f"{evt['event_id']}.mcap"
        mcap_tmp_path = output_dir / f"{evt['event_id']}.mcap.tmp"

        with open(mcap_tmp_path, "wb") as f:
            writer = Writer(f)
            writer.start(profile="raw-ingest-v2", library="fleet-simulator-2.0")

            schema_id = writer.register_schema(name="sensor_data.json", encoding="jsonschema", data=b"{}")
            
            # Register Telemetry Channels
            ch_can = writer.register_channel(topic="/vehicle/can_bus", message_encoding="json", schema_id=schema_id)
            ch_unc = writer.register_channel(topic="/perception/uncertainty", message_encoding="json", schema_id=schema_id)
            ch_emb = writer.register_channel(topic="/perception/embedding_128d", message_encoding="json", schema_id=schema_id)
            ch_meta = writer.register_channel(topic="/metadata", message_encoding="json", schema_id=schema_id)

            # Register Canonical Spec 02 Sensor Channels
            sensor_channels = {
                topic: writer.register_channel(topic=topic, message_encoding="binary", schema_id=schema_id)
                for topic in CANONICAL_SPEC02_SENSOR_TOPICS
            }

            now_ns = int(evt["timestamp_epoch"] * 1e9)
            meta = {
                "event_id": evt["event_id"],
                "truck_id": evt["truck_id"],
                "timestamp_epoch": evt["timestamp_epoch"],
                "gps_coordinates": evt["gps"],
                "is_shift_anchor": evt["is_shift_anchor"]
            }
            if "raw_video_filename" in evt:
                meta["raw_video_filename"] = evt["raw_video_filename"]
                meta["video_trigger_second"] = evt.get("video_trigger_second", 15.0)

            writer.add_message(channel_id=ch_can, log_time=now_ns, data=json.dumps(evt["can_data"]).encode("utf-8"), publish_time=now_ns)
            writer.add_message(channel_id=ch_unc, log_time=now_ns, data=json.dumps(evt["uncertainty"]).encode("utf-8"), publish_time=now_ns)
            writer.add_message(channel_id=ch_emb, log_time=now_ns, data=json.dumps(evt["embedding"]).encode("utf-8"), publish_time=now_ns)
            writer.add_message(channel_id=ch_meta, log_time=now_ns, data=json.dumps(meta).encode("utf-8"), publish_time=now_ns)

            # Write sensor payloads to each canonical channel
            for topic, channel_handle in sensor_channels.items():
                writer.add_message(channel_id=channel_handle, log_time=now_ns, data=sensor_dummy_payloads[topic], publish_time=now_ns)

            writer.finish()

        # Atomic rename prevents partial-write race conditions
        os.replace(mcap_tmp_path, mcap_final_path)

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
