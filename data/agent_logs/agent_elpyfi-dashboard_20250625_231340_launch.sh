#!/bin/bash
cd "/Users/d/Documents/projects/elpyfi-pm-claude/services/elpyfi-dashboard"

# Add delay to slow down agent actions
echo "🕐 Waiting 3 seconds before starting agent..."
sleep 3

# Launch Claude Code with the task
( claude --dangerously-skip-permissions << 'CLAUDE_PROMPT_EOF'
You are working on the elpyfi-dashboard service.

Task: Add error boundary components to prevent full app crashes


This relates to issue #677c187a

Please proceed with fixing this issue. Make sure to:
1. Read relevant files first
2. Make the necessary changes
3. Test your changes if possible
4. Provide a summary of what you did

CLAUDE_PROMPT_EOF
) 2>&1 | tee "/Users/d/Documents/projects/elpyfi-pm-claude/data/agent_logs/agent_elpyfi-dashboard_20250625_231340.log"
