#!/usr/bin/env python3
"""
Multi-Agent Orchestrator for PM Claude
Manages multiple Claude Code instances working on different services
"""

import os
import json
import subprocess
import asyncio
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import logging
import threading
import time

logger = logging.getLogger(__name__)


class AgentStatus(Enum):
    IDLE = "idle"
    PLANNING = "planning"
    WORKING = "working"
    COMPLETED = "completed"
    FAILED = "failed"
    AWAITING_APPROVAL = "awaiting_approval"


@dataclass
class AgentTask:
    """Represents a task for an agent"""
    service: str
    task_id: str
    description: str
    priority: str = "medium"
    issue_id: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    
    
@dataclass
class Agent:
    """Represents a Claude Code agent instance"""
    agent_id: str
    service: str
    task: AgentTask
    status: AgentStatus = AgentStatus.IDLE
    worktree_path: Optional[Path] = None
    process: Optional[subprocess.Popen] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    output_log: List[str] = field(default_factory=list)
    plan: Optional[str] = None
    recent_log_lines: List[str] = field(default_factory=list)  # Last 10 log lines
    

class AgentOrchestrator:
    """Orchestrates multiple Claude Code agents"""
    
    def __init__(self, base_path: Path):
        self.base_path = base_path
        self.agents: Dict[str, Agent] = {}
        self.task_queue: List[AgentTask] = []
        self.max_parallel_agents = 3
        self.require_approval = False  # Use --dangerously-skip-permissions by default
        self.agent_logs_dir = base_path / "data" / "agent_logs"
        self.agent_logs_dir.mkdir(parents=True, exist_ok=True)
        self.agent_delay_seconds = 0  # No delay by default
        
        # Start background thread to monitor agents
        self.monitor_thread = threading.Thread(target=self._monitor_agents, daemon=True)
        self.monitor_thread.start()
        
    def add_task(self, service: str, description: str, issue_id: Optional[str] = None) -> AgentTask:
        """Add a task to the queue"""
        task = AgentTask(
            service=service,
            task_id=f"{service}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            description=description,
            issue_id=issue_id
        )
        self.task_queue.append(task)
        logger.info(f"Added task: {task.task_id} - {description}")
        return task
        
    def dispatch_agent(self, task: AgentTask) -> Optional[Agent]:
        """Dispatch a Claude Code agent for a task"""
        if len([a for a in self.agents.values() if a.status == AgentStatus.WORKING]) >= self.max_parallel_agents:
            logger.warning("Max parallel agents reached")
            return None
            
        agent_id = f"agent_{task.task_id}"
        agent = Agent(
            agent_id=agent_id,
            service=task.service,
            task=task
        )
        
        # Skip worktree creation - agents work directly in service directories
        # This avoids the complexity of managing separate git repos
        agent.worktree_path = None
        
        # Generate task prompt
        prompt = self._generate_prompt(task)
        
        # Launch Claude Code
        if self._launch_claude(agent, prompt):
            self.agents[agent_id] = agent
            agent.status = AgentStatus.PLANNING if self.require_approval else AgentStatus.WORKING
            agent.started_at = datetime.now()
            return agent
        else:
            self._cleanup_worktree(worktree_path)
            return None
            
    def _create_worktree(self, service: str, task_id: str) -> Optional[Path]:
        """Create a git worktree for the agent"""
        service_path = self.base_path / "services" / service
        worktree_path = self.base_path / "worktrees" / f"{service}_{task_id}"
        
        try:
            # Create worktrees directory
            worktree_path.parent.mkdir(exist_ok=True)
            
            # Create new branch and worktree from the service directory
            branch_name = f"agent/{task_id}"
            # First, check if service directory exists and is a git repo
            if not service_path.exists():
                logger.error(f"Service directory does not exist: {service_path}")
                return None
                
            # Create worktree from the main repository but pointing to service subdirectory
            subprocess.run(
                ["git", "worktree", "add", "-b", branch_name, str(worktree_path), "HEAD"],
                cwd=self.base_path,
                check=True,
                capture_output=True
            )
            logger.info(f"Created worktree at {worktree_path}")
            return worktree_path
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to create worktree: {e}")
            logger.error(f"Error output: {e.stderr.decode() if e.stderr else 'No error output'}")
            return None
            
    def _generate_prompt(self, task: AgentTask) -> str:
        """Generate a prompt for Claude Code"""
        prompt = f"""You are working on the {task.service} service.

Task: {task.description}
"""
        
        if task.issue_id:
            prompt += f"""

This relates to issue #{task.issue_id}"""
            
        if self.require_approval:
            prompt += """

IMPORTANT: Before making any changes, please:
1. Read the relevant files to understand the current implementation
2. Create a plan for fixing this issue
3. Present your plan and wait for approval before proceeding

Start by analyzing the issue and creating a detailed plan.
"""
        else:
            prompt += """

Please proceed with fixing this issue. Make sure to:
1. Read relevant files first
2. Make the necessary changes
3. Test your changes if possible
4. Provide a summary of what you did
"""
        
        return prompt
        
    def _launch_claude(self, agent: Agent, prompt: str) -> bool:
        """Launch Claude Code instance"""
        # Save prompt to file
        prompt_file = self.agent_logs_dir / f"{agent.agent_id}_prompt.txt"
        prompt_file.write_text(prompt)
        
        # Create a shell script to launch Claude Code
        # This ensures proper environment and working directory
        launch_script = self.agent_logs_dir / f"{agent.agent_id}_launch.sh"
        # Use the actual service directory, not a worktree
        service_dir = self.base_path / "services" / agent.service
        script_content = f"""#!/bin/bash
cd "{service_dir}"

# Add delay only if configured
if [ {self.agent_delay_seconds} -gt 0 ]; then
    echo "🕐 Waiting {self.agent_delay_seconds} seconds before starting agent..."
    sleep {self.agent_delay_seconds}
fi

# Launch Claude Code with the task
# Log to both individual file and master agent log
MASTER_LOG="{self.agent_logs_dir}/all_agents.log"
AGENT_LOG="{self.agent_logs_dir}/{agent.agent_id}.log"

echo "==================== AGENT START: {agent.agent_id} ====================" | tee -a "$MASTER_LOG"
echo "Service: {agent.service}" | tee -a "$MASTER_LOG"
echo "Time: $(date)" | tee -a "$MASTER_LOG"
echo "Task: {agent.task.description}" | tee -a "$MASTER_LOG"
echo "======================================================================" | tee -a "$MASTER_LOG"

claude {"--dangerously-skip-permissions" if not self.require_approval else ""} << 'CLAUDE_PROMPT_EOF' 2>&1 | tee -a "$AGENT_LOG" | tee -a "$MASTER_LOG"
{prompt}
CLAUDE_PROMPT_EOF

echo "==================== AGENT END: {agent.agent_id} ====================" | tee -a "$MASTER_LOG"
"""
        
        launch_script.write_text(script_content)
        launch_script.chmod(0o755)
        
        try:
            # Launch Claude Code via script
            agent.process = subprocess.Popen(
                [str(launch_script)],
                cwd=agent.worktree_path,
                text=True
            )
            logger.info(f"Launched Claude Code for {agent.agent_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to launch Claude Code: {e}")
            return False
            
    def get_status(self) -> Dict[str, Any]:
        """Get status of all agents"""
        # Clean up dead agents (no process or completed/failed)
        dead_agents = []
        for agent_id, agent in self.agents.items():
            if agent.process and agent.process.poll() is not None:
                # Process has terminated
                if agent.status not in [AgentStatus.COMPLETED, AgentStatus.FAILED]:
                    agent.status = AgentStatus.FAILED
                    agent.completed_at = datetime.now()
                dead_agents.append(agent_id)
        
        # Remove dead agents that have been completed/failed for more than 5 minutes
        for agent_id in list(self.agents.keys()):
            agent = self.agents[agent_id]
            if agent.status in [AgentStatus.COMPLETED, AgentStatus.FAILED]:
                if agent.completed_at and (datetime.now() - agent.completed_at).seconds > 300:
                    del self.agents[agent_id]
        
        return {
            "active_agents": len([a for a in self.agents.values() if a.status == AgentStatus.WORKING]),
            "queued_tasks": len(self.task_queue),
            "agents": {
                agent_id: {
                    "service": agent.service,
                    "task": agent.task.description,
                    "status": agent.status.value,
                    "started_at": agent.started_at.isoformat() if agent.started_at else None,
                    "duration": str(datetime.now() - agent.started_at) if agent.started_at and not agent.completed_at else None,
                    "log_lines": agent.recent_log_lines
                }
                for agent_id, agent in self.agents.items()
            }
        }
        
    def approve_agent_plan(self, agent_id: str) -> bool:
        """Approve an agent's plan to proceed"""
        agent = self.agents.get(agent_id)
        if not agent or agent.status != AgentStatus.AWAITING_APPROVAL:
            return False
            
        agent.status = AgentStatus.WORKING
        # TODO: Signal agent to continue
        return True
        
    def stop_agent(self, agent_id: str) -> bool:
        """Stop a running agent"""
        agent = self.agents.get(agent_id)
        if not agent or not agent.process:
            return False
            
        agent.process.terminate()
        agent.status = AgentStatus.FAILED
        agent.completed_at = datetime.now()
            
        return True
        
    def _cleanup_worktree(self, worktree_path: Path):
        """Remove a git worktree"""
        try:
            subprocess.run(
                ["git", "worktree", "remove", str(worktree_path)],
                cwd=self.base_path,
                check=True,
                capture_output=True
            )
            logger.info(f"Cleaned up worktree at {worktree_path}")
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to cleanup worktree: {e}")
    
    def _monitor_agents(self):
        """Background thread to monitor agent processes"""
        while True:
            try:
                for agent_id, agent in list(self.agents.items()):
                    if agent.process and agent.status in [AgentStatus.WORKING, AgentStatus.PLANNING]:
                        # Check if process has finished
                        poll_result = agent.process.poll()
                        if poll_result is not None:
                            # Process has finished
                            if poll_result == 0:
                                agent.status = AgentStatus.COMPLETED
                                logger.info(f"Agent {agent_id} completed successfully")
                                
                                # Auto-update issue status if agent completed successfully
                                if agent.task.issue_id:
                                    try:
                                        from issue_tracker import IssueTracker, IssueStatus
                                        issue_tracker = IssueTracker(Path(__file__).parent.parent)
                                        issue = issue_tracker.get_issue(agent.task.issue_id)
                                        if issue and issue.status == IssueStatus.OPEN:
                                            issue_tracker.update_issue(agent.task.issue_id, status=IssueStatus.RESOLVED)
                                            logger.info(f"Auto-resolved issue {agent.task.issue_id} after agent completion")
                                    except Exception as e:
                                        logger.error(f"Failed to auto-update issue status: {e}")
                            else:
                                agent.status = AgentStatus.FAILED
                                logger.error(f"Agent {agent_id} failed with code {poll_result}")
                            agent.completed_at = datetime.now()
                        
                        # Check for timeout (e.g., 30 minutes)
                        elif agent.started_at:
                            duration = (datetime.now() - agent.started_at).seconds
                            if duration > 1800:  # 30 minutes
                                logger.warning(f"Agent {agent_id} timed out after {duration} seconds")
                                agent.process.terminate()
                                agent.status = AgentStatus.FAILED
                                agent.completed_at = datetime.now()
                    
                    # Check log for completion indicators and update recent lines
                    log_file = self.agent_logs_dir / f"{agent_id}.log"
                    if log_file.exists():
                        try:
                            content = log_file.read_text()
                            lines = content.strip().split('\n')
                            # Update recent log lines (last 10)
                            agent.recent_log_lines = lines[-10:] if lines else []
                            
                            if agent.status == AgentStatus.WORKING:
                                # Look for completion indicators
                                if any(indicator in content.lower() for indicator in [
                                    "## summary", "summary:", "completed", "finished",
                                    "done!", "task complete", "changes made",
                                    "i've completed", "i have completed", "successfully"
                                ]):
                                    # Check if process is still running or just finished
                                    if agent.process and agent.process.poll() is None:
                                        # Still running but seems done - wait a bit more
                                        pass
                                    else:
                                        # Process finished and log indicates completion
                                        agent.status = AgentStatus.COMPLETED
                                        agent.completed_at = datetime.now()
                                        logger.info(f"Agent {agent_id} completed (detected from log)")
                                        
                                        # Auto-update issue status
                                        if agent.task.issue_id:
                                            try:
                                                from issue_tracker import IssueTracker, IssueStatus
                                                issue_tracker = IssueTracker(Path(__file__).parent.parent)
                                                issue = issue_tracker.get_issue(agent.task.issue_id)
                                                if issue and issue.status == IssueStatus.OPEN:
                                                    issue_tracker.update_issue(agent.task.issue_id, status=IssueStatus.RESOLVED)
                                                    logger.info(f"Auto-resolved issue {agent.task.issue_id} after agent completion")
                                            except Exception as e:
                                                logger.error(f"Failed to auto-update issue status: {e}")
                        except Exception as e:
                            logger.error(f"Error reading log for {agent_id}: {e}")
                
                time.sleep(2)  # Check every 2 seconds
            except Exception as e:
                logger.error(f"Error in monitor thread: {e}")
                time.sleep(5)


def main():
    """Test the agent orchestrator"""
    from pathlib import Path
    
    logging.basicConfig(level=logging.INFO)
    
    base_path = Path(__file__).parent.parent
    orchestrator = AgentOrchestrator(base_path)
    
    # Example: Add tasks from issue tracker
    from issue_tracker import IssueTracker
    tracker = IssueTracker(base_path)
    
    open_issues = [issue for issue in tracker.get_issues() if issue.status.value == 'open']
    
    print(f"Found {len(open_issues)} open issues")
    
    for issue in open_issues:
        task = orchestrator.add_task(
            service=issue.service,
            description=f"Fix issue: {issue.title}",
            issue_id=issue.id
        )
        print(f"Added task for {issue.service}: {task.task_id}")
        
    # Show status
    print(json.dumps(orchestrator.get_status(), indent=2))


if __name__ == "__main__":
    main()