#!/bin/bash
# Keep PM Claude services running
# Run this in a screen/tmux session to survive terminal closes

while true; do
    echo "[$(date)] Checking services..."
    
    # Check if services are running
    STATUS=$(./pm-claude status | grep "✅ running" | wc -l)
    
    if [ "$STATUS" -lt 4 ]; then
        echo "[$(date)] Some services are down. Restarting..."
        ./pm-claude restart
    else
        echo "[$(date)] All services running OK"
    fi
    
    # Check every 5 minutes
    sleep 300
done