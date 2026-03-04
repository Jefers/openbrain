#!/usr/bin/env python3
"""
Open Brain Telegram Capture Bot
Stores thoughts locally with embeddings for semantic search
"""

import os
import sys
import json
import logging
import psycopg2
from psycopg2.extras import Json
from sentence_transformers import SentenceTransformer
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes

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

# Load embedding model (do this once at startup)
print("🔄 Loading embedding model (this may take a moment the first time)...")
try:
    model = SentenceTransformer('all-MiniLM-L6-v2')
    print("✅ Model loaded successfully!")
except Exception as e:
    logger.error(f"Failed to load model: {e}")
    sys.exit(1)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle incoming Telegram messages"""
    text = update.message.text
    if not text:
        return

    logger.info(f"📥 Received: {text[:50]}...")

    try:
        # Generate embedding
        embedding = model.encode(text).tolist()

        # Simple metadata
        metadata = {
            "source": "telegram",
            "length": len(text),
            "has_question": "?" in text,
            "chat_id": update.message.chat_id,
            "message_id": update.message.message_id,
            "username": update.message.from_user.username,
            "first_name": update.message.from_user.first_name
        }

        # Store in database (create new connection for each message)
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
    """Send a welcome message when /start is issued"""
    welcome = """
🧠 **Open Brain Ready!**

Send me any thought, idea, or note. I'll store it with embeddings so your AI agents can find it later by meaning, not just keywords.

**Examples:**
• "Just had an idea for a new project about renewable energy"
• "Meeting with Sarah - she mentioned she's unhappy with her current role"
• "Decision: Going to focus on learning Rust this quarter"

**Commands:**
/start - Show this message
/stats - Show database stats
/recent - Show last 5 thoughts

Try sending something now!
"""
    await update.message.reply_text(welcome, parse_mode='Markdown')

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show database statistics"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Get total count
        cur.execute("SELECT COUNT(*) FROM memories")
        total = cur.fetchone()[0]
        
        # Get last entry time
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
        await update.message.reply_text(f"❌ Error getting stats: {e}")

async def recent(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show recent thoughts"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT content, created_at FROM memories ORDER BY created_at DESC LIMIT 5")
        rows = cur.fetchall()
        cur.close()
        conn.close()
        
        if not rows:
            await update.message.reply_text("No memories yet. Start sending thoughts!")
            return
        
        msg = "📝 **Recent thoughts:**\n\n"
        for i, (content, created_at) in enumerate(rows, 1):
            # Truncate long messages
            if len(content) > 100:
                content = content[:97] + "..."
            msg += f"{i}. {content}\n   _{created_at.strftime('%Y-%m-%d %H:%M')}_\n\n"
        
        await update.message.reply_text(msg, parse_mode='Markdown')
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")

def main():
    """Start the bot"""
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        print("\n❌ ERROR: TELEGRAM_BOT_TOKEN environment variable not set!")
        print("\nTo fix this, either:")
        print("1. Set it in your terminal:")
        print("   export TELEGRAM_BOT_TOKEN='your_token_here'")
        print("\n2. Or add it to your shell profile (~/.zshrc):")
        print("   echo 'export TELEGRAM_BOT_TOKEN=\"your_token_here\"' >> ~/.zshrc")
        print("   source ~/.zshrc")
        return

    # Create application
    app = Application.builder().token(token).build()

    # Add handlers
    app.add_handler(MessageHandler(filters.COMMAND & filters.Regex('^/start$'), start))
    app.add_handler(MessageHandler(filters.COMMAND & filters.Regex('^/stats$'), stats))
    app.add_handler(MessageHandler(filters.COMMAND & filters.Regex('^/recent$'), recent))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("🤖 Bot is running... Send messages to your Telegram bot to capture thoughts.")
    print("Press Ctrl+C to stop")
    app.run_polling()

if __name__ == "__main__":
    main()
