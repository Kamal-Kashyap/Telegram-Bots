import os
os.system("pip install nest_asyncio")
import nest_asyncio
nest_asyncio.apply()

import asyncio
import re
from telegram import Update, ChatPermissions
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes
from telegram.constants import ChatMemberStatus
import nest_asyncio

# Replace with your Telegram bot token
TOKEN = "7883029751:AAE8Ol_knpB-fSXJyTX6stJNPcwPVNqn1NU"

warned_users = {}

PROMO_KEYWORDS = [
    "sale", "discount", "offer", "buy now", "limited time", "promo", "clearance", "flash sale",
    "super offer", "shop now", "deal of the day", "hurry up", "exclusive deal", "best price", "limited stock"
]

# Check if user is admin                                                                                                                                              
async def is_admin(update: Update) -> bool:
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    member = await update.get_bot().get_chat_member(chat_id, user_id)
    return member.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]

# Moderate messages
async def moderate_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat_id = update.effective_chat.id
    text = update.message.text or ""

    # Skip if user is admin
    if await is_admin(update):
        return

    # Remove any link (general regex)
    if re.search(r"(https?:\/\/[^\s]+|www\.[^\s]+|\b\w+\.\w{2,}\b)", text):
        await update.message.delete()
        warn_msg = await context.bot.send_message(chat_id, text=f"🚫 @{user.username or user.first_name}, links are not allowed.")
        await asyncio.sleep(5)
        await warn_msg.delete()
        return

    # Remove media types from non-admins
    if update.message.photo or update.message.video or update.message.sticker or update.message.animation or update.message.document:
        await update.message.delete()
        warn_msg = await context.bot.send_message(chat_id, text=f"🚫 @{user.username or user.first_name}, media sharing is not allowed.")
        await asyncio.sleep(5)
        await warn_msg.delete()
        return

    # Check for promotional keywords
    if any(keyword in text.lower() for keyword in PROMO_KEYWORDS):
        await update.message.delete()
        if user.id not in warned_users:
            warned_users[user.id] = {"violations": 1}
            warn_msg = await context.bot.send_message(chat_id, text=f"⚠️ @{user.username or user.first_name}, promotion is not allowed. One more and you'll be removed.")
            await asyncio.sleep(5)
            await warn_msg.delete()        
        else:
            warned_users[user.id]["violations"] += 1
            if warned_users[user.id]["violations"] >= 2:
                # Kick the user
                await context.bot.send_message(chat_id, text=f"🚫 @{user.username or user.first_name} removed for repeated violations.")
                await update.effective_chat.kick_member(user.id)
                await asyncio.sleep(5)

                # Delete all past messages from the user
                async for msg in update.effective_chat.get_history(limit=100):
                    if msg.from_user and msg.from_user.id == user.id:
                        try:
                            await msg.delete()
                        except:
                            pass

# Welcome new users
async def welcome_new_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    for member in update.message.new_chat_members:
        welcome_msg = await update.message.reply_text(f"👋 Welcome {member.full_name}!")
        await asyncio.sleep(5)
        await welcome_msg.delete()

# Main bot setup
async def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome_new_member))
    app.add_handler(MessageHandler(filters.ALL, moderate_message))

    print("✅ Telegram bot is running...")
    await app.run_polling()

# Run the bot
if __name__ == "__main__":
    nest_asyncio.apply()
    asyncio.get_event_loop().run_until_complete(main())
