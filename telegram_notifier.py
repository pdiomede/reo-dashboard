#!/usr/bin/env python3
"""
Telegram Notifier for REO Dashboard
Sends notifications to all subscribed users about oracle updates and status changes.
"""

import json
import os
import logging
from datetime import datetime
import asyncio
from telegram import Bot
from telegram.error import TelegramError
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
SUBSCRIBERS_FILE = 'subscribers_telegram.json'
ACTIVITY_LOG_FILE = 'activity_log_indexers_status_changes.json'
ACTIVE_INDEXERS_FILE = 'active_indexers.json'
DASHBOARD_URL = 'http://dashboards.thegraph.foundation/reo/'

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


def load_subscribers():
    """Load active subscribers from JSON file."""
    if not os.path.exists(SUBSCRIBERS_FILE):
        return []
    
    try:
        with open(SUBSCRIBERS_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            # Return only active subscribers
            return [sub for sub in data.get("subscribers", []) if sub.get("active", False)]
    except Exception as e:
        logger.error(f"Error loading subscribers: {e}")
        return []


def load_activity_log():
    """Load activity log to check for status changes."""
    if not os.path.exists(ACTIVITY_LOG_FILE):
        return None
    
    try:
        with open(ACTIVITY_LOG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading activity log: {e}")
        return None


def load_active_indexers():
    """Load active indexers data."""
    if not os.path.exists(ACTIVE_INDEXERS_FILE):
        return None
    
    try:
        with open(ACTIVE_INDEXERS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading active indexers: {e}")
        return None


def update_notification_stats():
    """Update the notification counter in subscribers file."""
    try:
        if not os.path.exists(SUBSCRIBERS_FILE):
            return
        
        with open(SUBSCRIBERS_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        data["stats"]["total_notifications_sent"] = data.get("stats", {}).get("total_notifications_sent", 0) + 1
        
        with open(SUBSCRIBERS_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.error(f"Error updating notification stats: {e}")


def format_oracle_update_message(indexers_data, activity_log):
    """Format the oracle update notification message."""
    metadata = indexers_data.get("metadata", {})
    last_check = metadata.get("last_check", "Unknown")
    last_oracle_update = metadata.get("last_oracle_update_time", "Unknown")
    
    indexers = indexers_data.get("indexers", [])
    total_indexers = len(indexers)
    eligible_count = sum(1 for idx in indexers if idx.get("status") == "eligible")
    grace_count = sum(1 for idx in indexers if idx.get("status") == "grace")
    ineligible_count = sum(1 for idx in indexers if idx.get("status") == "ineligible")
    
    # Check for status changes
    status_changes = activity_log.get("status_changes", []) if activity_log else []
    has_changes = len(status_changes) > 0
    
    # Build message
    message = "🔔 **Oracle Update Detected!**\n"
    message += "━━━━━━━━━━━━━━━━━━━\n"
    message += f"**Update Time:** {last_check}\n"
    message += f"**Oracle Timestamp:** {last_oracle_update}\n\n"
    
    message += "📊 **Dashboard Stats:**\n"
    message += f"• Total Indexers: **{total_indexers}**\n"
    message += f"• Eligible: **{eligible_count}** ✅\n"
    message += f"• Grace Period: **{grace_count}** ⚠️\n"
    message += f"• Ineligible: **{ineligible_count}** ❌\n\n"
    
    if has_changes:
        # Count changes by type
        to_eligible = sum(1 for c in status_changes if c.get("new_status") == "eligible")
        to_grace = sum(1 for c in status_changes if c.get("new_status") == "grace")
        to_ineligible = sum(1 for c in status_changes if c.get("new_status") == "ineligible")
        
        message += "📝 **Status Changes Detected:**\n"
        if to_eligible > 0:
            message += f"• {to_eligible} indexer(s) → **eligible** ✅\n"
        if to_grace > 0:
            message += f"• {to_grace} indexer(s) → **grace period** ⚠️\n"
        if to_ineligible > 0:
            message += f"• {to_ineligible} indexer(s) → **ineligible** ❌\n"
        message += "\n"
    else:
        message += "ℹ️ **No Status Changes**\n"
        message += "All indexers maintained their status.\n\n"
    
    message += f"🔍 [View Full Dashboard]({DASHBOARD_URL})"
    
    return message


def format_detailed_changes_message(activity_log, indexers_data):
    """Format a detailed message about status changes."""
    status_changes = activity_log.get("status_changes", [])
    
    if not status_changes:
        return None
    
    # Group changes by new status
    to_eligible = [c for c in status_changes if c.get("new_status") == "eligible"]
    to_grace = [c for c in status_changes if c.get("new_status") == "grace"]
    to_ineligible = [c for c in status_changes if c.get("new_status") == "ineligible"]
    
    message = "📝 **Detailed Status Changes**\n"
    message += "━━━━━━━━━━━━━━━━━━━\n\n"
    
    # Helper function to get indexer ENS name
    def get_ens_name(address):
        indexers = indexers_data.get("indexers", [])
        for idx in indexers:
            if idx.get("address", "").lower() == address.lower():
                # Check if there's an ENS name in the indexer data
                # Note: ENS is loaded separately, but we can show address for now
                return address[:10] + "..." + address[-6:]
        return address[:10] + "..." + address[-6:]
    
    # Helper function to get eligible_until for grace period
    def get_eligible_until(address):
        indexers = indexers_data.get("indexers", [])
        for idx in indexers:
            if idx.get("address", "").lower() == address.lower():
                return idx.get("eligible_until_readable", "")
        return ""
    
    if to_eligible:
        message += f"✅ **Became Eligible ({len(to_eligible)}):**\n"
        for change in to_eligible[:5]:  # Limit to 5 to avoid message being too long
            addr = get_ens_name(change.get("address", ""))
            prev = change.get("previous_status", "unknown")
            message += f"• `{addr}` ({prev} → eligible)\n"
        if len(to_eligible) > 5:
            message += f"• ... and {len(to_eligible) - 5} more\n"
        message += "\n"
    
    if to_grace:
        message += f"⚠️ **Entered Grace Period ({len(to_grace)}):**\n"
        for change in to_grace[:5]:
            addr = get_ens_name(change.get("address", ""))
            prev = change.get("previous_status", "unknown")
            eligible_until = get_eligible_until(change.get("address", ""))
            message += f"• `{addr}` ({prev} → grace)\n"
            if eligible_until:
                message += f"  Expires: {eligible_until}\n"
        if len(to_grace) > 5:
            message += f"• ... and {len(to_grace) - 5} more\n"
        message += "\n"
    
    if to_ineligible:
        message += f"❌ **Became Ineligible ({len(to_ineligible)}):**\n"
        for change in to_ineligible[:5]:
            addr = get_ens_name(change.get("address", ""))
            prev = change.get("previous_status", "unknown")
            message += f"• `{addr}` ({prev} → ineligible)\n"
        if len(to_ineligible) > 5:
            message += f"• ... and {len(to_ineligible) - 5} more\n"
        message += "\n"
    
    message += f"📄 [Full Report]({DASHBOARD_URL})"
    
    return message


async def send_notification_to_subscriber(bot, chat_id, message):
    """Send a notification to a single subscriber."""
    try:
        await bot.send_message(
            chat_id=chat_id,
            text=message,
            parse_mode='Markdown',
            disable_web_page_preview=True
        )
        return True
    except TelegramError as e:
        logger.error(f"Failed to send message to {chat_id}: {e}")
        return False


async def send_notifications_async():
    """Send notifications to all subscribers (async)."""
    # Check if bot token is set
    if not TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN not found in environment variables!")
        print("⚠ Telegram notifications skipped: TELEGRAM_BOT_TOKEN not set")
        return False
    
    # Load subscribers
    subscribers = load_subscribers()
    if not subscribers:
        logger.info("No active subscribers. Skipping notifications.")
        print("ℹ️ No active Telegram subscribers")
        return False
    
    # Load data
    activity_log = load_activity_log()
    indexers_data = load_active_indexers()
    
    if not indexers_data:
        logger.error("Could not load active indexers data")
        print("⚠ Could not load indexers data for notifications")
        return False
    
    # Format messages
    oracle_message = format_oracle_update_message(indexers_data, activity_log)
    
    # Check if there are status changes for detailed message
    status_changes = activity_log.get("status_changes", []) if activity_log else []
    detailed_message = None
    if status_changes:
        detailed_message = format_detailed_changes_message(activity_log, indexers_data)
    
    # Create bot instance
    bot = Bot(token=TELEGRAM_BOT_TOKEN)
    
    # Send notifications
    success_count = 0
    fail_count = 0
    
    print(f"📤 Sending Telegram notifications to {len(subscribers)} subscriber(s)...")
    
    for subscriber in subscribers:
        chat_id = subscriber.get("chat_id")
        if not chat_id:
            continue
        
        try:
            # Send oracle update message
            if await send_notification_to_subscriber(bot, chat_id, oracle_message):
                success_count += 1
                
                # Send detailed changes if available (with small delay)
                if detailed_message:
                    await asyncio.sleep(0.5)  # Small delay between messages
                    await send_notification_to_subscriber(bot, chat_id, detailed_message)
            else:
                fail_count += 1
            
            # Small delay to avoid rate limiting
            await asyncio.sleep(0.1)
            
        except Exception as e:
            logger.error(f"Error sending to {chat_id}: {e}")
            fail_count += 1
    
    # Update stats
    if success_count > 0:
        update_notification_stats()
    
    print(f"✅ Telegram notifications sent: {success_count} successful, {fail_count} failed")
    logger.info(f"Notifications sent: {success_count} successful, {fail_count} failed")
    
    return success_count > 0


def send_notifications():
    """Send notifications to all subscribers (wrapper function)."""
    try:
        # Run async function
        return asyncio.run(send_notifications_async())
    except Exception as e:
        logger.error(f"Error in send_notifications: {e}")
        print(f"⚠ Error sending Telegram notifications: {e}")
        return False


if __name__ == '__main__':
    # For testing purposes
    print("Testing Telegram notifications...")
    send_notifications()

