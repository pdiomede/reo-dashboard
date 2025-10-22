# Telegram Bot Logging Guide 📋

Complete guide to understanding and monitoring all log files for the REO Dashboard Telegram Bot.

## Log Files Overview

The bot system generates several log files to track different aspects of operation:

| Log File | Purpose | Location | Format |
|----------|---------|----------|--------|
| `telegram_bot.log` | Technical bot operations | `/home/graph/ftpbox/reo/logs/` | Timestamped with log levels |
| `telegram_bot_activity.log` | User activity tracking | `/home/graph/ftpbox/reo/logs/` | Timestamped events |
| `cron.log` | Dashboard script execution | `/home/graph/ftpbox/reo/` | Script output |
| `systemd journal` | Service management (if using systemd) | System logs | Standard systemd format |
| `subscribers_telegram.json` | Subscriber database | `/home/graph/ftpbox/reo/` | JSON with timestamps |

---

## 1. telegram_bot.log

### What It Tracks

**Technical operations and system events:**
- Bot startup/shutdown
- Command executions
- Errors and warnings
- Telegram API interactions
- Database operations

### Log Format

```
YYYY-MM-DD HH:MM:SS,mmm - logger_name - LEVEL - Message
```

### Example Entries

```
2025-10-22 15:30:00,123 - __main__ - INFO - Starting REO Dashboard Telegram Bot...
2025-10-22 15:30:05,456 - __main__ - INFO - /subscribe command from 123456789 (@username)
2025-10-22 15:30:05,789 - __main__ - INFO - New subscriber: 123456789 (@username)
2025-10-22 15:35:10,234 - __main__ - ERROR - Failed to subscribe: 987654321 (@user2)
```

### How to View

**Live monitoring:**
```bash
tail -f /home/graph/ftpbox/reo/logs/telegram_bot.log
```

**Last 100 lines:**
```bash
tail -n 100 /home/graph/ftpbox/reo/logs/telegram_bot.log
```

**Search for errors:**
```bash
grep ERROR /home/graph/ftpbox/reo/logs/telegram_bot.log
```

**View specific date:**
```bash
grep "2025-10-22" /home/graph/ftpbox/reo/logs/telegram_bot.log
```

---

## 2. telegram_bot_activity.log ⭐

### What It Tracks

**Important user activities and subscriber events:**
- Bot startups with subscriber counts
- New subscriptions (with user details)
- Unsubscribe events
- Subscribe/unsubscribe attempts
- Status checks
- Stats views
- Help command usage
- Test notifications sent

### Log Format

```
YYYY-MM-DD HH:MM:SS,mmm - Event Type - Details
```

### Event Types & Examples

#### Bot Startup
```
2025-10-22 15:30:00,000 - ========== BOT STARTED ==========
2025-10-22 15:30:00,001 - Startup Time: 2025-10-22 15:30:00 UTC
2025-10-22 15:30:00,002 - Active Subscribers: 42
2025-10-22 15:30:00,003 - =================================
```

#### New Subscriber
```
2025-10-22 15:35:10,123 - NEW_SUBSCRIBER ✅ - Chat ID: 123456789, Username: @alice_indexer, Name: Alice Smith
```

#### Unsubscribe
```
2025-10-22 16:20:45,456 - UNSUBSCRIBED 👋 - Chat ID: 987654321, Username: @bob_node, Name: Bob Johnson
```

#### Subscribe Attempts (Already Subscribed)
```
2025-10-22 16:30:00,789 - SUBSCRIBE_ATTEMPT (Already subscribed) - Chat ID: 123456789, Username: @alice_indexer, Name: Alice Smith
```

#### Unsubscribe Attempts (Not Subscribed)
```
2025-10-22 16:35:00,234 - UNSUBSCRIBE_ATTEMPT (Not subscribed) - Chat ID: 555555555, Username: @new_user
```

