#!/usr/bin/env python3
"""
Web Dashboard for PM Claude Agent Orchestration
Real-time monitoring of multiple Claude Code instances
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import asyncio
import json
from datetime import datetime
from typing import List
import uvicorn

from agent_orchestrator import AgentOrchestrator, AgentStatus
from issue_tracker import IssueTracker

app = FastAPI()
base_path = Path(__file__).parent.parent
orchestrator = AgentOrchestrator(base_path)
issue_tracker = IssueTracker(base_path)

# Store active websocket connections
connections: List[WebSocket] = []


@app.get("/")
async def get_dashboard():
    """Serve the dashboard HTML"""
    return HTMLResponse("""
<!DOCTYPE html>
<html>
<head>
    <title>PM Claude Agent Dashboard</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0;
            padding: 20px;
            background: #0a0a0a;
            color: #e0e0e0;
        }
        
        .header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 30px;
            padding-bottom: 20px;
            border-bottom: 1px solid #333;
        }
        
        h1 {
            margin: 0;
            color: #fff;
            font-size: 28px;
        }
        
        .stats {
            display: flex;
            gap: 30px;
            font-size: 14px;
        }
        
        .stat {
            text-align: center;
        }
        
        .stat-value {
            font-size: 24px;
            font-weight: bold;
            color: #4CAF50;
        }
        
        .agents-container {
            display: flex;
            gap: 30px;
            margin-bottom: 30px;
            overflow-x: auto;
        }
        
        .service-column {
            min-width: 280px;
            flex: 1;
            max-width: 320px;
        }
        
        .service-header {
            font-size: 18px;
            font-weight: 600;
            color: #4CAF50;
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 2px solid #333;
        }
        
        .agents-grid {
            display: flex;
            flex-direction: column;
            gap: 15px;
        }
        
        .agent-card {
            background: #1a1a1a;
            border: 1px solid #333;
            border-radius: 8px;
            padding: 15px;
            transition: all 0.3s;
        }
        
        .agent-card:hover {
            border-color: #555;
            transform: translateY(-2px);
        }
        
        .agent-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
        }
        
        .agent-id {
            font-family: monospace;
            font-size: 12px;
            color: #888;
        }
        
        .agent-status {
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 500;
        }
        
        .status-idle { background: #424242; }
        .status-planning { background: #FFA726; color: #000; }
        .status-working { background: #66BB6A; color: #000; }
        .status-awaiting_approval { background: #42A5F5; color: #000; }
        .status-completed { background: #26A69A; color: #000; }
        .status-failed { background: #EF5350; }
        
        .agent-service {
            font-size: 16px;
            font-weight: 500;
            margin-bottom: 8px;
            color: #4CAF50;
        }
        
        .agent-task {
            font-size: 14px;
            color: #ccc;
            margin-bottom: 12px;
            line-height: 1.5;
        }
        
        .agent-duration {
            font-size: 12px;
            color: #888;
        }
        
        .controls {
            margin-bottom: 30px;
            display: flex;
            gap: 10px;
        }
        
        button {
            background: #4CAF50;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 14px;
            transition: background 0.2s;
        }
        
        button:hover {
            background: #45a049;
        }
        
        button:disabled {
            background: #555;
            cursor: not-allowed;
        }
        
        .issues-section {
            margin-top: 40px;
            padding-top: 30px;
            border-top: 1px solid #333;
        }
        
        .issues-table-container {
            margin-top: 25px;
            overflow-x: auto;
        }
        
        .issues-table {
            width: 100%;
            border-collapse: separate;
            border-spacing: 0;
            background: #1a1a1a;
            border: 1px solid #333;
            border-radius: 8px;
            overflow: hidden;
        }
        
        .issues-table th {
            background: #2a2a2a;
            color: #4CAF50;
            padding: 15px;
            text-align: left;
            font-weight: 600;
            font-size: 14px;
            border-bottom: 1px solid #333;
            border-right: 1px solid #333;
        }
        
        .issues-table th:last-child {
            border-right: none;
        }
        
        .issues-table td {
            padding: 15px;
            border-bottom: 1px solid #333;
            border-right: 1px solid #333;
            vertical-align: top;
        }
        
        .issues-table td:last-child {
            border-right: none;
        }
        
        .issues-table tr:last-child td {
            border-bottom: none;
        }
        
        .issues-table tr:hover {
            background: #222;
        }
        
        .issue-title-cell {
            color: #fff;
            font-weight: 500;
            margin-bottom: 5px;
        }
        
        .issue-description-cell {
            color: #999;
            font-size: 12px;
            line-height: 1.4;
            max-width: 300px;
        }
        
        .issue-id-cell {
            font-family: monospace;
            font-size: 11px;
            color: #666;
        }
        
        
        .dispatch-btn {
            background: #2196F3;
            font-size: 12px;
            padding: 6px 12px;
        }
        
        .connection-status {
            position: fixed;
            bottom: 20px;
            right: 20px;
            padding: 8px 16px;
            border-radius: 20px;
            font-size: 12px;
            background: #333;
        }
        
        .connected { background: #4CAF50; color: #000; }
        .disconnected { background: #f44336; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🤖 PM Claude Agent Dashboard</h1>
        <div class="stats">
            <div class="stat">
                <div class="stat-value" id="active-count">0</div>
                <div>Active Agents</div>
            </div>
            <div class="stat">
                <div class="stat-value" id="queued-count">0</div>
                <div>Queued Tasks</div>
            </div>
            <div class="stat">
                <div class="stat-value" id="issue-count">0</div>
                <div>Open Issues</div>
            </div>
        </div>
    </div>
    
    <div class="controls">
        <button onclick="dispatchFromIssues()">Auto-Dispatch from Issues</button>
        <button onclick="refreshStatus()">Refresh</button>
    </div>
    
    <div id="agents-container" class="agents-container"></div>
    
    <div class="issues-section">
        <h2>Open Issues</h2>
        <div class="issues-table-container">
            <table class="issues-table">
                <thead>
                    <tr>
                        <th>PM Claude</th>
                        <th>Core</th>
                        <th>AI</th>
                        <th>API</th>
                        <th>Dashboard</th>
                    </tr>
                </thead>
                <tbody id="issues-table-body">
                </tbody>
            </table>
        </div>
    </div>
    
    <div id="connection-status" class="connection-status disconnected">
        Connecting...
    </div>
    
    <script>
        let ws = null;
        let agentData = {};
        let issueData = {};
        
        function connectWebSocket() {
            ws = new WebSocket("ws://localhost:8100/ws");
            
            ws.onopen = () => {
                document.getElementById('connection-status').className = 'connection-status connected';
                document.getElementById('connection-status').textContent = 'Connected';
            };
            
            ws.onmessage = (event) => {
                const data = JSON.parse(event.data);
                updateDashboard(data);
            };
            
            ws.onclose = () => {
                document.getElementById('connection-status').className = 'connection-status disconnected';
                document.getElementById('connection-status').textContent = 'Disconnected - Reconnecting...';
                setTimeout(connectWebSocket, 2000);
            };
            
            ws.onerror = (error) => {
                console.error('WebSocket error:', error);
            };
        }
        
        function updateDashboard(data) {
            // Update stats
            document.getElementById('active-count').textContent = data.active_agents;
            document.getElementById('queued-count').textContent = data.queued_tasks;
            document.getElementById('issue-count').textContent = data.open_issues;
            
            // Update agents - organize by service
            agentData = data.agents;
            const container = document.getElementById('agents-container');
            container.innerHTML = '';
            
            // Group agents by service
            const serviceGroups = {};
            for (const [agentId, agent] of Object.entries(agentData)) {
                if (!serviceGroups[agent.service]) {
                    serviceGroups[agent.service] = [];
                }
                serviceGroups[agent.service].push([agentId, agent]);
            }
            
            // Create columns for each service (always show all services)
            const services = ['pm-claude', 'elpyfi-core', 'elpyfi-ai', 'elpyfi-api', 'elpyfi-dashboard'];
            for (const service of services) {
                const column = document.createElement('div');
                column.className = 'service-column';
                
                const header = document.createElement('div');
                header.className = 'service-header';
                header.textContent = service;
                column.appendChild(header);
                
                const grid = document.createElement('div');
                grid.className = 'agents-grid';
                
                if (serviceGroups[service] && serviceGroups[service].length > 0) {
                    // Show active agents for this service
                    for (const [agentId, agent] of serviceGroups[service]) {
                        const card = createAgentCard(agentId, agent);
                        grid.appendChild(card);
                    }
                } else {
                    // Show placeholder card for empty services
                    const placeholder = document.createElement('div');
                    placeholder.className = 'agent-card';
                    placeholder.style.opacity = '0.4';
                    placeholder.style.border = '1px dashed #555';
                    placeholder.innerHTML = '<div style="text-align: center; padding: 15px; color: #666; font-size: 14px;">Ready for agents</div>';
                    grid.appendChild(placeholder);
                }
                
                column.appendChild(grid);
                container.appendChild(column);
            }
            
            // Update issues
            issueData = data.issues;
            renderIssuesTable();
        }
        
        function createAgentCard(agentId, agent) {
            const card = document.createElement('div');
            card.className = 'agent-card';
            
            const statusClass = 'status-' + agent.status;
            const duration = agent.duration || 'Just started';
            
            card.innerHTML = `
                <div class="agent-header">
                    <span class="agent-id">${agentId}</span>
                    <span class="agent-status ${statusClass}">${agent.status}</span>
                </div>
                <div class="agent-service">${agent.service}</div>
                <div class="agent-task">${agent.task}</div>
                <div class="agent-duration">⏱️ ${duration}</div>
            `;
            
            return card;
        }
        
        function renderIssuesTable() {
            const tableBody = document.getElementById('issues-table-body');
            
            // Group issues by service
            const services = ['pm-claude', 'elpyfi-core', 'elpyfi-ai', 'elpyfi-api', 'elpyfi-dashboard'];
            const issuesByService = {};
            
            services.forEach(service => {
                issuesByService[service] = issueData.filter(issue => issue.service === service);
            });
            
            // Find max number of issues in any service
            const maxIssues = Math.max(...services.map(service => issuesByService[service].length));
            
            // Clear table
            tableBody.innerHTML = '';
            
            // Create rows
            for (let i = 0; i < maxIssues; i++) {
                const row = document.createElement('tr');
                
                services.forEach(service => {
                    const cell = document.createElement('td');
                    const issue = issuesByService[service][i];
                    
                    if (issue) {
                        const description = issue.description || 'No description provided';
                        const truncatedDesc = description.length > 100 ? 
                            description.substring(0, 100) + '...' : description;
                        
                        cell.innerHTML = `
                            <div class="issue-title-cell">${issue.title}</div>
                            <div class="issue-description-cell">${truncatedDesc}</div>
                            <div class="issue-id-cell">${issue.id}</div>
                            <button class="dispatch-btn" onclick="dispatchAgent('${issue.service}', '${issue.id}')" style="margin-top: 8px;">
                                Dispatch
                            </button>
                        `;
                    } else {
                        cell.innerHTML = '<div style="color: #555; font-style: italic;">No issues</div>';
                    }
                    
                    row.appendChild(cell);
                });
                
                tableBody.appendChild(row);
            }
        }
        
        async function dispatchAgent(service, issueId) {
            try {
                const response = await fetch('/dispatch', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ service, issue_id: issueId })
                });
                const result = await response.json();
                if (result.success) {
                    alert('Agent dispatched successfully!');
                } else {
                    alert('Failed to dispatch agent: ' + result.error);
                }
            } catch (error) {
                alert('Error dispatching agent: ' + error);
            }
        }
        
        async function dispatchFromIssues() {
            if (!confirm('Dispatch agents for all open issues?')) return;
            
            try {
                const response = await fetch('/auto-dispatch', {
                    method: 'POST'
                });
                const result = await response.json();
                alert(`Dispatched ${result.dispatched} agents`);
            } catch (error) {
                alert('Error: ' + error);
            }
        }
        
        
        function refreshStatus() {
            if (ws && ws.readyState === WebSocket.OPEN) {
                ws.send('refresh');
            }
        }
        
        // Connect on load
        connectWebSocket();
    </script>
</body>
</html>
    """)


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates"""
    await websocket.accept()
    connections.append(websocket)
    
    try:
        # Send initial status
        await send_status_update(websocket)
        
        while True:
            # Listen for messages
            data = await websocket.receive_text()
            if data == "refresh":
                await send_status_update(websocket)
            
            # Send periodic updates
            await asyncio.sleep(2)
            await send_status_update(websocket)
            
    except WebSocketDisconnect:
        connections.remove(websocket)


async def send_status_update(websocket: WebSocket):
    """Send current status to a websocket client"""
    status = orchestrator.get_status()
    
    # Get open issues
    open_issues = [
        {
            "id": issue.id,
            "service": issue.service,
            "title": issue.title,
            "description": issue.description,
            "severity": issue.severity.value
        }
        for issue in issue_tracker.get_issues()
        if issue.status.value == 'open'
    ]
    
    data = {
        "active_agents": status["active_agents"],
        "queued_tasks": status["queued_tasks"],
        "agents": status["agents"],
        "issues": open_issues,
        "open_issues": len(open_issues)
    }
    
    await websocket.send_json(data)


@app.post("/dispatch")
async def dispatch_agent(request: dict):
    """Dispatch a new agent"""
    service = request.get("service")
    issue_id = request.get("issue_id")
    
    if not service:
        return {"success": False, "error": "Service required"}
    
    # Get issue details
    issue = issue_tracker.get_issue(issue_id) if issue_id else None
    task = issue.title if issue else "General maintenance"
    
    # Add task
    agent_task = orchestrator.add_task(service, task, issue_id)
    
    # Dispatch agent
    agent = orchestrator.dispatch_agent(agent_task)
    
    if agent:
        # Notify all clients
        for conn in connections:
            await send_status_update(conn)
        
        return {"success": True, "agent_id": agent.agent_id}
    else:
        return {"success": False, "error": "Failed to dispatch agent"}


@app.post("/auto-dispatch")
async def auto_dispatch():
    """Auto-dispatch agents for all open issues"""
    open_issues = [
        issue for issue in issue_tracker.get_issues()
        if issue.status.value == 'open'
    ]
    
    dispatched = 0
    for issue in open_issues:
        agent_task = orchestrator.add_task(
            service=issue.service,
            description=f"{issue.title}\n\n{issue.description}",
            issue_id=issue.id
        )
        
        agent = orchestrator.dispatch_agent(agent_task)
        if agent:
            dispatched += 1
    
    # Notify all clients
    for conn in connections:
        await send_status_update(conn)
    
    return {"dispatched": dispatched, "total_issues": len(open_issues)}


def main():
    """Run the dashboard server"""
    print("🚀 PM Claude Agent Dashboard")
    print("📍 http://localhost:8100")
    print("\nPress Ctrl+C to stop")
    
    uvicorn.run(app, host="0.0.0.0", port=8100)


if __name__ == "__main__":
    main()