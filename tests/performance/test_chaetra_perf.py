"""
Performance tests for CHAETRA system.
Tests memory usage, response times, and concurrent processing capabilities.
"""

import pytest
import asyncio
import time
import psutil
import os
from datetime import datetime
from typing import List, Dict, Any
from statistics import mean, median, stdev

from app.chaetra.brain import CHAETRABrain
from app.chaetra.interfaces import Evidence
from app.core.config import get_settings

settings = get_settings()

# Performance test configurations
CONCURRENT_REQUESTS = 10
REQUEST_BATCHES = 5
WARMUP_REQUESTS = 3
PERFORMANCE_THRESHOLD_MS = 1000  # 1 second max response time
MEMORY_THRESHOLD_MB = 512  # 512MB max memory usage

@pytest.fixture
async def perf_brain():
    """Create CHAETRA brain instance for performance testing"""
    brain = CHAETRABrain()
    await brain.initialize()
    yield brain
    await brain.shutdown()

@pytest.fixture
def sample_market_data():
    """Generate sample market data for testing"""
    return {
        "symbol": "TEST",
        "timestamp": datetime.utcnow().isoformat(),
        "data": {
            "price": 100.0,
            "volume": 1000000,
            "indicators": {
                "rsi": 50,
                "macd": {"value": 0.5, "signal": 0.3}
            }
        }
    }

class PerformanceMetrics:
    """Class to track and analyze performance metrics"""
    
    def __init__(self):
        self.response_times: List[float] = []
        self.memory_usage: List[float] = []
        self.error_count: int = 0
        self.success_count: int = 0
    
    def add_response_time(self, time_ms: float):
        """Add response time measurement"""
        self.response_times.append(time_ms)
    
    def add_memory_usage(self, memory_mb: float):
        """Add memory usage measurement"""
        self.memory_usage.append(memory_mb)
    
    def add_result(self, success: bool):
        """Add request result"""
        if success:
            self.success_count += 1
        else:
            self.error_count += 1
    
    def get_stats(self) -> Dict[str, Any]:
        """Calculate performance statistics"""
        if not self.response_times:
            return {}
        
        return {
            "response_time": {
                "min_ms": min(self.response_times),
                "max_ms": max(self.response_times),
                "mean_ms": mean(self.response_times),
                "median_ms": median(self.response_times),
                "stddev_ms": stdev(self.response_times) if len(self.response_times) > 1 else 0,
                "p95_ms": sorted(self.response_times)[int(len(self.response_times) * 0.95)]
            },
            "memory_usage": {
                "min_mb": min(self.memory_usage),
                "max_mb": max(self.memory_usage),
                "mean_mb": mean(self.memory_usage)
            },
            "requests": {
                "total": self.success_count + self.error_count,
                "success": self.success_count,
                "errors": self.error_count,
                "success_rate": self.success_count / (self.success_count + self.error_count)
            }
        }

def get_memory_usage() -> float:
    """Get current process memory usage in MB"""
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / 1024 / 1024

async def measure_performance(
    func: callable,
    *args,
    metrics: PerformanceMetrics
) -> None:
    """Measure performance of a function call"""
    start_time = time.perf_counter()
    try:
        await func(*args)
        metrics.add_result(True)
    except Exception as e:
        print(f"Error during performance test: {e}")
        metrics.add_result(False)
    
    end_time = time.perf_counter()
    metrics.add_response_time((end_time - start_time) * 1000)  # Convert to ms
    metrics.add_memory_usage(get_memory_usage())