#### Status Checks
```
2025-10-22 16:40:00,567 - STATUS_CHECK (Subscribed) - Chat ID: 123456789, Username: @alice_indexer, Since: 2025-10-22 15:35:10
2025-10-22 16:41:00,890 - STATUS_CHECK (Not subscribed) - Chat ID: 666666666, Username: @another_user
```

#### Stats Views
```
2025-10-22 16:45:00,123 - STATS_VIEW - Chat ID: 123456789, Username: @alice_indexer
```

#### Test Notifications
```
2025-10-22 16:50:00,456 - TEST_NOTIFICATION_SENT 🧪 - Chat ID: 123456789, Username: @alice_indexer
2025-10-22 16:51:00,789 - TEST_FAILED (Not subscribed) - Chat ID: 777777777, Username: @unsubscribed_user
```

#### Failed Operations
```
2025-10-22 17:00:00,012 - SUBSCRIBE_FAILED ❌ - Chat ID: 888888888, Username: @error_user
2025-10-22 17:01:00,345 - UNSUBSCRIBE_FAILED ❌ - Chat ID: 999999999, Username: @error_user2
```

### How to View

**Live monitoring:**
```bash
tail -f /home/graph/ftpbox/reo/logs/telegram_bot_activity.log
```

**See all new subscribers:**
```bash
grep "NEW_SUBSCRIBER" /home/graph/ftpbox/reo/logs/telegram_bot_activity.log
```

**See all unsubscribes:**
```bash
grep "UNSUBSCRIBED" /home/graph/ftpbox/reo/logs/telegram_bot_activity.log
```

**Count new subscribers today:**
```bash
grep "NEW_SUBSCRIBER" /home/graph/ftpbox/reo/logs/telegram_bot_activity.log | grep "$(date +%Y-%m-%d)" | wc -l
```

**See all bot startups:**
```bash
grep "BOT STARTED" /home/graph/ftpbox/reo/logs/telegram_bot_activity.log
```

**Last 50 activity events:**
```bash
tail -n 50 /home/graph/ftpbox/reo/logs/telegram_bot_activity.log
```

**Activity for specific user (by chat ID):**
```bash
grep "123456789" /home/graph/ftpbox/reo/logs/telegram_bot_activity.log
```

**Activity for specific username:**
```bash
grep "@alice_indexer" /home/graph/ftpbox/reo/logs/telegram_bot_activity.log
```

---

## 3. cron.log

### What It Tracks

**Dashboard script execution output:**
- Script start/completion
- Indexer data retrieval
- Eligibility checks
- Status changes
- Telegram notification sending
- Errors during script execution

### Example Entries

```
✓ Loaded 99 indexers from active_indexers.json
  - Eligible: 60
  - Grace: 2
  - Ineligible: 37
✓ Pass 1 complete: 62 eligible indexers to check
✓ Pass 2 complete: 62 renewal times updated
Pass 3: Updating status based on eligibility renewal time and grace period...
  - Eligible: 60
  - Grace: 2
  - Ineligible: 37
📤 Sending Telegram notifications to 42 subscriber(s)...
✅ Telegram notifications sent: 42 successful, 0 failed
```

### How to View

**Live monitoring:**
```bash
tail -f /home/graph/ftpbox/reo/cron.log
```

**Last execution:**
```bash
tail -n 100 /home/graph/ftpbox/reo/cron.log
```

**Check for errors:**
```bash
grep -i error /home/graph/ftpbox/reo/cron.log
```

**Check notification sending:**
```bash
grep "Telegram notifications" /home/graph/ftpbox/reo/cron.log | tail -n 10
```

---

## 4. Systemd Journal (if using systemd)

### What It Tracks

**Service management and bot output:**
- Service start/stop events
- Bot console output
- System-level errors
- Auto-restart events

### How to View

**Live monitoring:**
```bash
sudo journalctl -u telegram_bot.service -f
```

**Last 100 lines:**
```bash
sudo journalctl -u telegram_bot.service -n 100
```

**Since specific time:**
```bash
sudo journalctl -u telegram_bot.service --since "2025-10-22 15:00"
```

