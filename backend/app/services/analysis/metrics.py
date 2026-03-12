"""
LLM Observability Metrics v1.0
Tracks LLM calls, latency, token usage, and success rates
"""

import time
import json
from dataclasses import dataclass, field, asdict
from typing import Optional, Dict, List
from datetime import datetime
from collections import deque
from threading import Lock

from app.utils.logger import get_logger

logger = get_logger("LLMMetrics")


@dataclass
class LLMCallMetric:
    """Single LLM call metric record"""
    timestamp: str
    model: str
    prompt_type: str
    username: str
    tweet_count: int
    latency_ms: float
    success: bool
    validated: bool
    error: Optional[str] = None
    prompt_tokens: int = 0
    completion_tokens: int = 0
    confidence_score: float = 0.0


class LLMMetricsCollector:
    """
    Collects and aggregates LLM call metrics for observability.
    Thread-safe singleton pattern.
    """

    _instance = None
    _lock = Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._metrics: deque = deque(maxlen=1000)  # Keep last 1000 calls
        self._lock = Lock()
        self._initialized = True

    def record_call(
        self,
        model: str,
        prompt_type: str,
        username: str,
        tweet_count: int,
        latency_ms: float,
        success: bool,
        validated: bool,
        error: Optional[str] = None,
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
        confidence_score: float = 0.0
    ) -> LLMCallMetric:
        """Record a single LLM call metric"""
        metric = LLMCallMetric(
            timestamp=datetime.utcnow().isoformat(),
            model=model,
            prompt_type=prompt_type,
            username=username,
            tweet_count=tweet_count,
            latency_ms=latency_ms,
            success=success,
            validated=validated,
            error=error,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            confidence_score=confidence_score
        )

        with self._lock:
            self._metrics.append(metric)

        # Log metric
        status = "SUCCESS" if success else "FAILED"
        validation = "VALID" if validated else "INVALID"
        logger.info(
            f"[LLM] {status} | {model} | {prompt_type} | @{username} | "
            f"{tweet_count} tweets | {latency_ms:.0f}ms | {validation} | "
            f"confidence={confidence_score:.2f}"
        )

        return metric

    def get_recent_metrics(self, limit: int = 100) -> List[Dict]:
        """Get recent metrics as list of dicts"""
        with self._lock:
            recent = list(self._metrics)[-limit:]
        return [asdict(m) for m in recent]

    def get_aggregate_stats(self) -> Dict:
        """Calculate aggregate statistics"""
        with self._lock:
            metrics = list(self._metrics)

        if not metrics:
            return {
                "total_calls": 0,
                "success_rate": 0.0,
                "validation_rate": 0.0,
                "avg_latency_ms": 0.0,
                "avg_confidence": 0.0,
                "p95_latency_ms": 0.0,
                "total_tokens": 0,
                "by_model": {},
                "by_prompt_type": {}
            }

        total = len(metrics)
        successes = sum(1 for m in metrics if m.success)
        validated = sum(1 for m in metrics if m.validated)
        latencies = [m.latency_ms for m in metrics]
        confidences = [m.confidence_score for m in metrics if m.confidence_score > 0]

        # Sort for percentile calculation
        latencies_sorted = sorted(latencies)
        p95_index = int(len(latencies_sorted) * 0.95)

        # Group by model
        by_model = {}
        for m in metrics:
            if m.model not in by_model:
                by_model[m.model] = {"calls": 0, "successes": 0, "total_latency": 0}
            by_model[m.model]["calls"] += 1
            by_model[m.model]["successes"] += 1 if m.success else 0
            by_model[m.model]["total_latency"] += m.latency_ms

        for model_stats in by_model.values():
            model_stats["success_rate"] = model_stats["successes"] / model_stats["calls"]
            model_stats["avg_latency"] = model_stats["total_latency"] / model_stats["calls"]

        # Group by prompt type
        by_prompt = {}
        for m in metrics:
            if m.prompt_type not in by_prompt:
                by_prompt[m.prompt_type] = {"calls": 0, "successes": 0}
            by_prompt[m.prompt_type]["calls"] += 1
            by_prompt[m.prompt_type]["successes"] += 1 if m.success else 0

        for prompt_stats in by_prompt.values():
            prompt_stats["success_rate"] = prompt_stats["successes"] / prompt_stats["calls"]

        return {
            "total_calls": total,
            "success_rate": successes / total,
            "validation_rate": validated / total,
            "avg_latency_ms": sum(latencies) / total,
            "avg_confidence": sum(confidences) / len(confidences) if confidences else 0,
            "p95_latency_ms": latencies_sorted[p95_index] if latencies_sorted else 0,
            "total_tokens": sum(m.prompt_tokens + m.completion_tokens for m in metrics),
            "by_model": by_model,
            "by_prompt_type": by_prompt
        }

    def clear(self):
        """Clear all metrics (for testing)"""
        with self._lock:
            self._metrics.clear()


# Singleton instance
metrics_collector = LLMMetricsCollector()


class LLMCallTimer:
    """Context manager for timing LLM calls"""

    def __init__(
        self,
        model: str,
        prompt_type: str,
        username: str,
        tweet_count: int
    ):
        self.model = model
        self.prompt_type = prompt_type
        self.username = username
        self.tweet_count = tweet_count
        self.start_time: float = 0
        self.latency_ms: float = 0

    def __enter__(self):
        self.start_time = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.latency_ms = (time.perf_counter() - self.start_time) * 1000

    def record_success(
        self,
        validated: bool,
        confidence_score: float = 0.0,
        prompt_tokens: int = 0,
        completion_tokens: int = 0
    ):
        """Record successful call"""
        metrics_collector.record_call(
            model=self.model,
            prompt_type=self.prompt_type,
            username=self.username,
            tweet_count=self.tweet_count,
            latency_ms=self.latency_ms,
            success=True,
            validated=validated,
            confidence_score=confidence_score,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens
        )

    def record_failure(self, error: str):
        """Record failed call"""
        metrics_collector.record_call(
            model=self.model,
            prompt_type=self.prompt_type,
            username=self.username,
            tweet_count=self.tweet_count,
            latency_ms=self.latency_ms,
            success=False,
            validated=False,
            error=error
        )
