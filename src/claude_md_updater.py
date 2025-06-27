#!/usr/bin/env python3
"""
CLAUDE.md Auto-Updater for PM Claude
Maintains up-to-date context files for Claude across all services
"""

import os
import yaml
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
import git
import logging

logger = logging.getLogger(__name__)


class ClaudeMdUpdater:
    """Updates CLAUDE.md files with current system state"""
    
    def __init__(self, base_path: Path, orchestrator=None):
        self.base_path = base_path
        self.orchestrator = orchestrator
        self.claude_files = self._find_claude_files()
        
    def _find_claude_files(self) -> Dict[str, Path]:
        """Find all CLAUDE.md files in the project"""
        claude_files = {}
        
        # PM Claude's own CLAUDE.md
        pm_claude_md = self.base_path / "CLAUDE.md"
        if pm_claude_md.exists():
            claude_files["pm-claude"] = pm_claude_md
        
        # Service CLAUDE.md files
        services_dir = self.base_path / "services"
        if services_dir.exists():
            for service_dir in services_dir.iterdir():
                if service_dir.is_dir():
                    # Check for CLAUDE.md in root
                    claude_md = service_dir / "CLAUDE.md"
                    if claude_md.exists():
                        claude_files[service_dir.name] = claude_md
                    
                    # Check in subdirectories (like elpyfi-engine)
                    for subdir in service_dir.iterdir():
                        if subdir.is_dir():
                            claude_md = subdir / "CLAUDE.md"
                            if claude_md.exists():
                                claude_files[f"{service_dir.name}/{subdir.name}"] = claude_md
        
        logger.info(f"Found {len(claude_files)} CLAUDE.md files")
        return claude_files
    
    def update_all(self):
        """Update all CLAUDE.md files"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Update PM Claude's main CLAUDE.md
        self._update_pm_claude_md(timestamp)
        
        # Update service-specific CLAUDE.md files
        for service_id, file_path in self.claude_files.items():
            if service_id != "pm-claude":
                self._update_service_md(service_id, file_path, timestamp)
    
    def _update_pm_claude_md(self, timestamp: str):
        """Update PM Claude's main CLAUDE.md"""
        file_path = self.claude_files.get("pm-claude")
        if not file_path:
            return
        
        content = []
        content.append("# PM Claude System Context")
        content.append(f"\n*Last Updated: {timestamp}*")
        
        # System Status
        content.append("\n## System Status")
        
        if self.orchestrator:
            status = self.orchestrator.status()
            running_count = sum(1 for s in status.values() if s['status'] == 'running')
            content.append(f"- **Services Running**: {running_count}/{len(status)}")
            
            # Health status
            if hasattr(self.orchestrator, 'health_monitor'):
                health = self.orchestrator.health_monitor.get_health_summary()
                content.append(f"- **Overall Health**: {'✅ Healthy' if health['overall_health'] else '❌ Issues Detected'}")
        
        # Environment
        content.append(f"- **Environment**: {os.getenv('PM_CLAUDE_ENV', 'development')}")
        content.append(f"- **Python Version**: 3.11.13")
        content.append(f"- **Shared venv**: {self.base_path}/venv")
        
        # Services Overview
        content.append("\n## Services Overview")
        
        if self.orchestrator:
            content.append("\n| Service | Status | PID | Uptime | Memory | Health |")
            content.append("|---------|--------|-----|--------|--------|--------|")
            
            for service_id, info in status.items():
                health_status = "✅" if self.orchestrator.health_monitor.health_status.get(service_id, {}).get('is_healthy', True) else "❌"
                content.append(f"| {info['name']} | {info['status']} | {info['pid'] or '-'} | {info['uptime'] or '-'} | {info['memory'] or '-'} | {health_status} |")
        
        # Recent Events
        content.append("\n## Recent Events")
        content.append("- System initialized")
        content.append("- Services configured with shared Python 3.11 environment")
        content.append("- MCP server available for natural language control")
        
        # Configuration
        content.append("\n## Configuration")
        content.append("- **Config Directory**: `config/`")
        content.append("- **Services Config**: `config/services.yaml`")
        content.append("- **Secrets**: `config/secrets.yaml` (git-ignored)")
        
        # Available Commands
        content.append("\n## Available Commands")
        content.append("\n### CLI:")
        content.append("```bash")
        content.append("./pm-claude start|stop|status|restart [services]")
        content.append("./src/test_runner.py  # Run all tests")
        content.append("```")
        
        content.append("\n### MCP (Natural Language):")
        content.append("- \"Start the trading system\"")
        content.append("- \"Show me service status\"")
        content.append("- \"Run tests for the AI service\"")
        content.append("- \"Stop all services\"")
        
        # Architecture
        content.append("\n## Architecture")
        content.append("```")
        content.append("PM Claude")
        content.append("├── Service Orchestrator (process management)")
        content.append("├── Secrets Manager (config distribution)")
        content.append("├── Health Monitor (auto-recovery)")
        content.append("├── Test Runner (unified testing)")
        content.append("├── MCP Server (natural language)")
        content.append("└── CLAUDE.md Updater (context maintenance)")
        content.append("```")
        
        # Git Information
        content.append("\n## Repository Information")
        try:
            repo = git.Repo(self.base_path)
            content.append(f"- **Current Branch**: {repo.active_branch.name}")
            content.append(f"- **Last Commit**: {repo.head.commit.hexsha[:8]} - {repo.head.commit.message.strip()}")
            content.append(f"- **Modified Files**: {len(repo.index.diff(None))}")
        except:
            content.append("- Git information unavailable")
        
        # Write the file
        with open(file_path, 'w') as f:
            f.write('\n'.join(content))
        
        logger.info("Updated PM Claude CLAUDE.md")
    
    def _update_service_md(self, service_id: str, file_path: Path, timestamp: str):
        """Update a service-specific CLAUDE.md"""
        # Read existing content
        try:
            with open(file_path, 'r') as f:
                original_content = f.read()
        except:
            original_content = ""
        
        # Find the PM Claude section
        pm_section_start = original_content.find("## PM Claude Status")
        if pm_section_start == -1:
            # Add new section at the end
            new_content = original_content.rstrip() + "\n\n"
        else:
            # Replace existing section
            pm_section_end = original_content.find("\n## ", pm_section_start + 1)
            if pm_section_end == -1:
                pm_section_end = len(original_content)
            new_content = original_content[:pm_section_start]
        
        # Add PM Claude status section
        new_content += f"## PM Claude Status\n"
        new_content += f"*Updated by PM Claude on {timestamp}*\n\n"
        
        if self.orchestrator:
            # Find matching service
            matching_service = None
            for sid, service in self.orchestrator.services.items():
                if service_id.startswith(sid):
                    matching_service = (sid, service)
                    break
            
            if matching_service:
                sid, service = matching_service
                info = self.orchestrator.status().get(sid, {})
                
                new_content += f"- **Service Status**: {info.get('status', 'unknown')}\n"
                if info.get('pid'):
                    new_content += f"- **Process ID**: {info['pid']}\n"
                if info.get('uptime'):
                    new_content += f"- **Uptime**: {info['uptime']}\n"
                if info.get('memory'):
                    new_content += f"- **Memory Usage**: {info['memory']}\n"
                
                # Health status
                if hasattr(self.orchestrator, 'health_monitor'):
                    health = self.orchestrator.health_monitor.health_status.get(sid)
                    if health:
                        new_content += f"- **Health Check**: {'✅ Healthy' if health.is_healthy else '❌ Unhealthy'}\n"
                        if health.response_time:
                            new_content += f"- **Response Time**: {health.response_time*1000:.0f}ms\n"
            else:
                new_content += "- Service not managed by PM Claude\n"
        
        new_content += f"\n### Integration with PM Claude\n"
        new_content += f"This service is managed by PM Claude and uses:\n"
        new_content += f"- Shared Python 3.11 virtual environment\n"
        new_content += f"- Centralized secrets management\n"
        new_content += f"- Automated health monitoring\n"
        new_content += f"- Unified test runner\n"
        
        # Add issues section if there are any
        try:
            from issue_tracker import IssueTracker
            tracker = IssueTracker(self.base_path)
            # Match service name - could be 'elpyfi-dashboard' or 'elpyfi-core/elpyfi-engine'
            service_name = service_id.split('/')[0]
            issues = tracker.get_issues(service=service_name)
            
            if issues:
                new_content += f"\n### Known Issues\n"
                for issue in issues:
                    status_text = {
                        'open': 'OPEN',
                        'in_progress': 'IN PROGRESS',
                        'resolved': 'RESOLVED',
                        'wont_fix': 'WONT FIX'
                    }.get(issue.status.value, 'UNKNOWN')
                    
                    new_content += f"- [{status_text}] [{issue.id}] {issue.title}\n"
                    if issue.description:
                        new_content += f"  - {issue.description}\n"
        except Exception as e:
            logger.error(f"Error adding issues section: {e}")
        
        # If we cut off the original content, add it back
        if pm_section_start != -1:
            pm_section_end = original_content.find("\n## ", pm_section_start + 1)
            if pm_section_end != -1:
                new_content += original_content[pm_section_end:]
        
        # Write the updated content
        with open(file_path, 'w') as f:
            f.write(new_content)
        
        logger.info(f"Updated {service_id} CLAUDE.md")
    
    def watch_and_update(self, interval: int = 300):
        """Watch for changes and update periodically"""
        import asyncio
        
        async def update_loop():
            while True:
                try:
                    self.update_all()
                    await asyncio.sleep(interval)
                except Exception as e:
                    logger.error(f"Error updating CLAUDE.md files: {e}")
                    await asyncio.sleep(interval)
        
        return update_loop()


def main():
    """Test the CLAUDE.md updater"""
    from pathlib import Path
    import sys
    
    # Configure logging
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    
    # Add parent to path
    sys.path.insert(0, str(Path(__file__).parent))
    
    from service_orchestrator import ServiceOrchestrator
    
    base_path = Path(__file__).parent.parent
    
    # Initialize orchestrator
    orchestrator = ServiceOrchestrator(base_path)
    orchestrator.load_config()
    
    # Initialize updater
    updater = ClaudeMdUpdater(base_path, orchestrator)
    
    # Update all files
    print("Updating CLAUDE.md files...")
    updater.update_all()
    
    print(f"\nUpdated {len(updater.claude_files)} files:")
    for name, path in updater.claude_files.items():
        print(f"  - {name}: {path}")


if __name__ == "__main__":
    main()