**Today's logs:**
```bash
sudo journalctl -u telegram_bot.service --since today
```

**Last hour:**
```bash
sudo journalctl -u telegram_bot.service --since "1 hour ago"
```

**Errors only:**
```bash
sudo journalctl -u telegram_bot.service -p err
```

---

## 5. subscribers_telegram.json

### What It Tracks

**Subscriber database with metadata:**
- Chat IDs
- Usernames
- Subscribe timestamps
- Unsubscribe timestamps (if applicable)
- Active status
- Total statistics

### Structure

```json
{
  "subscribers": [
    {
      "chat_id": 123456789,
      "username": "alice_indexer",
      "subscribed_at": "2025-10-22 15:35:10",
      "active": true
    },
    {
      "chat_id": 987654321,
      "username": "bob_node",
      "subscribed_at": "2025-10-20 10:00:00",
      "unsubscribed_at": "2025-10-22 16:20:45",
      "active": false
    }
  ],
  "stats": {
    "total_subscribers": 42,
    "total_notifications_sent": 150
  }
}
```

### How to View

**View entire file:**
```bash
cat /home/graph/ftpbox/reo/subscribers_telegram.json
```

**Pretty print:**
```bash
cat /home/graph/ftpbox/reo/subscribers_telegram.json | python3 -m json.tool
```

**Count active subscribers:**
```bash
cat /home/graph/ftpbox/reo/subscribers_telegram.json | grep '"active": true' | wc -l
```

**View stats only:**
```bash
cat /home/graph/ftpbox/reo/subscribers_telegram.json | grep -A3 '"stats"'
```

---

## Monitoring Best Practices

### Daily Checks

```bash
# Check bot is running
ps aux | grep telegram_bot.py

# View recent activity
tail -n 50 /home/graph/ftpbox/reo/logs/telegram_bot_activity.log

# Check for errors in main log
grep ERROR /home/graph/ftpbox/reo/logs/telegram_bot.log | tail -n 10

# Check subscriber count
cat /home/graph/ftpbox/reo/subscribers_telegram.json | grep total_subscribers
```

### Weekly Analysis

```bash
# Count new subscribers this week
grep "NEW_SUBSCRIBER" /home/graph/ftpbox/reo/logs/telegram_bot_activity.log | grep "$(date +%Y-%m)" | wc -l

# Count unsubscribes this week
grep "UNSUBSCRIBED" /home/graph/ftpbox/reo/logs/telegram_bot_activity.log | grep "$(date +%Y-%m)" | wc -l

# Check notification success rate
grep "Telegram notifications sent" /home/graph/ftpbox/reo/cron.log | tail -n 20
```

### Troubleshooting Script

Create a monitoring script `/home/graph/ftpbox/reo/check_bot.sh`:

```bash
#!/bin/bash

echo "========== BOT STATUS CHECK =========="
echo ""

# Check if bot is running
if ps aux | grep -v grep | grep telegram_bot.py > /dev/null; then
    echo "✅ Bot is RUNNING"
else
    echo "❌ Bot is NOT running!"
fi

echo ""

# Check subscriber count
SUBS=$(cat /home/graph/ftpbox/reo/subscribers_telegram.json | grep total_subscribers | grep -o '[0-9]*')
echo "👥 Active Subscribers: $SUBS"

echo ""

# Check notifications sent
NOTIFS=$(cat /home/graph/ftpbox/reo/subscribers_telegram.json | grep total_notifications_sent | grep -o '[0-9]*')
echo "📤 Total Notifications Sent: $NOTIFS"

echo ""

# Check for recent errors
ERROR_COUNT=$(grep ERROR /home/graph/ftpbox/reo/logs/telegram_bot.log | wc -l)
echo "⚠️  Total Errors in Log: $ERROR_COUNT"

echo ""

# Last 5 activity events
echo "📋 Last 5 Activity Events:"
tail -n 5 /home/graph/ftpbox/reo/logs/telegram_bot_activity.log

echo ""
echo "===================================="
```

