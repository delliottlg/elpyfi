#!/bin/bash
cd "/Users/d/Documents/projects/elpyfi-pm-claude/worktrees/elpyfi-api_elpyfi-api_20250625_211649"

# Add delay to slow down agent actions
echo "🕐 Waiting 10 seconds before starting agent..."
sleep 10

# Launch Claude Code with the task
echo "You are working on the elpyfi-api service.

Task: Clean up .env file to only include ELPYFI_ prefixed variables
\nThis relates to issue #54d618c6

Please proceed with fixing this issue. Make sure to:
1. Read relevant files first
2. Make the necessary changes
3. Test your changes if possible
4. Provide a summary of what you did
" | claude \
    --dangerously-skip-permissions \
    2>&1 | tee "/Users/d/Documents/projects/elpyfi-pm-claude/data/agent_logs/agent_elpyfi-api_20250625_211649.log"
