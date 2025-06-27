#!/usr/bin/env python3
"""
CLI for PM Claude Agent Orchestration
Keeps the user in the loop while managing multiple Claude Code instances
"""

import click
import json
from pathlib import Path
from datetime import datetime
import time
from rich.console import Console
from rich.table import Table
from rich.live import Live
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.layout import Layout
from rich.text import Text

from agent_orchestrator import AgentStatus, AgentOrchestrator
from issue_tracker import IssueTracker

console = Console()


@click.group()
@click.pass_context
def cli(ctx):
    """PM Claude Agent Manager - Orchestrate multiple Claude Code instances"""
    ctx.ensure_object(dict)
    base_path = Path(__file__).parent.parent
    ctx.obj = {
        'orchestrator': AgentOrchestrator(base_path),
        'issue_tracker': IssueTracker(base_path),
        'base_path': base_path
    }


@cli.command()
@click.argument('service')
@click.argument('task')
@click.option('--issue', '-i', help='Associated issue ID')
@click.option('--auto-approve', is_flag=True, help='Skip approval step')
@click.option('--delay', '-d', type=int, default=0, help='Delay between agent actions (seconds)')
@click.pass_context
def dispatch(ctx, service, task, issue, auto_approve, delay):
    """Dispatch a Claude Code agent to work on a task"""
    orchestrator = ctx.obj['orchestrator']
    
    if auto_approve:
        orchestrator.require_approval = False
    
    orchestrator.agent_delay_seconds = delay
    
    # Add task
    agent_task = orchestrator.add_task(service, task, issue)
    
    # Dispatch agent
    console.print(f"[yellow]Dispatching agent for {service}...[/yellow]")
    agent = orchestrator.dispatch_agent(agent_task)
    
    if agent:
        console.print(f"[green]✓ Agent {agent.agent_id} started![/green]")
        console.print(f"Task: {task}")
        console.print(f"Worktree: {agent.worktree_path}")
        
        if not auto_approve:
            console.print("\n[yellow]Agent will present a plan for approval.[/yellow]")
            console.print("Use 'pm-agent status' to monitor progress.")
    else:
        console.print("[red]✗ Failed to dispatch agent[/red]")


@cli.command()
@click.option('--watch', '-w', is_flag=True, help='Watch status in real-time')
@click.pass_context
def status(ctx, watch):
    """Show status of all agents"""
    orchestrator = ctx.obj['orchestrator']
    
    def create_status_table():
        table = Table(title="PM Claude Active Agents")
        table.add_column("Agent ID", style="cyan")
        table.add_column("Service", style="green")
        table.add_column("Task", style="white")
        table.add_column("Status", style="yellow")
        table.add_column("Duration", style="blue")
        
        status = orchestrator.get_status()
        
        for agent_id, info in status['agents'].items():
            status_emoji = {
                'idle': '⚪',
                'planning': '📝',
                'working': '🔄',
                'awaiting_approval': '⏸️',
                'completed': '✅',
                'failed': '❌'
            }.get(info['status'], '❓')
            
            table.add_row(
                agent_id,
                info['service'],
                info['task'][:50] + '...' if len(info['task']) > 50 else info['task'],
                f"{status_emoji} {info['status']}",
                info['duration'] or '-'
            )
        
        # Summary
        table.caption = f"Active: {status['active_agents']} | Queued: {status['queued_tasks']}"
        return table
    
    if watch:
        with Live(create_status_table(), refresh_per_second=1) as live:
            try:
                while True:
                    time.sleep(1)
                    live.update(create_status_table())
            except KeyboardInterrupt:
                pass
    else:
        console.print(create_status_table())