Make it executable:
```bash
chmod +x /home/graph/ftpbox/reo/check_bot.sh
```

Run it:
```bash
/home/graph/ftpbox/reo/check_bot.sh
```

---

## Log Rotation

To prevent log files from growing too large:

### Option 1: Manual Rotation

Create a script `/home/graph/ftpbox/reo/rotate_logs.sh`:

```bash
#!/bin/bash

cd /home/graph/ftpbox/reo

# Create dated backup of logs
DATE=$(date +%Y%m%d)

if [ -f logs/telegram_bot.log ]; then
    mv logs/telegram_bot.log logs/telegram_bot.log.$DATE
    touch logs/telegram_bot.log
fi

if [ -f logs/telegram_bot_activity.log ]; then
    mv logs/telegram_bot_activity.log logs/telegram_bot_activity.log.$DATE
    touch logs/telegram_bot_activity.log
fi

if [ -f cron.log ]; then
    mv cron.log cron.log.$DATE
    touch cron.log
fi

# Delete logs older than 30 days
find /home/graph/ftpbox/reo/logs -name "*.log.*" -mtime +30 -delete

echo "Logs rotated successfully"

# Restart bot to use new log file
if systemctl is-active --quiet telegram_bot.service; then
    sudo systemctl restart telegram_bot.service
    echo "Bot restarted"
fi
```

### Option 2: Logrotate (System-Level)

Create `/etc/logrotate.d/telegram_bot`:

```
/home/graph/ftpbox/reo/logs/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 0644 graph graph
    postrotate
        systemctl restart telegram_bot.service > /dev/null 2>&1 || true
    endscript
}

/home/graph/ftpbox/reo/cron.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 0644 graph graph
}
```

---

## Quick Reference Commands

```bash
# View all logs live in separate terminals
tail -f /home/graph/ftpbox/reo/logs/telegram_bot.log           # Technical
tail -f /home/graph/ftpbox/reo/logs/telegram_bot_activity.log  # Activity
tail -f /home/graph/ftpbox/reo/cron.log                        # Dashboard
sudo journalctl -u telegram_bot.service -f                      # Systemd

# Search logs (run from /home/graph/ftpbox/reo directory)
grep "NEW_SUBSCRIBER" logs/telegram_bot_activity.log    # New subs
grep "UNSUBSCRIBED" logs/telegram_bot_activity.log      # Unsubs
grep ERROR logs/telegram_bot.log                         # Errors
grep "notifications sent" cron.log                       # Notif stats

# Count events
grep "NEW_SUBSCRIBER" logs/telegram_bot_activity.log | wc -l      # Total subs
grep "UNSUBSCRIBED" logs/telegram_bot_activity.log | wc -l        # Total unsubs
grep "BOT STARTED" logs/telegram_bot_activity.log | wc -l         # Bot restarts

# View specific user activity
grep "123456789" logs/telegram_bot_activity.log         # By chat ID
grep "@username" logs/telegram_bot_activity.log         # By username

# Check current status
ps aux | grep telegram_bot.py                           # Is running?
cat subscribers_telegram.json | grep total_subscribers  # Sub count
tail -n 1 logs/telegram_bot_activity.log                # Last event
```

---

## Summary

**All important bot activities are now logged:**

✅ **New subscribers** - With full user details  
✅ **Unsubscribes** - With timestamp  
✅ **Failed operations** - For debugging  
✅ **Bot startups** - With subscriber count  
✅ **All command usage** - Status checks, stats views, tests  
✅ **Technical errors** - In main log file  
✅ **Dashboard execution** - In cron log  

**Key Files to Monitor:**
1. `logs/telegram_bot_activity.log` - **Most important for tracking subscribers**
2. `logs/telegram_bot.log` - Technical issues and errors
3. `cron.log` - Dashboard script and notification delivery
4. `subscribers_telegram.json` - Current subscriber database

All logs are automatically created in the `logs/` directory and maintained. No manual intervention needed! 📊

