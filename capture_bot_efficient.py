#!/usr/bin/env python3
"""
Open Brain Telegram Capture Bot - Efficient version
Lower polling frequency for laptop use
"""

import os
import sys
import json
import logging
import time
import psycopg2
from psycopg2.extras import Json
from sentence_transformers import SentenceTransformer
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
from telegram.ext import ApplicationBuilder
from telegram.request import HTTPXRequest

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Database connection
def get_db_connection():
    try:
        conn = psycopg2.connect(
            dbname="openbrain",
            user=os.getenv("USER"),
            host="localhost"
        )
        return conn
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        sys.exit(1)

# Load embedding model
print("🔄 Loading embedding model...")
try:
    model = SentenceTransformer('all-MiniLM-L6-v2')
    print("✅ Model loaded successfully!")
except Exception as e:
    logger.error(f"Failed to load model: {e}")
    sys.exit(1)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if not text:
        return

    logger.info(f"📥 Received: {text[:50]}...")

    try:
        embedding = model.encode(text).tolist()
        metadata = {
            "source": "telegram",
            "length": len(text),
            "has_question": "?" in text,
            "chat_id": update.message.chat_id,
            "message_id": update.message.message_id,
            "username": update.message.from_user.username,
            "first_name": update.message.from_user.first_name
        }

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO memories (content, embedding, metadata) VALUES (%s, %s, %s)",
            (text, embedding, Json(metadata))
        )
        conn.commit()
        cur.close()
        conn.close()

        await update.message.reply_text("✅ Thought captured.")
        logger.info("✅ Stored successfully")

    except Exception as e:
        logger.error(f"❌ Error: {e}")
        await update.message.reply_text("❌ Failed to capture. Check logs.")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome = """
🧠 **Open Brain Ready!**

Send me any thought, idea, or note. I'll store it with embeddings.

**Commands:**
/start - Show this message
/stats - Show database stats
/recent - Show last 5 thoughts
/health - Check if bot is running

Try sending something now!
"""
    await update.message.reply_text(welcome, parse_mode='Markdown')

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM memories")
        total = cur.fetchone()[0]
        cur.execute("SELECT created_at FROM memories ORDER BY created_at DESC LIMIT 1")
        last = cur.fetchone()
        cur.close()
        conn.close()
        
        stats_msg = f"""
📊 **Database Stats**
• Total memories: `{total}`
• Last capture: `{last[0] if last else 'Never'}`
        """
        await update.message.reply_text(stats_msg, parse_mode='Markdown')
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")

async def recent(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT content, created_at FROM memories ORDER BY created_at DESC LIMIT 5")
        rows = cur.fetchall()
        cur.close()
        conn.close()
        
        if not rows:
            await update.message.reply_text("No memories yet.")
            return
        
        msg = "📝 **Recent thoughts:**\n\n"
        for i, (content, created_at) in enumerate(rows, 1):
            if len(content) > 100:
                content = content[:97] + "..."
            msg += f"{i}. {content}\n   _{created_at.strftime('%Y-%m-%d %H:%M')}_\n\n"
        
        await update.message.reply_text(msg, parse_mode='Markdown')
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")

async def health(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Bot is running efficiently!")

def main():
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        print("❌ ERROR: TELEGRAM_BOT_TOKEN not set!")
        return

    # Create a custom request with longer timeout and less frequent polling
    request = HTTPXRequest(connect_timeout=30, read_timeout=30, write_timeout=30)
    
    # Build application with custom request
    app = ApplicationBuilder().token(token).request(request).build()
    
    # Add handlers
    app.add_handler(MessageHandler(filters.COMMAND & filters.Regex('^/start$'), start))
    app.add_handler(MessageHandler(filters.COMMAND & filters.Regex('^/stats$'), stats))
    app.add_handler(MessageHandler(filters.COMMAND & filters.Regex('^/recent$'), recent))
    app.add_handler(MessageHandler(filters.COMMAND & filters.Regex('^/health$'), health))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("🤖 Bot running efficiently...")
    print("It will only use CPU when messages arrive.")
    print("Press Ctrl+C to stop")
    
    # This will use long polling efficiently
    app.run_polling()

if __name__ == "__main__":
    main()
