#!/bin/bash
cd "/Users/d/Documents/projects/elpyfi-pm-claude/worktrees/elpyfi-api_elpyfi-api_20250625_225010/services/elpyfi-api"

# Add delay to slow down agent actions
echo "🕐 Waiting 5 seconds before starting agent..."
sleep 5

# Launch Claude Code with the task
claude --dangerously-skip-permissions 2>&1 | tee "/Users/d/Documents/projects/elpyfi-pm-claude/data/agent_logs/agent_elpyfi-api_20250625_225010.log" << 'CLAUDE_PROMPT_EOF'
You are working on the elpyfi-api service.

Task: Add database connectivity check to /health endpoint


This relates to issue #2a39ccce

Please proceed with fixing this issue. Make sure to:
1. Read relevant files first
2. Make the necessary changes
3. Test your changes if possible
4. Provide a summary of what you did

CLAUDE_PROMPT_EOF
