#!/bin/bash
cd "/Users/d/Documents/projects/elpyfi-pm-claude/services/elpyfi-api"

# Add delay only if configured
if [ 30 -gt 0 ]; then
    echo "🕐 Waiting 30 seconds before starting agent..."
    sleep 30
fi

# Launch Claude Code with the task
claude --dangerously-skip-permissions << 'CLAUDE_PROMPT_EOF' 2>&1 | tee "/Users/d/Documents/projects/elpyfi-pm-claude/data/agent_logs/agent_elpyfi-api_20250626_211347.log"
You are working on the elpyfi-api service.

Task: Add a comment '# PM Claude test - agent dispatch working\!' at line 10 of main.py


Please proceed with fixing this issue. Make sure to:
1. Read relevant files first
2. Make the necessary changes
3. Test your changes if possible
4. Provide a summary of what you did

CLAUDE_PROMPT_EOF
