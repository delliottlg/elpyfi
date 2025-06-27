#!/bin/bash
cd "/Users/d/Documents/projects/elpyfi-pm-claude/services/elpyfi-api"

# Add delay only if configured
if [ 30 -gt 0 ]; then
    echo "🕐 Waiting 30 seconds before starting agent..."
    sleep 30
fi

# Launch Claude Code with the task
claude --dangerously-skip-permissions << 'CLAUDE_PROMPT_EOF' 2>&1 | tee "/Users/d/Documents/projects/elpyfi-pm-claude/data/agent_logs/agent_elpyfi-api_20250626_211629.log"
You are working on the elpyfi-api service.

Task: Add three comments to main.py: First add '# Comment 1: Testing agent dispatch' at line 12, then sleep for 1 second, then add '# Comment 2: Agent still working' at line 14, then sleep for 1 second, then add '# Comment 3: Task completed\!' at line 16. Use Python's time.sleep(1) between each comment.


Please proceed with fixing this issue. Make sure to:
1. Read relevant files first
2. Make the necessary changes
3. Test your changes if possible
4. Provide a summary of what you did

CLAUDE_PROMPT_EOF
