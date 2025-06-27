#!/usr/bin/env python3
"""
PM Claude MCP Server using FastMCP
"""

import sys
from pathlib import Path
from typing import Optional, List

from mcp.server.fastmcp import FastMCP

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from service_orchestrator import ServiceOrchestrator
from test_runner import ServiceTestRunner
from issue_tracker import IssueTracker, IssueSeverity, IssueStatus

# Create FastMCP instance
mcp = FastMCP("pm-claude")

# Global instances
orchestrator: Optional[ServiceOrchestrator] = None
test_runner: Optional[ServiceTestRunner] = None
issue_tracker: Optional[IssueTracker] = None


def init_services():
    """Initialize services if needed"""
    global orchestrator, test_runner, issue_tracker
    if orchestrator is None:
        base_path = Path(__file__).parent.parent
        orchestrator = ServiceOrchestrator(base_path)
        orchestrator.load_config()
        try:
            orchestrator.secrets_manager.load_secrets()
        except Exception as e:
            print(f"Warning: Could not load secrets: {e}", file=sys.stderr)
        test_runner = ServiceTestRunner(base_path)
        issue_tracker = IssueTracker(base_path)


@mcp.tool()
def start_services(services: List[str] = None) -> str:
    """
    Start ElPyFi services
    
    Args:
        services: List of service names to start. If None, starts all services.
    
    Returns:
        Status message
    """
    init_services()
    
    if services is None:
        services = []
    
    orchestrator.start_all(services)
    
    # Get status
    status = orchestrator.status()
    running = [f"✅ {info['name']} (PID: {info['pid']})" 
               for sid, info in status.items() 
               if info['status'] == 'running']
    
    if running:
        return "Started services:\n" + "\n".join(running)
    else:
        return "No services were started successfully"


@mcp.tool()
def stop_services(services: List[str] = None) -> str:
    """
    Stop ElPyFi services
    
    Args:
        services: List of service names to stop. If None, stops all services.
    
    Returns:
        Status message
    """
    init_services()
    
    if services:
        for service in services:
            orchestrator.stop_service(service)
        return f"Stopped services: {', '.join(services)}"
    else:
        orchestrator.stop_all()
        return "All services stopped"


@mcp.tool()
def service_status() -> str:
    """
    Get the current status of all services
    
    Returns:
        Formatted status table
    """
    init_services()
    
    status = orchestrator.status()
    
    lines = ["Service Status:\n"]
    lines.append(f"{'Service':<25} {'Status':<10} {'PID':<8} {'Uptime':<10} {'Memory':<10}")
    lines.append("-" * 70)
    
    for service_id, info in status.items():
        status_emoji = {
            'running': '✅',
            'stopped': '⏹️',
            'failed': '❌'
        }.get(info['status'], '❓')
        
        lines.append(
            f"{info['name']:<25} {status_emoji} {info['status']:<8} "
            f"{info['pid'] or '-':<8} {info['uptime'] or '-':<10} "
            f"{info['memory'] or '-':<10}"
        )
    
    return "\n".join(lines)


@mcp.tool()
def run_tests(service: Optional[str] = None) -> str:
    """
    Run tests for ElPyFi services
    
    Args:
        service: Service name to test. If None, runs all tests.
    
    Returns:
        Test results
    """
    init_services()
    
    if service:
        # Run specific service test
        test_method = getattr(test_runner, f"test_{service.replace('-', '_')}", None)
        if test_method:
            result = test_method()
            status = "✅ PASSED" if result['success'] else "❌ FAILED"
            message = f"{service}: {status}"
            if not result['success'] and result.get('error'):
                message += f"\nError: {result['error'][:200]}..."
            return message
        else:
            return f"Unknown service: {service}"
    else:
        # Run all tests
        success = test_runner.run_all_tests()
        return "All tests passed!" if success else "Some tests failed. Check the output for details."


@mcp.tool()
def list_services() -> str:
    """
    List all available services
    
    Returns:
        List of services with descriptions
    """
    init_services()
    
    lines = ["Available services:\n"]
    
    for service_id, service in orchestrator.services.items():
        lines.append(f"• {service_id}")
        lines.append(f"  Name: {service.name}")
        lines.append(f"  Path: {service.path}")
        if service.depends_on:
            lines.append(f"  Dependencies: {', '.join(service.depends_on)}")
        lines.append("")
    
    return "\n".join(lines)


@mcp.tool()
def add_issue(
    service: str,
    title: str,
    description: str = "",
    severity: str = "medium"
) -> str:
    """
    Add an issue or note for a service
    
    Args:
        service: Service name (e.g., 'elpyfi-dashboard')
        title: Brief issue title
        description: Detailed description (optional)
        severity: low, medium, high, or critical
    
    Returns:
        Issue details
    """
    init_services()
    
    try:
        sev = IssueSeverity(severity.lower())
    except ValueError:
        return f"Invalid severity. Use: low, medium, high, or critical"
    
    issue = issue_tracker.add_issue(
        service=service,
        title=title,
        description=description,
        severity=sev
    )
    
    return f"✅ Added issue {issue.id}: {issue.title}"


