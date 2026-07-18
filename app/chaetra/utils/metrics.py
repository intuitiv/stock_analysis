"""Metrics collection system for CHAETRA."""
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass
import time
from datetime import datetime
import asyncio
import threading
from collections import defaultdict
import statistics
from app.chaetra.utils.logging import CHAETRALogger

logger = CHAETRALogger("metrics")

@dataclass
class MetricValue:
    """A single metric value with metadata."""
    value: Union[int, float]
    timestamp: datetime
    labels: Dict[str, str]

class Metric:
    """Base class for metrics."""
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.values: List[MetricValue] = []
        
    def add(self, value: Union[int, float], labels: Optional[Dict[str, str]] = None):
        """Add a value to the metric."""
        self.values.append(MetricValue(
            value=value,
            timestamp=datetime.utcnow(),
            labels=labels or {}
        ))

class Counter(Metric):
    """Counter metric type."""
    
    def __init__(self, name: str, description: str):
        super().__init__(name, description)
        self._value = 0
        
    def increment(self, amount: int = 1, labels: Optional[Dict[str, str]] = None):
        """Increment counter by amount."""
        self._value += amount
        self.add(self._value, labels)
        
    def get_value(self) -> int:
        """Get current counter value."""
        return self._value

class Gauge(Metric):
    """Gauge metric type."""
    
    def __init__(self, name: str, description: str):
        super().__init__(name, description)
        self._value = 0.0
        
    def set(self, value: float, labels: Optional[Dict[str, str]] = None):
        """Set gauge value."""
        self._value = value
        self.add(value, labels)
        
    def get_value(self) -> float:
        """Get current gauge value."""
        return self._value

class Histogram(Metric):
    """Histogram metric type."""
    
    def __init__(
        self,
        name: str,
        description: str,
        buckets: Optional[List[float]] = None
    ):
        super().__init__(name, description)
        self.buckets = buckets or [0.1, 0.5, 1.0, 2.0, 5.0, 10.0, float('inf')]
        self._values: List[float] = []
        
    def observe(self, value: float, labels: Optional[Dict[str, str]] = None):
        """Add an observation."""
        self._values.append(value)
        self.add(value, labels)
        
    def get_stats(self) -> Dict[str, float]:
        """Get histogram statistics."""
        if not self._values:
            return {
                "count": 0,
                "sum": 0,
                "avg": 0,
                "median": 0,
                "stddev": 0
            }
            
        return {
            "count": len(self._values),
            "sum": sum(self._values),
            "avg": statistics.mean(self._values),
            "median": statistics.median(self._values),
            "stddev": statistics.stdev(self._values) if len(self._values) > 1 else 0
        }
        
    def get_buckets(self) -> Dict[float, int]:
        """Get bucket counts."""
        buckets = {b: 0 for b in self.buckets}
        for value in self._values:
            for bucket in self.buckets:
                if value <= bucket:
                    buckets[bucket] += 1
                    break
        return buckets

class MetricsCollector:
    """Collector for system metrics."""
    
    def __init__(self):
        self._metrics: Dict[str, Metric] = {}
        self._lock = threading.Lock()
        
    def register_metric(self, metric: Metric) -> None:
        """Register a new metric."""
        with self._lock:
            if metric.name in self._metrics:
                logger.warning(f"Metric {metric.name} already registered")
                return
            self._metrics[metric.name] = metric
            
    def get_metric(self, name: str) -> Optional[Metric]:
        """Get a registered metric."""
        return self._metrics.get(name)
        
    def get_all_metrics(self) -> Dict[str, Metric]:
        """Get all registered metrics."""
        return self._metrics.copy()

class SystemMetrics:
    """Pre-configured system metrics."""
    
    def __init__(self, collector: MetricsCollector):
        self.collector = collector
        self._setup_metrics()
        
    def _setup_metrics(self):
        """Setup default system metrics."""
        # Memory metrics
        self.memory_usage = Gauge(
            "memory_usage_bytes",
            "Memory usage in bytes"
        )
        
        # Processing metrics
        self.request_duration = Histogram(
            "request_duration_seconds",
            "Request processing duration in seconds"
        )
        
        self.request_count = Counter(
            "request_count_total",
            "Total number of requests processed"
        )
        
        self.error_count = Counter(
            "error_count_total",
            "Total number of errors encountered"
        )
        
        # Component metrics
        self.pattern_count = Counter(
            "pattern_count_total",
            "Total number of patterns detected"
        )
        
        self.opinion_confidence = Histogram(
            "opinion_confidence",
            "Distribution of opinion confidence scores"
        )
        
        # Cache metrics
        self.cache_hits = Counter(
            "cache_hits_total",
            "Total number of cache hits"
        )
        
        self.cache_misses = Counter(
            "cache_misses_total",
            "Total number of cache misses"
        )
        
        # Register all metrics
        for metric in [
            self.memory_usage,
            self.request_duration,
            self.request_count,
            self.error_count,
            self.pattern_count,
            self.opinion_confidence,
            self.cache_hits,
            self.cache_misses
        ]:
            self.collector.register_metric(metric)

class MetricsContext:
    """Context manager for timing operations."""
    
    def __init__(self, histogram: Histogram, labels: Optional[Dict[str, str]] = None):
        self.histogram = histogram
        self.labels = labels
        self.start_time = None
        
    async def __aenter__(self):
        """Enter async context."""
        self.start_time = time.time()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit async context."""
        duration = time.time() - self.start_time
        self.histogram.observe(duration, self.labels)

# Create global metrics collector and system metrics
metrics_collector = MetricsCollector()
system_metrics = SystemMetrics(metrics_collector)

def get_metrics_report() -> Dict[str, Any]:
    """Generate a metrics report."""
    report = {}
    
    for name, metric in metrics_collector.get_all_metrics().items():
        if isinstance(metric, Counter):
            report[name] = metric.get_value()
        elif isinstance(metric, Gauge):
            report[name] = metric.get_value()
        elif isinstance(metric, Histogram):
            report[name] = {
                "stats": metric.get_stats(),
                "buckets": metric.get_buckets()
            }
            
    return report
