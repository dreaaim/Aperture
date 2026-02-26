"""Performance optimization service for database queries, caching, and async processing.

This module provides performance optimization services including:
- Database query optimization and analysis
- Multi-level caching system
- Async task queue and batch processing
- Performance monitoring and bottleneck detection

Example:
    from app.services.performance_service import PerformanceService
    
    performance = PerformanceService()
    
    # Analyze query performance
    analysis = performance.analyze_query_performance("SELECT * FROM models")
    
    # Get from multi-level cache
    data = performance.get_multi_level("cache_key")
    
    # Submit async task
    task_id = performance.submit_task(process_data, data)
    
    # Get performance report
    report = performance.get_performance_report()
"""

import time
import asyncio
import threading
import hashlib
from typing import Dict, Any, List, Optional, Callable, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, Future
from collections import defaultdict
from app.utils.telemetry import get_tracer

tracer = get_tracer()


@dataclass
class QueryAnalysis:
    """Query analysis result."""
    query_hash: str
    execution_time: float
    rows_affected: int
    suggestions: List[str]
    index_recommendations: List[str]
    estimated_cost: str


@dataclass
class CacheEntry:
    """Cache entry with metadata."""
    key: str
    value: Any
    created_at: float
    ttl: int
    access_count: int
    last_accessed: float
    size_bytes: int


@dataclass
class AsyncTask:
    """Async task status."""
    task_id: str
    status: str
    created_at: float
    completed_at: Optional[float]
    result: Any
    error: Optional[str]


@dataclass
class PerformanceMetric:
    """Performance metric data point."""
    metric_name: str
    value: float
    timestamp: float
    tags: Dict[str, str]


@dataclass
class PerformanceReport:
    """Performance report summary."""
    report_time: float
    avg_response_time: float
    p95_response_time: float
    p99_response_time: float
    throughput: float
    error_rate: float
    cache_hit_rate: float
    active_connections: int
    bottlenecks: List[Dict[str, Any]]
    recommendations: List[str]