@mcp.tool()
def list_issues(
    service: Optional[str] = None,
    status: Optional[str] = None
) -> str:
    """
    List tracked issues
    
    Args:
        service: Filter by service name (optional)
        status: Filter by status - open, in_progress, resolved, wont_fix (optional)
    
    Returns:
        Formatted issue list
    """
    init_services()
    
    status_enum = None
    if status:
        try:
            status_enum = IssueStatus(status.lower())
        except ValueError:
            return f"Invalid status. Use: open, in_progress, resolved, or wont_fix"
    
    issues = issue_tracker.get_issues(service=service, status=status_enum)
    
    if not issues:
        return "No issues found"
    
    lines = [f"📋 Found {len(issues)} issue(s):\n"]
    
    for issue in issues[:10]:  # Limit to 10 for readability
        status_icon = {
            IssueStatus.OPEN: "🔴",
            IssueStatus.IN_PROGRESS: "🟡", 
            IssueStatus.RESOLVED: "🟢",
            IssueStatus.WONT_FIX: "⚪"
        }.get(issue.status, "❓")
        
        lines.append(f"{status_icon} [{issue.id}] {issue.service}: {issue.title}")
        if issue.description:
            lines.append(f"   {issue.description[:100]}...")
    
    if len(issues) > 10:
        lines.append(f"\n... and {len(issues) - 10} more")
    
    return "\n".join(lines)


@mcp.tool()
def update_issue(
    issue_id: str,
    status: Optional[str] = None,
    description: Optional[str] = None
) -> str:
    """
    Update an issue's status or description
    
    Args:
        issue_id: Issue ID to update
        status: New status - open, in_progress, resolved, wont_fix (optional)
        description: New description (optional)
    
    Returns:
        Update confirmation
    """
    init_services()
    
    status_enum = None
    if status:
        try:
            status_enum = IssueStatus(status.lower())
        except ValueError:
            return f"Invalid status. Use: open, in_progress, resolved, or wont_fix"
    
    issue = issue_tracker.update_issue(
        issue_id=issue_id,
        status=status_enum,
        description=description
    )
    
    if issue:
        return f"✅ Updated issue {issue.id}: {issue.title} (status: {issue.status.value})"
    else:
        return f"❌ Issue {issue_id} not found"


# Multi-agent orchestration tools
@mcp.tool()
def dispatch_agent(service: str, task: str, issue_id: Optional[str] = None, auto_approve: bool = False) -> str:
    """
    Dispatch a Claude Code agent to work on a task
    
    Args:
        service: Service name (e.g. elpyfi-dashboard)
        task: Task description
        issue_id: Associated issue ID (optional)
        auto_approve: Skip approval step (optional)
    
    Returns:
        Dispatch status
    """
    init_services()
    from agent_orchestrator import AgentOrchestrator
    
    orchestrator = AgentOrchestrator(base_path)
    orchestrator.require_approval = not auto_approve
    
    # Add task
    agent_task = orchestrator.add_task(service, task, issue_id)
    
    # Dispatch agent
    agent = orchestrator.dispatch_agent(agent_task)
    
    if agent:
        return f"""Agent dispatched successfully!
Agent ID: {agent.agent_id}
Service: {service}
Task: {task}
Worktree: {agent.worktree_path}
Status: {agent.status.value}

Use 'get_agent_status' to monitor progress."""
    else:
        return "Failed to dispatch agent. Check if maximum parallel agents limit reached."


@mcp.tool()
def get_agent_status(agent_id: Optional[str] = None) -> str:
    """
    Get status of agents
    
    Args:
        agent_id: Specific agent ID (optional, shows all if not provided)
    
    Returns:
        Agent status information
    """
    init_services()
    from agent_orchestrator import AgentOrchestrator
    
    orchestrator = AgentOrchestrator(base_path)
    status = orchestrator.get_status()
    
    if agent_id:
        agent_info = status['agents'].get(agent_id)
        if agent_info:
            return f"""Agent: {agent_id}
Service: {agent_info['service']}
Task: {agent_info['task']}
Status: {agent_info['status']}
Started: {agent_info['started_at']}
Duration: {agent_info['duration'] or 'just started'}"""
        else:
            return f"Agent {agent_id} not found"
    else:
        result = f"Active agents: {status['active_agents']}\n"
        result += f"Queued tasks: {status['queued_tasks']}\n\n"
        
        for aid, info in status['agents'].items():
            result += f"\n{aid}:\n"
            result += f"  Service: {info['service']}\n"
            result += f"  Status: {info['status']}\n"
            result += f"  Duration: {info['duration'] or 'just started'}\n"
        
        return result if status['agents'] else "No active agents"


@mcp.tool() 
def auto_dispatch_agents(service: Optional[str] = None, auto_approve: bool = False) -> str:
    """
    Automatically dispatch agents for all open issues
    
    Args:
        service: Filter by service name (optional)
        auto_approve: Skip approval step (optional)
    
    Returns:
        Dispatch summary
    """
    init_services()
    from agent_orchestrator import AgentOrchestrator
    
    orchestrator = AgentOrchestrator(base_path)
    orchestrator.require_approval = not auto_approve
    
    tracker = IssueTracker(base_path)
    issues = [i for i in tracker.get_issues() if i.status.value == 'open']
    
    if service:
        issues = [i for i in issues if i.service == service]
    
    if not issues:
        return "No open issues found"
    
    dispatched = []
    failed = []
    
    for issue in issues:
        agent_task = orchestrator.add_task(
            service=issue.service,
            description=f"{issue.title}\n\n{issue.description}",
            issue_id=issue.id
        )
        
        agent = orchestrator.dispatch_agent(agent_task)
        if agent:
            dispatched.append(f"{issue.service}: {issue.title} (Agent: {agent.agent_id})")
        else:
            failed.append(f"{issue.service}: {issue.title}")
    
    result = f"Dispatched {len(dispatched)} agents:\n"
    result += "\n".join(dispatched)
    
    if failed:
        result += f"\n\nFailed to dispatch {len(failed)}:\n"
        result += "\n".join(failed)
    
    return result


if __name__ == "__main__":
    # Run the server
    mcp.run()