@cli.command()
@click.option('--all', 'dispatch_all', is_flag=True, help='Dispatch agents for all open issues')
@click.option('--service', '-s', help='Only dispatch for specific service')
@click.option('--auto-approve', is_flag=True, help='Skip approval step')
@click.option('--delay', '-d', type=int, default=0, help='Delay between agent actions (seconds)')
@click.pass_context
def auto_dispatch(ctx, dispatch_all, service, auto_approve, delay):
    """Automatically dispatch agents based on open issues"""
    orchestrator = ctx.obj['orchestrator']
    tracker = ctx.obj['issue_tracker']
    
    if auto_approve:
        orchestrator.require_approval = False
    
    orchestrator.agent_delay_seconds = delay
    
    # Get open issues
    issues = [i for i in tracker.get_issues() if i.status.value == 'open']
    
    if service:
        issues = [i for i in issues if i.service == service]
    
    if not issues:
        console.print("[yellow]No open issues found[/yellow]")
        return
    
    # Show issues
    table = Table(title="Open Issues")
    table.add_column("Service", style="green")
    table.add_column("Issue", style="yellow") 
    table.add_column("Title", style="white")
    
    for issue in issues:
        table.add_row(issue.service, issue.id[:8], issue.title)
    
    console.print(table)
    
    if not dispatch_all:
        if not click.confirm("\nDispatch agents for these issues?"):
            return
    
    # Dispatch agents
    console.print(f"\n[green]Dispatching {len(issues)} agents...[/green]")
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("Dispatching agents...", total=len(issues))
        
        for issue in issues:
            agent_task = orchestrator.add_task(
                service=issue.service,
                description=f"{issue.title}\n\n{issue.description}",
                issue_id=issue.id
            )
            
            agent = orchestrator.dispatch_agent(agent_task)
            if agent:
                console.print(f"[green]✓[/green] {issue.service}: {issue.title[:50]}")
            else:
                console.print(f"[red]✗[/red] {issue.service}: Failed to dispatch")
            
            progress.advance(task)
            time.sleep(0.5)  # Small delay between launches


@cli.command()
@click.argument('agent_id')
@click.pass_context
def approve(ctx, agent_id):
    """Approve an agent's plan"""
    orchestrator = ctx.obj['orchestrator']
    
    agent = orchestrator.agents.get(agent_id)
    if not agent:
        console.print(f"[red]Agent {agent_id} not found[/red]")
        return
    
    # TODO: Show the agent's plan
    if agent.plan:
        console.print(Panel(agent.plan, title=f"Plan from {agent_id}"))
    
    if click.confirm("Approve this plan?"):
        if orchestrator.approve_agent_plan(agent_id):
            console.print("[green]✓ Plan approved! Agent continuing...[/green]")
        else:
            console.print("[red]Failed to approve plan[/red]")


@cli.command()
@click.argument('agent_id')
@click.pass_context
def logs(ctx, agent_id):
    """Show logs from an agent"""
    orchestrator = ctx.obj['orchestrator']
    
    log_file = orchestrator.agent_logs_dir / f"{agent_id}.log"
    if not log_file.exists():
        console.print(f"[red]No logs found for {agent_id}[/red]")
        return
    
    console.print(Panel(log_file.read_text(), title=f"Logs from {agent_id}"))


@cli.command()
@click.argument('agent_id')
@click.pass_context
def stop(ctx, agent_id):
    """Stop a running agent"""
    orchestrator = ctx.obj['orchestrator']
    
    if orchestrator.stop_agent(agent_id):
        console.print(f"[green]✓ Stopped agent {agent_id}[/green]")
    else:
        console.print(f"[red]Failed to stop agent {agent_id}[/red]")


@cli.command()
@click.pass_context
def dashboard(ctx):
    """Interactive dashboard for monitoring agents"""
    orchestrator = ctx.obj['orchestrator']
    
    layout = Layout()
    layout.split_column(
        Layout(name="header", size=3),
        Layout(name="main"),
        Layout(name="footer", size=3)
    )
    
    def update_display():
        # Header
        header = Text("PM Claude Agent Dashboard", style="bold blue")
        layout["header"].update(Panel(header))
        
        # Main content - agent status
        status = orchestrator.get_status()
        
        # Create status display
        main_content = ""
        for agent_id, info in status['agents'].items():
            status_color = {
                'working': 'green',
                'planning': 'yellow',
                'failed': 'red',
                'completed': 'blue'
            }.get(info['status'], 'white')
            
            main_content += f"[{status_color}]● {agent_id}[/{status_color}]\n"
            main_content += f"  Service: {info['service']}\n"
            main_content += f"  Task: {info['task'][:60]}...\n"
            main_content += f"  Duration: {info['duration'] or 'just started'}\n\n"
        
        if not main_content:
            main_content = "[dim]No active agents[/dim]"
        
        layout["main"].update(Panel(main_content, title="Active Agents"))
        
        # Footer
        footer = f"Active: {status['active_agents']} | Queued: {status['queued_tasks']} | Press Ctrl+C to exit"
        layout["footer"].update(Panel(footer))
        
        return layout
    
    with Live(update_display(), refresh_per_second=1, console=console) as live:
        try:
            while True:
                time.sleep(1)
                live.update(update_display())
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    cli()