# 📘 Runbook: Consumer Disconnect / Data Feed Loss

## Alert

- No incoming messages for > 5 seconds
- Consumer heartbeat missing
- `feed_alive == 0`

## Severity

Critical — trading impact

## What this means

Consumer is not receiving market data from multicast feed.

## Diagnosis

ps aux | grep feed_monitor

python3 monitoring/feed_monitor.py

python3 network/multicast_receiver.py

sudo tcpdump -i any udp port 5001

## Recovery

python3 monitoring/feed_monitor.py &

sudo systemctl restart networking

pkill -f feed_monitor && python3 monitoring/feed_monitor.py &

## Verification

feed_alive == 1
packets flowing again
