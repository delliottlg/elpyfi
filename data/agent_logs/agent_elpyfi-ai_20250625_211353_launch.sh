#!/bin/bash
cd "/Users/d/Documents/projects/elpyfi-pm-claude/worktrees/elpyfi-ai_elpyfi-ai_20250625_211353"

# Add delay to slow down agent actions
echo "🕐 Waiting 30 seconds before starting agent..."
sleep 30

# Launch Claude Code with the task
claude \
    --task "You are working on the elpyfi-ai service.

Task: Update Pydantic .dict() to .model_dump() for v2 compatibility
\nThis relates to issue #59520bf4

Please proceed with fixing this issue. Make sure to:
1. Read relevant files first
2. Make the necessary changes
3. Test your changes if possible
4. Provide a summary of what you did
" \
    --dangerously-skip-permissions \
    --delay 30 \
    2>&1 | tee "/Users/d/Documents/projects/elpyfi-pm-claude/data/agent_logs/agent_elpyfi-ai_20250625_211353.log"
