#!/bin/bash
cd "/Users/d/Documents/projects/elpyfi-pm-claude/services/elpyfi-api"

# Add delay only if configured
if [ 0 -gt 0 ]; then
    echo "🕐 Waiting 0 seconds before starting agent..."
    sleep 0
fi

# Launch Claude Code with the task
claude --dangerously-skip-permissions << 'CLAUDE_PROMPT_EOF' 2>&1 | tee "/Users/d/Documents/projects/elpyfi-pm-claude/data/agent_logs/agent_elpyfi-api_20250626_212023.log"
You are working on the elpyfi-api service.

Task: Add a comment '# Real-time test!' to the top of config.py, then print 'Step 1 done', then 
  add another comment '# Still working...' after 2 seconds, then print 'Step 2 done', then add a final comment '# All done!' 
  and print 'Task completed!'


Please proceed with fixing this issue. Make sure to:
1. Read relevant files first
2. Make the necessary changes
3. Test your changes if possible
4. Provide a summary of what you did

CLAUDE_PROMPT_EOF
