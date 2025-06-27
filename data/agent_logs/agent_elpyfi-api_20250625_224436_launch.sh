#!/bin/bash
cd "/Users/d/Documents/projects/elpyfi-pm-claude/worktrees/elpyfi-api_elpyfi-api_20250625_224436"

# Add delay to slow down agent actions
echo "🕐 Waiting 30 seconds before starting agent..."
sleep 30

# Launch Claude Code with the task
cat << 'EOF' | claude \
     \
    2>&1 | tee "/Users/d/Documents/projects/elpyfi-pm-claude/data/agent_logs/agent_elpyfi-api_20250625_224436.log"
You are working on the elpyfi-api service.

Task: Remove old local venv and use PM Claude's shared environment
\nThis relates to issue #5f943e8d

IMPORTANT: Before making any changes, please:
1. Read the relevant files to understand the current implementation
2. Create a plan for fixing this issue
3. Present your plan and wait for approval before proceeding

Start by analyzing the issue and creating a detailed plan.

EOF