class PerformanceService:
    """Performance optimization service."""
    
    def __init__(self, max_workers: int = 10, cache_size: int = 10000):
        """Initialize the performance service.
        
        Args:
            max_workers: Maximum number of worker threads
            cache_size: Maximum number of cache entries
        """
        self._executor = ThreadPoolExecutor(max_workers=max_workers)
        self._tasks: Dict[str, AsyncTask] = {}
        self._task_counter = 0
        
        self._l1_cache: Dict[str, CacheEntry] = {}
        self._l1_cache_size = cache_size
        self._l1_cache_lock = threading.Lock()
        
        self._metrics: List[PerformanceMetric] = []
        self._metrics_lock = threading.Lock()
        self._max_metrics = 100000
        
        self._query_stats: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
            "count": 0,
            "total_time": 0.0,
            "max_time": 0.0,
            "min_time": float('inf')
        })
        
        self._response_times: List[float] = []
        self._response_times_lock = threading.Lock()
        self._max_response_times = 10000
        
        self._connection_pool_stats = {
            "active": 0,
            "idle": 0,
            "max_size": 100,
            "wait_count": 0
        }
        
        self._performance_thresholds = {
            "response_time_warning": 1.0,
            "response_time_critical": 3.0,
            "cache_hit_rate_warning": 0.5,
            "error_rate_warning": 0.05
        }
    
    def analyze_query_performance(self, query: str, execution_time: float = 0,
                                  rows_affected: int = 0) -> QueryAnalysis:
        """Analyze query performance and provide optimization suggestions.
        
        Args:
            query: The SQL query to analyze
            execution_time: Actual execution time if available
            rows_affected: Number of rows affected
            
        Returns:
            QueryAnalysis with suggestions
        """
        with tracer.start_as_current_span("analyze_query_performance", attributes={
            "query_hash": hashlib.md5(query.encode()).hexdigest()[:8],
            "execution_time": execution_time
        }) as span:
            query_hash = hashlib.md5(query.encode()).hexdigest()[:8]
            suggestions = []
            index_recommendations = []
            estimated_cost = "low"
            
            query_lower = query.lower()
            
            if "select *" in query_lower:
                suggestions.append("Avoid SELECT * - specify only needed columns")
            
            if "where" not in query_lower and "limit" not in query_lower:
                suggestions.append("Consider adding WHERE clause or LIMIT to reduce result set")
            
            if "order by" in query_lower and "limit" not in query_lower:
                suggestions.append("ORDER BY without LIMIT may be slow on large tables")
            
            if "like '%" in query_lower:
                suggestions.append("Leading wildcard LIKE queries cannot use indexes")
                index_recommendations.append("Consider full-text search for pattern matching")
            
            if "join" in query_lower:
                join_count = query_lower.count("join")
                if join_count > 3:
                    suggestions.append(f"Query has {join_count} JOINs - consider denormalization")
            
            if "subquery" in query_lower or query_lower.count("(select") > 0:
                suggestions.append("Consider rewriting subqueries as JOINs for better performance")
            
            if execution_time > 1.0:
                estimated_cost = "high"
                suggestions.append(f"Query took {execution_time:.2f}s - consider optimization")
            elif execution_time > 0.1:
                estimated_cost = "medium"
            
            if "id" in query_lower and "where" in query_lower:
                index_recommendations.append("Ensure id columns have indexes")
            
            if "created_at" in query_lower or "updated_at" in query_lower:
                index_recommendations.append("Consider indexes on timestamp columns")
            
            analysis = QueryAnalysis(
                query_hash=query_hash,
                execution_time=execution_time,
                rows_affected=rows_affected,
                suggestions=suggestions,
                index_recommendations=index_recommendations,
                estimated_cost=estimated_cost
            )
            
            self._record_query_stats(query_hash, execution_time)
            
            span.set_attribute("suggestions_count", len(suggestions))
            span.set_attribute("estimated_cost", estimated_cost)
            
            return analysis
    
    def _record_query_stats(self, query_hash: str, execution_time: float) -> None:
        """Record query statistics."""
        stats = self._query_stats[query_hash]
        stats["count"] += 1
        stats["total_time"] += execution_time
        stats["max_time"] = max(stats["max_time"], execution_time)
        stats["min_time"] = min(stats["min_time"], execution_time)
    
    def suggest_indexes(self, table_name: str, columns: List[str],
                       query_patterns: List[str]) -> List[str]:
        """Suggest indexes based on query patterns.
        
        Args:
            table_name: The table name
            columns: List of columns in the table
            query_patterns: Common query patterns
            
        Returns:
            List of index creation suggestions
        """
        with tracer.start_as_current_span("suggest_indexes", attributes={
            "table_name": table_name,
            "columns_count": len(columns)
        }) as span:
            suggestions = []
            
            for pattern in query_patterns:
                pattern_lower = pattern.lower()
                
                for col in columns:
                    if col.lower() in pattern_lower:
                        if "where" in pattern_lower:
                            suggestions.append(f"CREATE INDEX idx_{table_name}_{col} ON {table_name}({col})")
                        if "order by" in pattern_lower:
                            suggestions.append(f"CREATE INDEX idx_{table_name}_{col}_order ON {table_name}({col})")
            
            if "created_at" in columns:
                suggestions.append(f"CREATE INDEX idx_{table_name}_created_at ON {table_name}(created_at DESC)")
            
            if "updated_at" in columns:
                suggestions.append(f"CREATE INDEX idx_{table_name}_updated_at ON {table_name}(updated_at DESC)")
            
            suggestions = list(set(suggestions))
            
            span.set_attribute("suggestions_count", len(suggestions))
            
            return suggestions
    
    def get_multi_level(self, key: str) -> Tuple[Optional[Any], str]:
        """Get value from multi-level cache.
        
        Args:
            key: The cache key
            
        Returns:
            Tuple of (value, source) where source is 'L1', 'L2', or 'L3'
        """
        with tracer.start_as_current_span("get_multi_level", attributes={
            "key": key[:50]
        }) as span:
            with self._l1_cache_lock:
                if key in self._l1_cache:
                    entry = self._l1_cache[key]
                    if time.time() - entry.created_at < entry.ttl:
                        entry.access_count += 1
                        entry.last_accessed = time.time()
                        span.set_attribute("cache_hit", "L1")
                        return entry.value, "L1"
                    else:
                        del self._l1_cache[key]
            
            span.set_attribute("cache_hit", "miss")
            return None, "miss"
    
    def set_multi_level(self, key: str, value: Any, ttl: int = 3600,
                        levels: List[str] = None) -> None:
        """Set value in multi-level cache.
        
        Args:
            key: The cache key
            value: The value to cache
            ttl: Time to live in seconds
            levels: Cache levels to use (default: ['L1'])
        """
        with tracer.start_as_current_span("set_multi_level", attributes={
            "key": key[:50],
            "ttl": ttl
        }) as span:
            if levels is None:
                levels = ['L1']
            
            if 'L1' in levels:
                with self._l1_cache_lock:
                    if len(self._l1_cache) >= self._l1_cache_size:
                        self._evict_l1_cache()
                    
                    size_bytes = len(str(value).encode('utf-8'))
                    entry = CacheEntry(
                        key=key,
                        value=value,
                        created_at=time.time(),
                        ttl=ttl,
                        access_count=0,
                        last_accessed=time.time(),
                        size_bytes=size_bytes
                    )
                    self._l1_cache[key] = entry
            
            span.set_attribute("levels", str(levels))
    
    def _evict_l1_cache(self) -> None:
        """Evict entries from L1 cache using LRU strategy."""
        if not self._l1_cache:
            return
        
        sorted_entries = sorted(
            self._l1_cache.items(),
            key=lambda x: x[1].last_accessed
        )
        
        evict_count = max(1, len(sorted_entries) // 10)
        for key, _ in sorted_entries[:evict_count]:
            del self._l1_cache[key]
    
    def invalidate_cache(self, pattern: str = None, key: str = None) -> int:
        """Invalidate cache entries.
        
        Args:
            pattern: Pattern to match keys (optional)
            key: Specific key to invalidate (optional)
            
        Returns:
            Number of entries invalidated
        """
        with tracer.start_as_current_span("invalidate_cache", attributes={
            "pattern": pattern or "none",
            "key": key or "none"
        }) as span:
            count = 0
            
            with self._l1_cache_lock:
                if key:
                    if key in self._l1_cache:
                        del self._l1_cache[key]
                        count = 1
                elif pattern:
                    keys_to_delete = [
                        k for k in self._l1_cache.keys()
                        if pattern in k
                    ]
                    for k in keys_to_delete:
                        del self._l1_cache[k]
                        count += 1
            
            span.set_attribute("invalidated_count", count)
            return count
    
    def submit_task(self, func: Callable, *args, **kwargs) -> str:
        """Submit an async task for execution.
        
        Args:
            func: The function to execute
            *args: Positional arguments
            **kwargs: Keyword arguments
            
        Returns:
            Task ID
        """
        with tracer.start_as_current_span("submit_task", attributes={
            "func_name": func.__name__
        }) as span:
            self._task_counter += 1
            task_id = f"task_{self._task_counter}_{int(time.time())}"
            
            task = AsyncTask(
                task_id=task_id,
                status="pending",
                created_at=time.time(),
                completed_at=None,
                result=None,
                error=None
            )
            self._tasks[task_id] = task
            
            def task_wrapper():
                try:
                    self._tasks[task_id].status = "running"
                    result = func(*args, **kwargs)
                    self._tasks[task_id].result = result
                    self._tasks[task_id].status = "completed"
                except Exception as e:
                    self._tasks[task_id].error = str(e)
                    self._tasks[task_id].status = "failed"
                finally:
                    self._tasks[task_id].completed_at = time.time()
            
            self._executor.submit(task_wrapper)
            
            span.set_attribute("task_id", task_id)
            
            return task_id
    
    def get_task_status(self, task_id: str) -> Optional[AsyncTask]:
        """Get the status of an async task.
        
        Args:
            task_id: The task ID
            
        Returns:
            AsyncTask object or None if not found
        """
        return self._tasks.get(task_id)
    
    def batch_process(self, items: List[Any], processor: Callable,
                     batch_size: int = 10) -> List[str]:
        """Process items in batches.
        
        Args:
            items: Items to process
            processor: Function to process each item
            batch_size: Number of items per batch
            
        Returns:
            List of task IDs
        """
        with tracer.start_as_current_span("batch_process", attributes={
            "total_items": len(items),
            "batch_size": batch_size
        }) as span:
            task_ids = []
            
            for i in range(0, len(items), batch_size):
                batch = items[i:i + batch_size]
                
                def process_batch(b=batch):
                    return [processor(item) for item in b]
                
                task_id = self.submit_task(process_batch)
                task_ids.append(task_id)
            
            span.set_attribute("tasks_created", len(task_ids))
            
            return task_ids
    
    async def parallel_execute(self, funcs: List[Tuple[Callable, tuple, dict]]) -> List[Any]:
        """Execute multiple functions in parallel.
        
        Args:
            funcs: List of (function, args, kwargs) tuples
            
        Returns:
            List of results
        """
        with tracer.start_as_current_span("parallel_execute", attributes={
            "function_count": len(funcs)
        }) as span:
            loop = asyncio.get_event_loop()
            
            futures = []
            for func, args, kwargs in funcs:
                if asyncio.iscoroutinefunction(func):
                    future = func(*args, **kwargs)
                else:
                    future = loop.run_in_executor(None, func, *args, **kwargs)
                futures.append(future)
            
            results = await asyncio.gather(*futures, return_exceptions=True)
            
            span.set_attribute("results_count", len(results))
            
            return results
    
    def record_response_time(self, response_time: float, endpoint: str = "unknown") -> None:
        """Record a response time for metrics.
        
        Args:
            response_time: Response time in seconds
            endpoint: The endpoint name
        """
        with self._response_times_lock:
            self._response_times.append(response_time)
            if len(self._response_times) > self._max_response_times:
                self._response_times = self._response_times[-self._max_response_times:]
        
        self.collect_metric("response_time", response_time, {"endpoint": endpoint})
    
    def collect_metric(self, metric_name: str, value: float,
                       tags: Dict[str, str] = None) -> None:
        """Collect a performance metric.
        
        Args:
            metric_name: Name of the metric
            value: Metric value
            tags: Optional tags
        """
        metric = PerformanceMetric(
            metric_name=metric_name,
            value=value,
            timestamp=time.time(),
            tags=tags or {}
        )
        
        with self._metrics_lock:
            self._metrics.append(metric)
            if len(self._metrics) > self._max_metrics:
                self._metrics = self._metrics[-self._max_metrics:]
    
    def get_performance_report(self, time_window: int = 3600) -> PerformanceReport:
        """Generate a performance report.
        
        Args:
            time_window: Time window in seconds
            
        Returns:
            PerformanceReport with metrics and recommendations
        """
        with tracer.start_as_current_span("get_performance_report", attributes={
            "time_window": time_window
        }) as span:
            current_time = time.time()
            start_time = current_time - time_window
            
            with self._response_times_lock:
                recent_times = [t for t in self._response_times]
            
            if recent_times:
                sorted_times = sorted(recent_times)
                avg_response_time = sum(recent_times) / len(recent_times)
                p95_index = int(len(sorted_times) * 0.95)
                p99_index = int(len(sorted_times) * 0.99)
                p95_response_time = sorted_times[min(p95_index, len(sorted_times) - 1)]
                p99_response_time = sorted_times[min(p99_index, len(sorted_times) - 1)]
            else:
                avg_response_time = 0
                p95_response_time = 0
                p99_response_time = 0
            
            throughput = len(recent_times) / time_window if time_window > 0 else 0
            
            with self._l1_cache_lock:
                cache_hit_rate = 0
                total_access = sum(e.access_count for e in self._l1_cache.values())
                if total_access > 0:
                    cache_hit_rate = total_access / (total_access + len(self._l1_cache))
            
            bottlenecks = []
            recommendations = []
            
            if avg_response_time > self._performance_thresholds["response_time_warning"]:
                bottlenecks.append({
                    "type": "high_response_time",
                    "value": avg_response_time,
                    "threshold": self._performance_thresholds["response_time_warning"]
                })
                recommendations.append("Consider optimizing slow endpoints or adding caching")
            
            if cache_hit_rate < self._performance_thresholds["cache_hit_rate_warning"]:
                bottlenecks.append({
                    "type": "low_cache_hit_rate",
                    "value": cache_hit_rate,
                    "threshold": self._performance_thresholds["cache_hit_rate_warning"]
                })
                recommendations.append("Increase cache TTL or warm up frequently accessed data")
            
            slow_queries = [
                {"hash": h, "avg_time": s["total_time"] / s["count"]}
                for h, s in self._query_stats.items()
                if s["count"] > 0 and s["total_time"] / s["count"] > 0.5
            ]
            
            if slow_queries:
                bottlenecks.append({
                    "type": "slow_queries",
                    "count": len(slow_queries),
                    "queries": slow_queries[:5]
                })
                recommendations.append("Optimize slow database queries")
            
            report = PerformanceReport(
                report_time=current_time,
                avg_response_time=round(avg_response_time, 4),
                p95_response_time=round(p95_response_time, 4),
                p99_response_time=round(p99_response_time, 4),
                throughput=round(throughput, 2),
                error_rate=0.0,
                cache_hit_rate=round(cache_hit_rate, 4),
                active_connections=self._connection_pool_stats["active"],
                bottlenecks=bottlenecks,
                recommendations=recommendations
            )
            
            span.set_attribute("avg_response_time", avg_response_time)
            span.set_attribute("bottlenecks_count", len(bottlenecks))
            
            return report
    
    def detect_bottlenecks(self) -> List[Dict[str, Any]]:
        """Detect performance bottlenecks.
        
        Returns:
            List of detected bottlenecks
        """
        with tracer.start_as_current_span("detect_bottlenecks") as span:
            bottlenecks = []
            
            with self._response_times_lock:
                if self._response_times:
                    avg_time = sum(self._response_times) / len(self._response_times)
                    if avg_time > self._performance_thresholds["response_time_critical"]:
                        bottlenecks.append({
                            "type": "critical_response_time",
                            "severity": "critical",
                            "value": avg_time,
                            "message": f"Average response time is {avg_time:.2f}s"
                        })
            
            with self._l1_cache_lock:
                if len(self._l1_cache) > self._l1_cache_size * 0.9:
                    bottlenecks.append({
                        "type": "cache_near_capacity",
                        "severity": "warning",
                        "value": len(self._l1_cache),
                        "message": f"Cache is at {len(self._l1_cache)/self._l1_cache_size*100:.1f}% capacity"
                    })
            
            for query_hash, stats in self._query_stats.items():
                if stats["count"] > 0:
                    avg_time = stats["total_time"] / stats["count"]
                    if avg_time > 1.0:
                        bottlenecks.append({
                            "type": "slow_query",
                            "severity": "warning",
                            "query_hash": query_hash,
                            "avg_time": avg_time,
                            "message": f"Query {query_hash} averages {avg_time:.2f}s"
                        })
            
            if self._connection_pool_stats["wait_count"] > 10:
                bottlenecks.append({
                    "type": "connection_pool_pressure",
                    "severity": "warning",
                    "value": self._connection_pool_stats["wait_count"],
                    "message": "Connection pool experiencing wait pressure"
                })
            
            span.set_attribute("bottlenecks_found", len(bottlenecks))
            
            return bottlenecks
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics.
        
        Returns:
            Dictionary with cache statistics
        """
        with self._l1_cache_lock:
            total_size = sum(e.size_bytes for e in self._l1_cache.values())
            total_access = sum(e.access_count for e in self._l1_cache.values())
            
            return {
                "l1_cache": {
                    "entries": len(self._l1_cache),
                    "max_entries": self._l1_cache_size,
                    "total_size_bytes": total_size,
                    "total_access": total_access,
                    "utilization": len(self._l1_cache) / self._l1_cache_size
                }
            }
    
    def get_query_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get query statistics.
        
        Returns:
            Dictionary with query statistics
        """
        return dict(self._query_stats)
    
    def clear_metrics(self) -> None:
        """Clear all collected metrics."""
        with self._metrics_lock:
            self._metrics.clear()
        
        with self._response_times_lock:
            self._response_times.clear()
        
        self._query_stats.clear()
    
    def update_connection_pool_stats(self, active: int, idle: int, wait_count: int = 0) -> None:
        """Update connection pool statistics.
        
        Args:
            active: Number of active connections
            idle: Number of idle connections
            wait_count: Number of waiting requests
        """
        self._connection_pool_stats["active"] = active
        self._connection_pool_stats["idle"] = idle
        self._connection_pool_stats["wait_count"] = wait_count
    
    def shutdown(self) -> None:
        """Shutdown the performance service."""
        self._executor.shutdown(wait=True)
