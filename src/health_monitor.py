#!/usr/bin/env python3
"""
Health Monitor for PM Claude
Monitors service health and performs automatic recovery
"""

import asyncio
import aiohttp
import psutil
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


@dataclass
class HealthCheck:
    """Health check configuration"""
    type: str  # http, tcp, process
    endpoint: Optional[str] = None
    interval: int = 30  # seconds
    timeout: int = 10
    retries: int = 3
    
    
@dataclass
class HealthStatus:
    """Health status of a service"""
    service_id: str
    is_healthy: bool
    last_check: datetime
    consecutive_failures: int = 0
    error_message: Optional[str] = None
    response_time: Optional[float] = None
    details: Dict[str, Any] = field(default_factory=dict)


class HealthMonitor:
    """Monitors service health and coordinates recovery"""
    
    def __init__(self, orchestrator):
        self.orchestrator = orchestrator
        self.health_status: Dict[str, HealthStatus] = {}
        self.monitoring_tasks: Dict[str, asyncio.Task] = {}
        self.recovery_callbacks: Dict[str, List[Callable]] = {}
        self._running = False
        
    async def start_monitoring(self):
        """Start health monitoring for all services"""
        self._running = True
        
        for service_id, service in self.orchestrator.services.items():
            if service.health_check and service.status == "running":
                task = asyncio.create_task(
                    self._monitor_service(service_id)
                )
                self.monitoring_tasks[service_id] = task
        
        logger.info(f"Started health monitoring for {len(self.monitoring_tasks)} services")
    
    async def stop_monitoring(self):
        """Stop all health monitoring"""
        self._running = False
        
        for task in self.monitoring_tasks.values():
            task.cancel()
        
        await asyncio.gather(*self.monitoring_tasks.values(), return_exceptions=True)
        self.monitoring_tasks.clear()
        
        logger.info("Stopped health monitoring")
    
    async def _monitor_service(self, service_id: str):
        """Monitor a single service"""
        service = self.orchestrator.services[service_id]
        health_config = HealthCheck(**service.health_check)
        
        # Initialize health status
        self.health_status[service_id] = HealthStatus(
            service_id=service_id,
            is_healthy=True,
            last_check=datetime.now()
        )
        
        while self._running and service.status == "running":
            try:
                # Perform health check
                is_healthy, response_time, error = await self._check_health(
                    service_id, health_config
                )
                
                # Update status
                status = self.health_status[service_id]
                status.last_check = datetime.now()
                status.response_time = response_time
                
                if is_healthy:
                    if not status.is_healthy:
                        logger.info(f"✅ {service_id} recovered")
                        await self._trigger_recovery_callbacks(service_id, "recovered")
                    
                    status.is_healthy = True
                    status.consecutive_failures = 0
                    status.error_message = None
                else:
                    status.consecutive_failures += 1
                    status.error_message = error
                    
                    if status.is_healthy:
                        logger.warning(f"⚠️  {service_id} health check failed: {error}")
                    
                    # Mark as unhealthy after configured retries
                    if status.consecutive_failures >= health_config.retries:
                        if status.is_healthy:
                            logger.error(f"❌ {service_id} marked unhealthy after {health_config.retries} failures")
                            await self._trigger_recovery_callbacks(service_id, "unhealthy")
                        status.is_healthy = False
                
                # Wait for next check
                await asyncio.sleep(health_config.interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error monitoring {service_id}: {e}")
                await asyncio.sleep(health_config.interval)
    
    async def _check_health(self, service_id: str, config: HealthCheck) -> tuple[bool, Optional[float], Optional[str]]:
        """Perform a health check"""
        start_time = time.time()
        
        try:
            if config.type == "http":
                return await self._check_http_health(config.endpoint, config.timeout)
            
            elif config.type == "tcp":
                # Simple TCP connection check
                host, port = config.endpoint.split(":")
                return await self._check_tcp_health(host, int(port), config.timeout)
            
            elif config.type == "process":
                # Check if process is running
                service = self.orchestrator.services[service_id]
                if service.process and service.process.poll() is None:
                    response_time = time.time() - start_time
                    return True, response_time, None
                else:
                    return False, None, "Process not running"
            
            elif config.type == "postgresql":
                # Database health check
                return await self._check_postgresql_health(config.endpoint, config.timeout)
            
            else:
                return False, None, f"Unknown health check type: {config.type}"
                
        except Exception as e:
            return False, None, str(e)
    
    async def _check_http_health(self, endpoint: str, timeout: int) -> tuple[bool, Optional[float], Optional[str]]:
        """Check HTTP endpoint health"""
        start_time = time.time()
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(endpoint, timeout=timeout) as response:
                    response_time = time.time() - start_time
                    
                    if response.status == 200:
                        return True, response_time, None
                    else:
                        return False, response_time, f"HTTP {response.status}"
                        
            except asyncio.TimeoutError:
                return False, None, "Request timeout"
            except aiohttp.ClientError as e:
                return False, None, f"Connection error: {str(e)}"
    
    async def _check_tcp_health(self, host: str, port: int, timeout: int) -> tuple[bool, Optional[float], Optional[str]]:
        """Check TCP connection health"""
        start_time = time.time()
        
        try:
            _, writer = await asyncio.wait_for(
                asyncio.open_connection(host, port),
                timeout=timeout
            )
            writer.close()
            await writer.wait_closed()
            
            response_time = time.time() - start_time
            return True, response_time, None
            
        except asyncio.TimeoutError:
            return False, None, "Connection timeout"
        except Exception as e:
            return False, None, f"Connection failed: {str(e)}"
    
    async def _check_postgresql_health(self, connection_string: str, timeout: int) -> tuple[bool, Optional[float], Optional[str]]:
        """Check PostgreSQL health"""
        start_time = time.time()
        
        try:
            import asyncpg
            
            conn = await asyncio.wait_for(
                asyncpg.connect(connection_string),
                timeout=timeout
            )
            
            # Simple query to check connection
            await conn.fetchval("SELECT 1")
            await conn.close()
            
            response_time = time.time() - start_time
            return True, response_time, None
            
        except asyncio.TimeoutError:
            return False, None, "Database connection timeout"
        except Exception as e:
            return False, None, f"Database error: {str(e)}"
    
    def register_recovery_callback(self, service_id: str, callback: Callable):
        """Register a callback for service recovery events"""
        if service_id not in self.recovery_callbacks:
            self.recovery_callbacks[service_id] = []
        self.recovery_callbacks[service_id].append(callback)
    
    async def _trigger_recovery_callbacks(self, service_id: str, event: str):
        """Trigger recovery callbacks for a service"""
        if service_id in self.recovery_callbacks:
            for callback in self.recovery_callbacks[service_id]:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(service_id, event)
                    else:
                        callback(service_id, event)
                except Exception as e:
                    logger.error(f"Error in recovery callback: {e}")
    
    def get_health_summary(self) -> Dict[str, Any]:
        """Get health summary for all services"""
        summary = {
            "timestamp": datetime.now().isoformat(),
            "services": {},
            "overall_health": True
        }
        
        for service_id, status in self.health_status.items():
            service_info = {
                "healthy": status.is_healthy,
                "last_check": status.last_check.isoformat(),
                "response_time": status.response_time,
                "consecutive_failures": status.consecutive_failures,
                "error": status.error_message
            }
            
            # Add service process info
            service = self.orchestrator.services.get(service_id)
            if service and service.process:
                try:
                    process = psutil.Process(service.process.pid)
                    service_info["cpu_percent"] = process.cpu_percent(interval=0.1)
                    service_info["memory_mb"] = process.memory_info().rss / 1024 / 1024
                except:
                    pass
            
            summary["services"][service_id] = service_info
            
            if not status.is_healthy:
                summary["overall_health"] = False
        
        return summary
    
    async def perform_auto_recovery(self, service_id: str):
        """Attempt to auto-recover a failed service"""
        logger.info(f"Attempting auto-recovery for {service_id}")
        
        # Stop the service
        self.orchestrator.stop_service(service_id)
        
        # Wait a moment
        await asyncio.sleep(5)
        
        # Try to restart
        success = self.orchestrator.start_service(service_id)
        
        if success:
            logger.info(f"✅ Successfully recovered {service_id}")
            # Restart monitoring
            if service_id in self.monitoring_tasks:
                self.monitoring_tasks[service_id].cancel()
            
            task = asyncio.create_task(self._monitor_service(service_id))
            self.monitoring_tasks[service_id] = task
        else:
            logger.error(f"❌ Failed to recover {service_id}")
    
    def print_health_status(self):
        """Print formatted health status"""
        summary = self.get_health_summary()
        
        print("\n🏥 Health Status")
        print("=" * 80)
        print(f"Overall Health: {'✅ Healthy' if summary['overall_health'] else '❌ Unhealthy'}")
        print(f"Timestamp: {summary['timestamp']}")
        print("-" * 80)
        
        print(f"{'Service':<25} {'Status':<10} {'Response':<12} {'CPU':<8} {'Memory':<10} {'Last Check':<20}")
        print("-" * 80)
        
        for service_id, info in summary["services"].items():
            service_name = self.orchestrator.services[service_id].name
            status = "✅ Healthy" if info["healthy"] else "❌ Unhealthy"
            response = f"{info['response_time']*1000:.0f}ms" if info['response_time'] else "-"
            cpu = f"{info.get('cpu_percent', 0):.1f}%" if 'cpu_percent' in info else "-"
            memory = f"{info.get('memory_mb', 0):.1f}MB" if 'memory_mb' in info else "-"
            last_check = datetime.fromisoformat(info['last_check']).strftime("%H:%M:%S")
            
            print(f"{service_name:<25} {status:<10} {response:<12} {cpu:<8} {memory:<10} {last_check:<20}")
            
            if info['error']:
                print(f"  └─ Error: {info['error']}")
        
        print("=" * 80)