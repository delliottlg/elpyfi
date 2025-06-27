#!/bin/bash
cd "/Users/d/Documents/projects/elpyfi-pm-claude/services/elpyfi-core"

# Add delay only if configured
if [ 30 -gt 0 ]; then
    echo "🕐 Waiting 30 seconds before starting agent..."
    sleep 30
fi

# Launch Claude Code with the task
claude  << 'CLAUDE_PROMPT_EOF' 2>&1 | tee "/Users/d/Documents/projects/elpyfi-pm-claude/data/agent_logs/agent_elpyfi-core_20250626_205452.log"
You are working on the elpyfi-core service.

Task: Improve database schema mismatch error handling - While engine.py handles missing order_id column gracefully, add proper warning logs and fallback behavior. Consider adding column existence check on startup to log clear warnings about schema issues.


IMPORTANT: Before making any changes, please:
1. Read the relevant files to understand the current implementation
2. Create a plan for fixing this issue
3. Present your plan and wait for approval before proceeding

Start by analyzing the issue and creating a detailed plan.

CLAUDE_PROMPT_EOF
