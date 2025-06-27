#!/bin/bash
cd "/Users/d/Documents/projects/elpyfi-pm-claude/worktrees/elpyfi-core_elpyfi-core_20250625_224727"

# Add delay to slow down agent actions
echo "🕐 Waiting 30 seconds before starting agent..."
sleep 30

# Launch Claude Code with the task
claude  2>&1 | tee "/Users/d/Documents/projects/elpyfi-pm-claude/data/agent_logs/agent_elpyfi-core_20250625_224727.log" << 'CLAUDE_PROMPT_EOF'
You are working on the elpyfi-core service.

Task: Improve database schema mismatch error handling


This relates to issue #0d682431

IMPORTANT: Before making any changes, please:
1. Read the relevant files to understand the current implementation
2. Create a plan for fixing this issue
3. Present your plan and wait for approval before proceeding

Start by analyzing the issue and creating a detailed plan.

CLAUDE_PROMPT_EOF
