from prometheus_client import Counter, Gauge, Histogram, start_http_server

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

def init_metrics(port: int = 8080):
    start_http_server(port)
