import os
import yaml
import logging
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

logger = logging.getLogger("TriageConfig")

class Filter1Baseline(BaseModel):
    lateral_accel_g: float = 0.30
    ttc_seconds: float = 3.0

class Filter1Downhill(BaseModel):
    grade_threshold_pct: float = 8.0
    lateral_accel_g: float = 0.20
    ttc_seconds: float = 4.5

class Filter1Config(BaseModel):
    enabled: bool = True
    baseline: Filter1Baseline = Field(default_factory=Filter1Baseline)
    downhill_grade_adjustment: Filter1Downhill = Field(default_factory=Filter1Downhill)
    trigger_signals: List[str] = Field(
        default_factory=lambda: [
            "aeb_active",
            "e_stop_active",
            "operator_takeover",
            "abs_traction_event",
            "rollover_warning"
        ]
    )

class Filter2Config(BaseModel):
    enabled: bool = True
    detection_confidence_threshold: float = 0.65
    shannon_entropy_threshold: float = 0.70
    temporal_variance_5frame_threshold: float = 0.04

class Filter3Config(BaseModel):
    enabled: bool = True
    vector_dim: int = 128
    similarity_metric: str = "cosine"
    distance_threshold_tau: float = 0.72
    local_index_path: str = "/var/cache/usearch/baseline_128d.usearch"
    daily_vector_sync_mb: float = 50.0

class Filter4Config(BaseModel):
    enabled: bool = True
    active_campaign_id: str = "blast_zone_regrade_2026_q4"
    polygon_coordinates: List[List[float]] = Field(default_factory=list)

class Filter5Config(BaseModel):
    enabled: bool = True
    uniform_sampling_rate: float = 0.001
    mandatory_shift_anchor: bool = True

class Filter6Config(BaseModel):
    enabled: bool = True
    time_window_seconds: int = 7200
    spatial_radius_meters: float = 100.0
    cosine_similarity_min: float = 0.90
    target_suppression_rate: float = 0.70

class QuotaConfig(BaseModel):
    daily_ceiling_gb: float = 20.0
    nominal_target_gb: float = 7.0
    preemption_order: List[str] = Field(default_factory=list)
    tier_limits_gb: Dict[str, float] = Field(default_factory=dict)

class TriagePolicy(BaseModel):
    version: str = "2.0"
    cell_id: str = "pilbara-cell-04"
    quotas: QuotaConfig = Field(default_factory=QuotaConfig)
    filter_1_deterministic: Filter1Config = Field(default_factory=Filter1Config)
    filter_2_uncertainty: Filter2Config = Field(default_factory=Filter2Config)
    filter_3_novelty: Filter3Config = Field(default_factory=Filter3Config)
    filter_4_geofence: Filter4Config = Field(default_factory=Filter4Config)
    filter_5_sampling: Filter5Config = Field(default_factory=Filter5Config)
    filter_6_dedup: Filter6Config = Field(default_factory=Filter6Config)
    decimation: Dict[str, Any] = Field(default_factory=dict)

class ConfigWatcher:
    def __init__(self, config_path: str):
        self.config_path = config_path
        self._last_mtime: float = 0.0
        self.policy: TriagePolicy = TriagePolicy()
        self.reload()

    def reload(self) -> bool:
        if not os.path.exists(self.config_path):
            logger.warning(f"Config path {self.config_path} does not exist. Using defaults.")
            return False
        try:
            mtime = os.path.getmtime(self.config_path)
            if mtime != self._last_mtime:
                with open(self.config_path, "r") as f:
                    data = yaml.safe_load(f)
                self.policy = TriagePolicy(**data)
                self._last_mtime = mtime
                logger.info(f"Loaded triage policy v{self.policy.version} for {self.policy.cell_id}")
                return True
        except Exception as e:
            logger.error(f"Error loading config from {self.config_path}: {e}")
        return False
