#!/bin/bash
# Simple deployment script for Telegram bot
# This script just restarts the bot service after you've uploaded new files via FTP

echo "======================================"
echo "  Deploying Telegram Bot Updates"
echo "======================================"
echo ""

echo "📦 Restarting Telegram bot service..."
sudo systemctl restart telegram_bot.service

echo ""
echo "⏳ Waiting for bot to start..."
sleep 2

echo ""
echo "📊 Current bot status:"
echo "--------------------------------------"
sudo systemctl status telegram_bot.service --no-pager -l

echo ""
echo "======================================"
echo "✅ Deployment complete!"
echo ""
echo "📋 To view live logs:"
echo "   tail -f /home/graph/ftpbox/reo/logs/telegram_bot_activity.log"
echo "======================================"

