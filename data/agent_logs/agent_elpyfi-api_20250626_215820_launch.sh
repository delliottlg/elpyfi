#!/bin/bash
cd "/Users/d/Documents/projects/elpyfi-pm-claude/services/elpyfi-api"

# Add delay only if configured
if [ 0 -gt 0 ]; then
    echo "🕐 Waiting 0 seconds before starting agent..."
    sleep 0
fi

# Launch Claude Code with the task
# Log to both individual file and master agent log
MASTER_LOG="/Users/d/Documents/projects/elpyfi-pm-claude/data/agent_logs/all_agents.log"
AGENT_LOG="/Users/d/Documents/projects/elpyfi-pm-claude/data/agent_logs/agent_elpyfi-api_20250626_215820.log"

echo "==================== AGENT START: agent_elpyfi-api_20250626_215820 ====================" | tee -a "$MASTER_LOG"
echo "Service: elpyfi-api" | tee -a "$MASTER_LOG"
echo "Time: $(date)" | tee -a "$MASTER_LOG"
echo "Task: Add a comment '# Real-time test!' to the top of config.py, then print 'Step 1 done', then 
  add another comment '# Still working...' after 2 seconds, then print 'Step 2 done', then add a final comment '# All done!' 
  and print 'Task completed!'can" | tee -a "$MASTER_LOG"
echo "======================================================================" | tee -a "$MASTER_LOG"

claude --dangerously-skip-permissions << 'CLAUDE_PROMPT_EOF' 2>&1 | tee -a "$AGENT_LOG" | tee -a "$MASTER_LOG"
You are working on the elpyfi-api service.

Task: Add a comment '# Real-time test!' to the top of config.py, then print 'Step 1 done', then 
  add another comment '# Still working...' after 2 seconds, then print 'Step 2 done', then add a final comment '# All done!' 
  and print 'Task completed!'can


Please proceed with fixing this issue. Make sure to:
1. Read relevant files first
2. Make the necessary changes
3. Test your changes if possible
4. Provide a summary of what you did

CLAUDE_PROMPT_EOF

echo "==================== AGENT END: agent_elpyfi-api_20250626_215820 ====================" | tee -a "$MASTER_LOG"
