#!/usr/bin/env python3
"""
Service Orchestrator for PM Claude
Manages starting, stopping, and monitoring services
"""

import os
import sys
import signal
import subprocess
import time
import yaml
import asyncio
import psutil
import socket
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime
import logging

from secrets_manager import SecretsManager
from health_monitor import HealthMonitor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ServiceConfig:
    """Configuration for a service"""
    name: str
    path: Path
    command: List[str]
    working_dir: str
    env_prefix: str
    startup_order: int
    depends_on: List[str]
    health_check: Optional[Dict[str, Any]] = None
    process: Optional[subprocess.Popen] = None
    status: str = "stopped"
    last_health_check: Optional[datetime] = None


class ServiceOrchestrator:
    """Orchestrates service lifecycle"""
    
    def __init__(self, base_path: Path):
        self.base_path = base_path
        self.config_path = base_path / "config/services.yaml"
        self.services: Dict[str, ServiceConfig] = {}
        self.secrets_manager = SecretsManager(base_path / "config")
        self.python_cmd = str(base_path / "venv/bin/python")
        self.health_monitor = HealthMonitor(self)
        self.pid_dir = base_path / "data" / "pids"
        self.pid_dir.mkdir(parents=True, exist_ok=True)
        
    def load_config(self):
        """Load service configurations"""
        with open(self.config_path) as f:
            config = yaml.safe_load(f)
        
        for service_id, service_data in config['services'].items():
            if service_data.get('external', False):
                continue  # Skip external services like PostgreSQL
                
            # Parse startup command
            cmd_str = service_data['startup']['command']
            if cmd_str.startswith("python"):
                # Replace with our shared venv python
                cmd_parts = cmd_str.split()
                cmd_parts[0] = self.python_cmd
                command = cmd_parts
            else:
                command = cmd_str.split()
            
            self.services[service_id] = ServiceConfig(
                name=service_data['name'],
                path=self.base_path / service_data['path'],
                command=command,
                working_dir=service_data['startup'].get('working_dir', '.'),
                env_prefix=service_data['startup'].get('env_prefix', ''),
                startup_order=service_data.get('startup_order', 99),
                depends_on=service_data.get('depends_on', []),
                health_check=service_data.get('health')
            )
            
            # Load saved PID if exists
            self._load_service_pid(service_id)
    
    def _save_service_pid(self, service_id: str, pid: int):
        """Save service PID to file"""
        pid_file = self.pid_dir / f"{service_id}.pid"
        pid_file.write_text(str(pid))
    
    def _load_service_pid(self, service_id: str):
        """Load service PID from file and check if process is running"""
        service = self.services.get(service_id)
        if not service:
            return
            
        pid_file = self.pid_dir / f"{service_id}.pid"
        if pid_file.exists():
            try:
                pid = int(pid_file.read_text().strip())
                # Check if process is still running
                if psutil.pid_exists(pid):
                    process = psutil.Process(pid)
                    # Verify it's one of our services
                    cmdline = ' '.join(process.cmdline())
                    # Also check process name for next-server
                    process_name = process.name()
                    if any(part in cmdline for part in ['engine.py', 'main.py', 'elpyfi']) or 'next-server' in process_name:
                        service.status = "running"
                        # Create a minimal process object for compatibility
                        class PidProcess:
                            def __init__(self, pid):
                                self.pid = pid
                            def poll(self):
                                try:
                                    p = psutil.Process(self.pid)
                                    if p.status() == psutil.STATUS_ZOMBIE:
                                        return -1
                                    return None
                                except psutil.NoSuchProcess:
                                    return -1
                            def terminate(self):
                                try:
                                    p = psutil.Process(self.pid)
                                    if p.status() != psutil.STATUS_ZOMBIE:
                                        p.terminate()
                                except:
                                    pass
                            def kill(self):
                                try:
                                    p = psutil.Process(self.pid)
                                    if p.status() != psutil.STATUS_ZOMBIE:
                                        p.kill()
                                except:
                                    pass
                            def wait(self, timeout=None):
                                try:
                                    p = psutil.Process(self.pid)
                                    if p.status() != psutil.STATUS_ZOMBIE:
                                        p.wait(timeout)
                                except:
                                    pass
                        service.process = PidProcess(pid)
                        return
            except:
                pass
            
            # PID file exists but process not running, clean up
            pid_file.unlink()
    
    def _remove_service_pid(self, service_id: str):
        """Remove service PID file"""
        pid_file = self.pid_dir / f"{service_id}.pid"
        if pid_file.exists():
            pid_file.unlink()
    
    def prepare_environment(self, service_id: str) -> Dict[str, str]:
        """Prepare environment variables for a service"""
        # Start with current environment
        env = os.environ.copy()
        
        # Add service-specific secrets
        try:
            service_env = self.secrets_manager.get_service_env_vars(
                service_id, 
                prefix=self.services[service_id].env_prefix
            )
            env.update(service_env)
            
            # Add PM Claude specific vars
            env['PM_CLAUDE_SERVICE'] = service_id
            env['PM_CLAUDE_MANAGED'] = 'true'
            
        except Exception as e:
            logger.warning(f"Could not load secrets for {service_id}: {e}")
        
        return env
    
    def _is_port_in_use(self, port: int) -> bool:
        """Check if a port is already in use"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(1)
                result = s.connect_ex(('localhost', port))
                return result == 0
        except:
            return False
    
    def _get_service_port(self, service: ServiceConfig) -> Optional[int]:
        """Extract port number from service health check config"""
        if not service.health_check or service.health_check.get('type') != 'http':
            return None
        
        endpoint = service.health_check.get('endpoint', '')
        # Extract port from URL like http://localhost:9000/health
        try:
            if ':' in endpoint:
                port_str = endpoint.split(':')[2].split('/')[0]
                return int(port_str)
        except:
            pass
        return None
    
    def start_service(self, service_id: str) -> bool:
        """Start a single service"""
        service = self.services.get(service_id)
        if not service:
            logger.error(f"Unknown service: {service_id}")
            return False
        
        # Check if port is already in use
        port = self._get_service_port(service)
        if port and self._is_port_in_use(port):
            logger.warning(f"Port {port} is already in use for {service_id}")
            # Mark as running since something is already there
            service.status = "running"
            logger.info(f"⚠️ {service.name} appears to be already running on port {port}")
            return True
        
        if service.status == "running":
            logger.info(f"Service {service_id} is already running")
            return True
        
        # Check dependencies
        for dep in service.depends_on:
            if dep in self.services and self.services[dep].status != "running":
                logger.error(f"Cannot start {service_id}: dependency {dep} is not running")
                return False
        
        # Prepare working directory
        working_dir = service.path / service.working_dir
        if not working_dir.exists():
            logger.error(f"Working directory not found: {working_dir}")
            return False
        
        # Prepare environment
        env = self.prepare_environment(service_id)
        
        # Start the service
        try:
            logger.info(f"Starting {service.name} ({service_id})...")
            logger.debug(f"Command: {' '.join(service.command)}")
            logger.debug(f"Working dir: {working_dir}")
            
            # Create log file for this service
            log_dir = self.base_path / "data" / "service_logs"
            log_dir.mkdir(parents=True, exist_ok=True)
            log_file = log_dir / f"{service_id}.log"
            
            # Open log file in append mode
            with open(log_file, 'a') as f:
                f.write(f"\n{'='*60}\n")
                f.write(f"Starting {service.name} at {datetime.now()}\n")
                f.write(f"{'='*60}\n")
            
            # Start service with output to log file
            with open(log_file, 'a') as log_f:
                service.process = subprocess.Popen(
                    service.command,
                    cwd=working_dir,
                    env=env,
                    stdout=log_f,
                    stderr=subprocess.STDOUT,
                    text=True
                )
            
            # Give it a moment to start
            time.sleep(2)
            
            # Check if it's still running
            if service.process.poll() is None:
                service.status = "running"
                logger.info(f"✅ {service.name} started successfully (PID: {service.process.pid})")
                # Save PID for persistence
                self._save_service_pid(service_id, service.process.pid)
                return True
            else:
                service.status = "failed"
                stdout, stderr = service.process.communicate()
                logger.error(f"❌ {service.name} failed to start")
                if stderr:
                    logger.error(f"Error: {stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to start {service_id}: {e}")
            service.status = "failed"
            return False
    
    def stop_service(self, service_id: str) -> bool:
        """Stop a single service"""
        service = self.services.get(service_id)
        if not service:
            return True
        
        # If we have a process reference, use it
        if service.process:
            try:
                logger.info(f"Stopping {service.name}...")
                
                # Try graceful shutdown first
                service.process.terminate()
                try:
                    service.process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    # Force kill if needed
                    logger.warning(f"Force killing {service.name}")
                    service.process.kill()
                    service.process.wait()
                
                service.status = "stopped"
                service.process = None
                self._remove_service_pid(service_id)
                logger.info(f"✅ {service.name} stopped")
                return True
                
            except Exception as e:
                logger.error(f"Failed to stop {service_id}: {e}")
                return False
        
        # If no process but port is in use, try to kill by pattern
        port = self._get_service_port(service)
        if port and self._is_port_in_use(port):
            logger.info(f"Attempting to stop external {service.name} process on port {port}")
            
            # Service-specific kill patterns
            kill_patterns = {
                'elpyfi-core': ['engine.py'],
                'elpyfi-ai': ['main.py.*elpyfi-ai'],
                'elpyfi-api': ['elpyfi_api.main', 'src.elpyfi_api.main'],
                'elpyfi-dashboard': ['next.*9003', 'npm.*dev.*9003']
            }
            
            patterns = kill_patterns.get(service_id, [])
            for pattern in patterns:
                try:
                    subprocess.run(['pkill', '-f', pattern], capture_output=True)
                except:
                    pass
            
            # Give it a moment
            time.sleep(2)
            
            # Check if port is now free
            if not self._is_port_in_use(port):
                service.status = "stopped"
                self._remove_service_pid(service_id)
                logger.info(f"✅ {service.name} stopped")
                return True
            else:
                logger.error(f"Failed to stop {service.name} - port {port} still in use")
                return False
        
        # Nothing to stop
        service.status = "stopped"
        self._remove_service_pid(service_id)
        return True
    
    def start_all(self, services: Optional[List[str]] = None):
        """Start all services in dependency order"""
        # Load secrets first
        try:
            self.secrets_manager.load_secrets()
        except Exception as e:
            logger.error(f"Failed to load secrets: {e}")
            return
        
        # Determine which services to start
        if services:
            service_list = [(s, self.services[s]) for s in services if s in self.services]
        else:
            service_list = list(self.services.items())
        
        # Sort by startup order
        service_list.sort(key=lambda x: x[1].startup_order)
        
        logger.info(f"Starting {len(service_list)} services...")
        
        for service_id, service in service_list:
            if not self.start_service(service_id):
                logger.error(f"Failed to start {service_id}, aborting startup sequence")
                break
    
    def stop_all(self):
        """Stop all services in reverse order"""
        # Sort by startup order (reverse)
        service_list = list(self.services.items())
        service_list.sort(key=lambda x: x[1].startup_order, reverse=True)
        
        logger.info(f"Stopping {len(service_list)} services...")
        
        for service_id, service in service_list:
            self.stop_service(service_id)
    
    def status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all services"""
        status = {}
        
        for service_id, service in self.services.items():
            status[service_id] = {
                'name': service.name,
                'status': service.status,
                'pid': service.process.pid if service.process else None,
                'uptime': self._get_uptime(service),
                'memory': self._get_memory_usage(service),
                'path': str(service.path)
            }
        
        return status
    
    def _get_uptime(self, service: ServiceConfig) -> Optional[str]:
        """Get service uptime"""
        if not service.process or service.status != "running":
            return None
        
        try:
            process = psutil.Process(service.process.pid)
            create_time = datetime.fromtimestamp(process.create_time())
            uptime = datetime.now() - create_time
            
            hours = int(uptime.total_seconds() // 3600)
            minutes = int((uptime.total_seconds() % 3600) // 60)
            return f"{hours}h {minutes}m"
        except:
            return None
    
    def _get_memory_usage(self, service: ServiceConfig) -> Optional[str]:
        """Get service memory usage"""
        if not service.process or service.status != "running":
            return None
        
        try:
            process = psutil.Process(service.process.pid)
            memory = process.memory_info().rss / 1024 / 1024  # MB
            return f"{memory:.1f} MB"
        except:
            return None
    
    def print_status(self):
        """Print formatted status"""
        status = self.status()
        
        print("\n📊 Service Status")
        print("=" * 60)
        print(f"{'Service':<20} {'Status':<10} {'PID':<8} {'Uptime':<10} {'Memory':<10}")
        print("-" * 60)
        
        for service_id, info in status.items():
            status_emoji = {
                'running': '✅',
                'stopped': '⏹️',
                'failed': '❌'
            }.get(info['status'], '❓')
            
            print(f"{info['name']:<20} {status_emoji} {info['status']:<8} "
                  f"{info['pid'] or '-':<8} {info['uptime'] or '-':<10} "
                  f"{info['memory'] or '-':<10}")
        
        print("=" * 60)


def main():
    """CLI for service orchestrator"""
    import argparse
    
    parser = argparse.ArgumentParser(description="PM Claude Service Orchestrator")
    parser.add_argument('command', choices=['start', 'stop', 'status', 'restart'],
                        help='Command to execute')
    parser.add_argument('services', nargs='*', 
                        help='Specific services to operate on (default: all)')
    
    args = parser.parse_args()
    
    # Initialize orchestrator
    base_path = Path(__file__).parent.parent
    orchestrator = ServiceOrchestrator(base_path)
    orchestrator.load_config()
    
    # Execute command
    if args.command == 'start':
        orchestrator.start_all(args.services)
        orchestrator.print_status()
    
    elif args.command == 'stop':
        orchestrator.stop_all()
        print("All services stopped")
    
    elif args.command == 'status':
        orchestrator.print_status()
    
    elif args.command == 'restart':
        orchestrator.stop_all()
        time.sleep(2)
        orchestrator.start_all(args.services)
        orchestrator.print_status()
    
    # Set up signal handlers for graceful shutdown
    def signal_handler(signum, frame):
        print("\n\nReceived interrupt, stopping services...")
        orchestrator.stop_all()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Keep running if services were started
    if args.command in ['start', 'restart']:
        print("\nPress Ctrl+C to stop all services")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    main()