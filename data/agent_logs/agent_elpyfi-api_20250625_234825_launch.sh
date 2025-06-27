#!/bin/bash
cd "/Users/d/Documents/projects/elpyfi-pm-claude/services/elpyfi-api"

# Add delay only if configured
if [ 0 -gt 0 ]; then
    echo "🕐 Waiting 0 seconds before starting agent..."
    sleep 0
fi

# Launch Claude Code with the task
( claude --dangerously-skip-permissions << 'CLAUDE_PROMPT_EOF'
You are working on the elpyfi-api service.

Task: Fix asyncpg connection cleanup


This relates to issue #d3a61355

Please proceed with fixing this issue. Make sure to:
1. Read relevant files first
2. Make the necessary changes
3. Test your changes if possible
4. Provide a summary of what you did

CLAUDE_PROMPT_EOF
) 2>&1 | tee "/Users/d/Documents/projects/elpyfi-pm-claude/data/agent_logs/agent_elpyfi-api_20250625_234825.log"
