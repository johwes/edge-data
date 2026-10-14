import os
import sys
import time
import signal
import logging
from pathlib import Path

from .config import ConfigWatcher
from .pipeline import TriagePipeline
from .metrics import init_metrics

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s"
)
logger = logging.getLogger("TriageMain")

running = True

def handle_signal(sig, frame):
    global running
    logger.info(f"Received signal {sig}. Initiating graceful shutdown...")
    running = False

signal.signal(signal.SIGINT, handle_signal)
signal.signal(signal.SIGTERM, handle_signal)

def main():
    config_path = os.getenv("CONFIG_PATH", "/etc/triage-config/triage_policy.yaml")
    raw_ingest_path = Path(os.getenv("RAW_INGEST_PATH", "/mnt/raw_ingest"))
    gds_curated_path = Path(os.getenv("GDS_CURATED_PATH", "/mnt/gds_curated"))
    metrics_port = int(os.getenv("METRICS_PORT", "8080"))

    logger.info("======================================================")
    logger.info("   Starting Enterprise Edge Triage Engine v2.0        ")
    logger.info(f"   Config Path:      {config_path}")
    logger.info(f"   Raw Ingest:       {raw_ingest_path}")
    logger.info(f"   GDS Curated:      {gds_curated_path}")
    logger.info(f"   Metrics Port:     {metrics_port}")
    logger.info("======================================================")

    # 1. Start Prometheus metrics endpoint
    try:
        init_metrics(metrics_port)
        logger.info(f"Prometheus metrics server active at http://0.0.0.0:{metrics_port}/metrics")
    except Exception as e:
        logger.error(f"Failed to start metrics server on port {metrics_port}: {e}")

    # 2. Initialize Config and Pipeline
    watcher = ConfigWatcher(config_path)
    pipeline = TriagePipeline(watcher.policy)

    raw_ingest_path.mkdir(parents=True, exist_ok=True)
    gds_curated_path.mkdir(parents=True, exist_ok=True)

    health_file = Path("/tmp/healthy")
    health_file.touch()

    logger.info("Monitoring edge shared storage for incoming MCAP telemetry...")

    while running:
        try:
            # Check for policy updates
            if watcher.reload():
                pipeline.update_policy(watcher.policy)

            # Touch health file for liveness/readiness
            health_file.touch()

            # Find incoming MCAP files
            mcap_files = sorted(
                list(raw_ingest_path.glob("**/*.mcap")),
                key=lambda p: p.stat().st_mtime
            )

            for mcap_file in mcap_files:
                if not running:
                    break
                pipeline.process_mcap_file(mcap_file, gds_curated_path)

            time.sleep(1.0)
        except Exception as e:
            logger.error(f"Unexpected error in main triage loop: {e}", exc_info=True)
            time.sleep(2.0)

    logger.info("Edge Triage Engine stopped cleanly.")

if __name__ == "__main__":
    main()
