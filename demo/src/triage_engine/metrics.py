import os
import re
import json
import logging
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn
import threading
from typing import Optional, Any
from urllib.parse import unquote

from prometheus_client import Counter, Gauge, Histogram, generate_latest, CONTENT_TYPE_LATEST

logger = logging.getLogger("TriageMetrics")

# Ingestion and Curation Counters
EVENTS_INGESTED = Counter(
    "edge_triage_events_ingested_total",
    "Total number of raw vehicle events ingested from edge ring buffer",
    ["cell_id"]
)

EVENTS_CURATED = Counter(
    "edge_triage_events_curated_total",
    "Total number of events accepted into Golden Data Set",
    ["cell_id", "tier"]
)

EVENTS_DISCARDED = Counter(
    "edge_triage_events_discarded_total",
    "Total number of nominal or redundant events discarded at edge",
    ["cell_id", "filter_reason"]
)

DEDUP_SUPPRESSIONS = Counter(
    "edge_triage_dedup_suppressions_total",
    "Total number of redundant events suppressed by Filter 6 spatiotemporal coreset deduplication",
    ["cell_id"]
)

# Byte Volume Metrics
BYTES_INGESTED = Counter(
    "edge_triage_bytes_ingested_total",
    "Total raw bytes ingested into edge buffer",
    ["cell_id"]
)

BYTES_CURATED = Counter(
    "edge_triage_bytes_curated_total",
    "Total curated bytes preserved for cloud synchronization",
    ["cell_id"]
)

REDUCTION_PERCENTAGE = Gauge(
    "edge_triage_reduction_percentage",
    "Current data volume reduction percentage (1 - curated/ingested)",
    ["cell_id"]
)

# Latency
PROCESSING_LATENCY = Histogram(
    "edge_triage_processing_duration_seconds",
    "Time spent evaluating filters and decimating an MCAP package",
    ["cell_id"],
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0]
)

class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True

    def handle_error(self, request, client_address):
        import sys
        _, exc, _ = sys.exc_info()
        if isinstance(exc, (ConnectionResetError, BrokenPipeError, TimeoutError, OSError)):
            return
        super().handle_error(request, client_address)

class UnifiedMetricsHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    curated_dir: Path = Path("/mnt/gds_curated")
    pipeline_ref: Optional[Any] = None

    def log_message(self, format, *args):
        # Suppress verbose access logging for polling endpoints
        pass

    def end_headers(self):
        self.send_header("Connection", "close")
        self.close_connection = True
        super().end_headers()

    def handle_one_request(self):
        try:
            super().handle_one_request()
        except (ConnectionResetError, BrokenPipeError, TimeoutError, OSError):
            self.close_connection = True

    def do_HEAD(self):
        url_path = self.path.split("?")[0]
        if url_path == "/metrics":
            data = generate_latest()
            self.send_response(200)
            self.send_header("Content-Type", CONTENT_TYPE_LATEST)
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
        elif url_path in ["/api/status", "/api/shift-brief"]:
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
        elif url_path.startswith("/videos/"):
            video_name = unquote(url_path[len("/videos/"):])
            clean_name = os.path.basename(video_name)
            target_file = self.curated_dir / clean_name
            self.serve_video_range(target_file, head_only=True)
        elif url_path in ["/", "/index.html"]:
            self.serve_dashboard(head_only=True)
        else:
            self.send_error(404, "Not Found")

    def do_GET(self):
        url_path = self.path.split("?")[0]

        if url_path == "/metrics":
            data = generate_latest()
            self.send_response(200)
            self.send_header("Content-Type", CONTENT_TYPE_LATEST)
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            try:
                self.wfile.write(data)
            except (BrokenPipeError, ConnectionResetError):
                pass

        elif url_path == "/api/status":
            self.handle_api_status(force_live_brief=False)

        elif url_path == "/api/shift-brief":
            self.handle_api_status(force_live_brief=True, brief_only=True)

        elif url_path.startswith("/videos/"):
            video_name = unquote(url_path[len("/videos/"):])
            clean_name = os.path.basename(video_name)
            target_file = self.curated_dir / clean_name
            self.serve_video_range(target_file)

        elif url_path in ["/", "/index.html"]:
            self.serve_dashboard()

        else:
            self.send_error(404, "Not Found")

    def handle_api_status(self, force_live_brief: bool = False, brief_only: bool = False):
        from .pipeline import generate_shift_handover_brief

        # Scan curated dir for video files and MCAPs
        videos = []
        curated_files = []
        vlm_by_event = {}
        try:
            if self.curated_dir.exists():
                for p in sorted(self.curated_dir.glob("*.mp4"), key=lambda x: x.stat().st_mtime, reverse=True):
                    vlm_data = None
                    vlm_file = p.with_suffix(".vlm.json")
                    if vlm_file.exists():
                        try:
                            vlm_data = json.loads(vlm_file.read_text(encoding="utf-8"))
                            if isinstance(vlm_data, dict) and vlm_data.get("event_id"):
                                vlm_by_event[vlm_data["event_id"]] = vlm_data
                        except Exception:
                            vlm_data = None
                    videos.append({
                        "name": p.name,
                        "size": p.stat().st_size,
                        "url": f"/videos/{p.name}",
                        "vlm": vlm_data,
                    })
                for p in sorted(self.curated_dir.glob("*.mcap"), key=lambda x: x.stat().st_mtime, reverse=True):
                    curated_files.append({
                        "name": p.name,
                        "size": p.stat().st_size
                    })
        except Exception as err:
            logger.debug(f"Error scanning curated dir for status: {err}")

        # Extract live values from pipeline reference if available
        ingested_bytes = getattr(self.pipeline_ref, "total_ingested_bytes", 0) if self.pipeline_ref else 0
        curated_bytes = getattr(self.pipeline_ref, "total_curated_bytes", 0) if self.pipeline_ref else 0
        reduction_pct = 0.0
        if ingested_bytes > 0:
            reduction_pct = (1.0 - (curated_bytes / ingested_bytes)) * 100.0

        # Also fall back to disk if pipeline hasn't processed in this instance
        if curated_bytes == 0 and curated_files:
            curated_bytes = sum(f["size"] for f in curated_files) + sum(v["size"] for v in videos)

        events_ingested = 0
        events_curated = 0
        events_discarded = 0
        dedup_suppressions = 0

        # Try to read prometheus metric values
        try:
            for metric in [EVENTS_INGESTED, DEDUP_SUPPRESSIONS]:
                for sample in metric.collect()[0].samples:
                    if sample.name == "edge_triage_events_ingested_total":
                        events_ingested = int(sample.value)
                    elif sample.name == "edge_triage_dedup_suppressions_total":
                        dedup_suppressions = int(sample.value)
            for sample in EVENTS_CURATED.collect()[0].samples:
                if sample.name == "edge_triage_events_curated_total":
                    events_curated += int(sample.value)
            for sample in EVENTS_DISCARDED.collect()[0].samples:
                if sample.name == "edge_triage_events_discarded_total":
                    events_discarded += int(sample.value)
            for sample in REDUCTION_PERCENTAGE.collect()[0].samples:
                if sample.name == "edge_triage_reduction_percentage" and sample.value > 0:
                    reduction_pct = sample.value
        except Exception:
            pass

        if events_curated == 0 and curated_files:
            events_curated = len(curated_files)

        maint_alerts = list(getattr(self.pipeline_ref, "maintenance_alerts", []) or []) if self.pipeline_ref else []
        road_advisories = []
        raw_advisories = list(getattr(self.pipeline_ref, "road_advisories", []) or []) if self.pipeline_ref else []
        for adv in raw_advisories:
            enriched = dict(adv)
            vlm_match = vlm_by_event.get(enriched.get("event_id", ""))
            if vlm_match and vlm_match.get("root_cause"):
                enriched["vlm_context"] = vlm_match.get("root_cause")
            road_advisories.append(enriched)

        payload = {
            "cell_id": getattr(self.pipeline_ref, "cell_id", "pilbara-cell-04") if self.pipeline_ref else "pilbara-cell-04",
            "bytes_ingested": ingested_bytes,
            "bytes_curated": curated_bytes,
            "reduction_pct": reduction_pct,
            "events_ingested": events_ingested or len(curated_files) + events_discarded,
            "events_curated": events_curated,
            "events_discarded": events_discarded,
            "dedup_suppressions": dedup_suppressions,
            "videos": videos,
            "curated_files": curated_files[:25],
            "maintenance_alerts": maint_alerts,
            "road_advisories": road_advisories,
        }
        shift_brief = generate_shift_handover_brief(payload, force_live=force_live_brief)
        payload["shift_brief"] = shift_brief

        out_obj = shift_brief if brief_only else payload
        resp_bytes = json.dumps(out_obj).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(resp_bytes)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(resp_bytes)

    def serve_dashboard(self, head_only: bool = False):
        html_path = Path(__file__).parent / "dashboard.html"
        if not html_path.exists():
            body = b"<h1>Edge Data Triage Dashboard</h1><p><a href='/metrics'>/metrics</a></p>"
        else:
            with open(html_path, "rb") as f:
                body = f.read()

        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        if not head_only:
            self.wfile.write(body)

    def serve_video_range(self, file_path: Path, head_only: bool = False):
        if not file_path.exists() or not file_path.is_file():
            self.send_error(404, "Video clip not found")
            return

        file_size = file_path.stat().st_size
        range_header = self.headers.get("Range")

        if range_header:
            match = re.match(r"bytes=(\d+)-(\d*)", range_header)
            if match:
                start = int(match.group(1))
                end = int(match.group(2)) if match.group(2) else file_size - 1
                if start >= file_size or end >= file_size or start > end:
                    self.send_response(416)
                    self.send_header("Content-Range", f"bytes */{file_size}")
                    self.send_header("Access-Control-Allow-Origin", "*")
                    self.end_headers()
                    return
                length = end - start + 1
                self.send_response(206)
                self.send_header("Content-Type", "video/mp4")
                self.send_header("Content-Range", f"bytes {start}-{end}/{file_size}")
                self.send_header("Content-Length", str(length))
                self.send_header("Accept-Ranges", "bytes")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.send_header("Cache-Control", "no-cache")
                self.end_headers()
                if not head_only:
                    try:
                        with open(file_path, "rb") as f:
                            f.seek(start)
                            remaining = length
                            while remaining > 0:
                                chunk = f.read(min(remaining, 65536))
                                if not chunk:
                                    break
                                self.wfile.write(chunk)
                                remaining -= len(chunk)
                    except (BrokenPipeError, ConnectionResetError):
                        pass
                return

        self.send_response(200)
        self.send_header("Content-Type", "video/mp4")
        self.send_header("Content-Length", str(file_size))
        self.send_header("Accept-Ranges", "bytes")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        if not head_only:
            try:
                with open(file_path, "rb") as f:
                    while True:
                        chunk = f.read(65536)
                        if not chunk:
                            break
                        self.wfile.write(chunk)
            except (BrokenPipeError, ConnectionResetError):
                pass

def init_metrics(port: int = 8080, curated_dir: Optional[Path] = None, pipeline: Optional[Any] = None):
    """Starts the threaded HTTP server serving /metrics, /api/status, /videos/*, and /."""
    if curated_dir:
        UnifiedMetricsHandler.curated_dir = curated_dir
    if pipeline:
        UnifiedMetricsHandler.pipeline_ref = pipeline

    server = ThreadedHTTPServer(("0.0.0.0", port), UnifiedMetricsHandler)
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()
    logger.info(f"Unified Web & Metrics server running on http://0.0.0.0:{port}/ (serving /metrics and /)")