@pytest.mark.performance
@pytest.mark.asyncio
async def test_concurrent_processing(perf_brain, sample_market_data):
    """Test concurrent processing performance"""
    metrics = PerformanceMetrics()
    
    # Warmup
    print("\nPerforming warmup requests...")
    for _ in range(WARMUP_REQUESTS):
        await measure_performance(
            perf_brain.process_input,
            "market_data",
            sample_market_data,
            metrics
        )
    
    # Reset metrics after warmup
    metrics = PerformanceMetrics()
    
    print(f"\nRunning {REQUEST_BATCHES} batches of {CONCURRENT_REQUESTS} concurrent requests...")
    for batch in range(REQUEST_BATCHES):
        print(f"Batch {batch + 1}/{REQUEST_BATCHES}")
        
        tasks = [
            measure_performance(
                perf_brain.process_input,
                "market_data",
                sample_market_data,
                metrics
            )
            for _ in range(CONCURRENT_REQUESTS)
        ]
        
        await asyncio.gather(*tasks)
    
    stats = metrics.get_stats()
    print("\nPerformance Test Results:")
    print(f"Total Requests: {stats['requests']['total']}")
    print(f"Success Rate: {stats['requests']['success_rate']:.2%}")
    print(f"Mean Response Time: {stats['response_time']['mean_ms']:.2f}ms")
    print(f"95th Percentile Response Time: {stats['response_time']['p95_ms']:.2f}ms")
    print(f"Max Memory Usage: {stats['memory_usage']['max_mb']:.2f}MB")
    
    # Assert performance requirements
    assert stats["response_time"]["p95_ms"] < PERFORMANCE_THRESHOLD_MS
    assert stats["memory_usage"]["max_mb"] < MEMORY_THRESHOLD_MB
    assert stats["requests"]["success_rate"] > 0.95

@pytest.mark.performance
@pytest.mark.asyncio
async def test_memory_leaks(perf_brain, sample_market_data):
    """Test for memory leaks during extended operation"""
    initial_memory = get_memory_usage()
    metrics = PerformanceMetrics()
    
    print("\nTesting for memory leaks...")
    for _ in range(100):  # Extended test
        await measure_performance(
            perf_brain.process_input,
            "market_data",
            sample_market_data,
            metrics
        )
    
    # Force garbage collection
    import gc
    gc.collect()
    
    final_memory = get_memory_usage()
    memory_growth = final_memory - initial_memory
    
    print(f"\nMemory Usage:")
    print(f"Initial: {initial_memory:.2f}MB")
    print(f"Final: {final_memory:.2f}MB")
    print(f"Growth: {memory_growth:.2f}MB")
    
    # Assert reasonable memory growth
    assert memory_growth < 50  # Max 50MB growth

@pytest.mark.performance
@pytest.mark.asyncio
async def test_component_performance(perf_brain, sample_market_data):
    """Test performance of individual components"""
    metrics = {
        "memory": PerformanceMetrics(),
        "learning": PerformanceMetrics(),
        "reasoning": PerformanceMetrics(),
        "opinion": PerformanceMetrics(),
        "llm": PerformanceMetrics()
    }
    
    print("\nTesting component performance...")
    
    # Test memory operations
    for _ in range(10):
        await measure_performance(
            perf_brain.memory.store_short_term,
            "test_key",
            sample_market_data,
            metrics["memory"]
        )
    
    # Test learning operations
    evidence = [
        Evidence(
            source="test",
            content=sample_market_data,
            confidence=0.8,
            timestamp=datetime.utcnow()
        )
    ]
    for _ in range(10):
        await measure_performance(
            perf_brain.learning.learn,
            "PATTERN",
            sample_market_data,
            evidence,
            metrics["learning"]
        )
    
    # Test reasoning operations
    for _ in range(10):
        await measure_performance(
            perf_brain.reasoning.analyze,
            {"type": "technical"},
            {"data": sample_market_data},
            metrics["reasoning"]
        )
    
    # Test opinion formation
    for _ in range(10):
        await measure_performance(
            perf_brain.opinion.form_opinion,
            "test_topic",
            evidence,
            metrics["opinion"]
        )
    
    # Test LLM processing
    for _ in range(10):
        await measure_performance(
            perf_brain.llm.process_text,
            "Analyze market data",
            metrics["llm"]
        )
    
    print("\nComponent Performance Results:")
    for component, metric in metrics.items():
        stats = metric.get_stats()
        print(f"\n{component.title()} Component:")
        print(f"Mean Response Time: {stats['response_time']['mean_ms']:.2f}ms")
        print(f"Success Rate: {stats['requests']['success_rate']:.2%}")
    
    # Assert component performance
    for metric in metrics.values():
        stats = metric.get_stats()
        assert stats["response_time"]["mean_ms"] < PERFORMANCE_THRESHOLD_MS
        assert stats["requests"]["success_rate"] > 0.9

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
