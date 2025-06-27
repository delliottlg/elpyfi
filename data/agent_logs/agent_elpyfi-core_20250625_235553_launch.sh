#!/bin/bash
cd "/Users/d/Documents/projects/elpyfi-pm-claude/services/elpyfi-core"

# Add delay only if configured
if [ 0 -gt 0 ]; then
    echo "🕐 Waiting 0 seconds before starting agent..."
    sleep 0
fi

# Launch Claude Code with the task
claude --dangerously-skip-permissions << 'CLAUDE_PROMPT_EOF' 2>&1 | tee "/Users/d/Documents/projects/elpyfi-pm-claude/data/agent_logs/agent_elpyfi-core_20250625_235553.log"
You are working on the elpyfi-core service.

Task: Improve database schema mismatch error handling


This relates to issue #0d682431

Please proceed with fixing this issue. Make sure to:
1. Read relevant files first
2. Make the necessary changes
3. Test your changes if possible
4. Provide a summary of what you did

CLAUDE_PROMPT_EOF
