#!/usr/bin/env python3
"""
Telegram Bot for REO Dashboard Notifications
Handles user subscriptions and manages the subscriber database.
"""

import json
import os
import logging
from datetime import datetime
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
SUBSCRIBERS_FILE = 'subscribers.json'
DASHBOARD_URL = 'http://dashboards.thegraph.foundation/reo/'

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


def load_subscribers():
    """Load subscribers from JSON file."""
    if not os.path.exists(SUBSCRIBERS_FILE):
        return {
            "subscribers": [],
            "stats": {
                "total_subscribers": 0,
                "total_notifications_sent": 0
            }
        }
    
    try:
        with open(SUBSCRIBERS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading subscribers: {e}")
        return {
            "subscribers": [],
            "stats": {
                "total_subscribers": 0,
                "total_notifications_sent": 0
            }
        }


def save_subscribers(data):
    """Save subscribers to JSON file."""
    try:
        with open(SUBSCRIBERS_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        logger.error(f"Error saving subscribers: {e}")
        return False


def is_subscribed(chat_id):
    """Check if a chat_id is already subscribed."""
    data = load_subscribers()
    for sub in data.get("subscribers", []):
        if sub.get("chat_id") == chat_id and sub.get("active", False):
            return True
    return False


def add_subscriber(chat_id, username):
    """Add a new subscriber."""
    data = load_subscribers()
    
    # Check if already subscribed
    for sub in data.get("subscribers", []):
        if sub.get("chat_id") == chat_id:
            if sub.get("active", False):
                return False  # Already active
            else:
                # Reactivate
                sub["active"] = True
                sub["resubscribed_at"] = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
                data["stats"]["total_subscribers"] = sum(1 for s in data["subscribers"] if s.get("active", False))
                save_subscribers(data)
                return True
    
    # Add new subscriber
    subscriber = {
        "chat_id": chat_id,
        "username": username or "Unknown",
        "subscribed_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
        "active": True
    }
    data["subscribers"].append(subscriber)
    data["stats"]["total_subscribers"] = sum(1 for s in data["subscribers"] if s.get("active", False))
    
    save_subscribers(data)
    return True


def remove_subscriber(chat_id):
    """Remove a subscriber (set to inactive)."""
    data = load_subscribers()
    
    for sub in data.get("subscribers", []):
        if sub.get("chat_id") == chat_id and sub.get("active", False):
            sub["active"] = False
            sub["unsubscribed_at"] = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
            data["stats"]["total_subscribers"] = sum(1 for s in data["subscribers"] if s.get("active", False))
            save_subscribers(data)
            return True
    
    return False


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command."""
    chat_id = update.effective_chat.id
    username = update.effective_user.username
    
    welcome_message = f"""
🔔 **Welcome to REO Dashboard Notifications!**

This bot sends you real-time alerts about:
• Oracle updates
• Indexer status changes
• Grace period expirations

📊 View the dashboard: {DASHBOARD_URL}

**Available Commands:**
/subscribe - Subscribe to notifications
/unsubscribe - Stop receiving notifications
/status - Check your subscription status
/stats - View bot statistics
/help - Show this help message

💡 **Tip:** Use /subscribe to get started!
"""
    
    await update.message.reply_text(welcome_message, parse_mode='Markdown')


async def subscribe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /subscribe command."""
    chat_id = update.effective_chat.id
    username = update.effective_user.username
    
    if is_subscribed(chat_id):
        await update.message.reply_text(
            "✅ You're already subscribed to notifications!\n\n"
            f"📊 View dashboard: {DASHBOARD_URL}\n"
            "Use /unsubscribe to stop receiving alerts."
        )
        return
    
    if add_subscriber(chat_id, username):
        await update.message.reply_text(
            "🎉 **Successfully subscribed!**\n\n"
            "You will now receive notifications about:\n"
            "• Oracle updates\n"
            "• Indexer status changes\n"
            "• Grace period expirations\n\n"
            f"📊 Dashboard: {DASHBOARD_URL}\n\n"
            "Use /unsubscribe anytime to stop receiving alerts.",
            parse_mode='Markdown'
        )
        logger.info(f"New subscriber: {chat_id} (@{username})")
    else:
        await update.message.reply_text(
            "❌ Failed to subscribe. Please try again later."
        )


async def unsubscribe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /unsubscribe command."""
    chat_id = update.effective_chat.id
    
    if not is_subscribed(chat_id):
        await update.message.reply_text(
            "ℹ️ You're not currently subscribed.\n\n"
            "Use /subscribe to start receiving notifications."
        )
        return
    
    if remove_subscriber(chat_id):
        await update.message.reply_text(
            "👋 **Successfully unsubscribed!**\n\n"
            "You will no longer receive notifications.\n\n"
            "You can subscribe again anytime using /subscribe.",
            parse_mode='Markdown'
        )
        logger.info(f"Unsubscribed: {chat_id}")
    else:
        await update.message.reply_text(
            "❌ Failed to unsubscribe. Please try again later."
        )


async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /status command."""
    chat_id = update.effective_chat.id
    username = update.effective_user.username
    
    if is_subscribed(chat_id):
        data = load_subscribers()
        for sub in data.get("subscribers", []):
            if sub.get("chat_id") == chat_id:
                subscribed_at = sub.get("subscribed_at", "Unknown")
                await update.message.reply_text(
                    f"✅ **Subscription Status: Active**\n\n"
                    f"👤 Username: @{username or 'Unknown'}\n"
                    f"📅 Subscribed: {subscribed_at}\n"
                    f"🔔 Receiving: Oracle & Status updates\n\n"
                    f"📊 Dashboard: {DASHBOARD_URL}",
                    parse_mode='Markdown'
                )
                return
    else:
        await update.message.reply_text(
            "❌ **Subscription Status: Not Active**\n\n"
            "Use /subscribe to start receiving notifications.",
            parse_mode='Markdown'
        )


async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /stats command."""
    data = load_subscribers()
    total_subs = data.get("stats", {}).get("total_subscribers", 0)
    total_notifs = data.get("stats", {}).get("total_notifications_sent", 0)
    
    await update.message.reply_text(
        f"📊 **Bot Statistics**\n\n"
        f"👥 Active Subscribers: {total_subs}\n"
        f"📤 Notifications Sent: {total_notifs}\n\n"
        f"🌐 Dashboard: {DASHBOARD_URL}",
        parse_mode='Markdown'
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command."""
    help_text = f"""
📖 **REO Dashboard Bot - Help**

**Available Commands:**

/start - Welcome message and introduction
/subscribe - Subscribe to notifications
/unsubscribe - Stop receiving notifications
/status - Check your subscription status
/stats - View bot statistics
/help - Show this help message

**What You'll Receive:**

🔔 **Oracle Updates** - When the eligibility oracle runs
📝 **Status Changes** - When indexers change status
⚠️ **Grace Periods** - When indexers enter/exit grace period
❌ **Ineligibility** - When indexers become ineligible

**Dashboard:**
{DASHBOARD_URL}

**About GIP-0079:**
This bot monitors the Indexer Rewards Eligibility Oracle that tracks which indexers are eligible for rewards based on their service quality.

Need help? Check the full documentation at the dashboard link above.
"""
    
    await update.message.reply_text(help_text, parse_mode='Markdown')


async def test(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /test command - sends a test notification."""
    chat_id = update.effective_chat.id
    
    if not is_subscribed(chat_id):
        await update.message.reply_text(
            "❌ You must be subscribed to test notifications.\n\n"
            "Use /subscribe first."
        )
        return
    
    test_message = f"""
🧪 **Test Notification**

This is a test message to confirm notifications are working correctly.

If you received this, you're all set! ✅

📊 Dashboard: {DASHBOARD_URL}
"""
    
    await update.message.reply_text(test_message, parse_mode='Markdown')
    logger.info(f"Test notification sent to: {chat_id}")


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle errors."""
    logger.error(f"Update {update} caused error {context.error}")


def main():
    """Start the bot."""
    if not TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN not found in environment variables!")
        print("❌ Error: TELEGRAM_BOT_TOKEN not set in .env file")
        return
    
    # Create the Application
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    # Register command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("subscribe", subscribe))
    application.add_handler(CommandHandler("unsubscribe", unsubscribe))
    application.add_handler(CommandHandler("status", status))
    application.add_handler(CommandHandler("stats", stats))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("test", test))
    
    # Register error handler
    application.add_error_handler(error_handler)
    
    # Start the bot
    logger.info("Starting REO Dashboard Telegram Bot...")
    print("✅ REO Dashboard Telegram Bot is running!")
    print("📱 Users can now subscribe by sending /start")
    print("🛑 Press Ctrl+C to stop the bot")
    
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()

