#!/bin/bash
cd "/Users/d/Documents/projects/elpyfi-pm-claude/services/elpyfi-core"

# Add delay only if configured
if [ 30 -gt 0 ]; then
    echo "🕐 Waiting 30 seconds before starting agent..."
    sleep 30
fi

# Launch Claude Code with the task
claude --dangerously-skip-permissions << 'CLAUDE_PROMPT_EOF' 2>&1 | tee "/Users/d/Documents/projects/elpyfi-pm-claude/data/agent_logs/agent_elpyfi-core_20250626_210210.log"
You are working on the elpyfi-core service.

Task: Improve database schema mismatch error handling - While engine.py handles missing order_id column gracefully, add proper warning logs and fallback behavior. Consider adding column existence check on startup to log clear warnings about schema issues.


Please proceed with fixing this issue. Make sure to:
1. Read relevant files first
2. Make the necessary changes
3. Test your changes if possible
4. Provide a summary of what you did

CLAUDE_PROMPT_EOF
