#!/usr/bin/env python3
"""
Open Brain Telegram Bot - With Search Commands
Now you can query your brain from mobile!
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
from telegram.ext import CommandHandler
import asyncio

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
    """Handle incoming Telegram messages (store them)"""
    text = update.message.text
    if not text or text.startswith('/'):
        return

    logger.info(f"📥 Received: {text[:50]}...")

    try:
        # Generate embedding
        embedding = model.encode(text).tolist()
        
        # Metadata
        metadata = {
            "source": "telegram",
            "length": len(text),
            "has_question": "?" in text,
            "chat_id": update.message.chat_id,
            "message_id": update.message.message_id,
            "username": update.message.from_user.username,
            "first_name": update.message.from_user.first_name
        }
        
        # Store in database
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

async def search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Search your brain - usage: /search query here"""
    if not context.args:
        await update.message.reply_text("❌ Please provide a search query. Example: /search why am I building this system")
        return
    
    query = ' '.join(context.args)
    logger.info(f"🔍 Search request: {query}")
    
    try:
        # Generate embedding for query
        embedding = model.encode(query).tolist()
        
        # Search database
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT content, created_at, metadata->>'category',
                   (embedding <=> %s::vector) as distance
            FROM memories
            ORDER BY embedding <=> %s::vector ASC
            LIMIT 5
        """, (embedding, embedding))
        
        results = cur.fetchall()
        cur.close()
        conn.close()
        
        if not results:
            await update.message.reply_text("📭 No matches found.")
            return
        
        # Format results
        response = f"🔍 *Search results for:* _{query}_\n\n"
        for i, (content, created_at, category, distance) in enumerate(results, 1):
            similarity = 1 - distance
            date = created_at.strftime("%Y-%m-%d")
            # Truncate long content
            if len(content) > 200:
                content = content[:197] + "..."
            response += f"{i}. *[{category}]* ({similarity:.2f})\n{content}\n_{date}_\n\n"
        
        await update.message.reply_text(response, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"❌ Search error: {e}")
        await update.message.reply_text(f"❌ Search failed: {str(e)[:100]}")

async def recent(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show recent memories"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT content, created_at, metadata->>'category'
            FROM memories 
            ORDER BY created_at DESC 
            LIMIT 5
        """)
        results = cur.fetchall()
        cur.close()
        conn.close()
        
        if not results:
            await update.message.reply_text("📭 No memories yet.")
            return
        
        response = "📝 *Recent memories:*\n\n"
        for content, created_at, category in results:
            date = created_at.strftime("%Y-%m-%d %H:%M")
            if len(content) > 100:
                content = content[:97] + "..."
            response += f"• *[{category}]* {content}\n  _{date}_\n\n"
        
        await update.message.reply_text(response, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        await update.message.reply_text(f"❌ Failed: {str(e)[:100]}")

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show brain statistics"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM memories")
        total = cur.fetchone()[0]
        
        cur.execute("SELECT COUNT(*) FROM memories WHERE metadata->>'source' = 'telegram'")
        telegram = cur.fetchone()[0]
        
        cur.execute("SELECT COUNT(*) FROM memories WHERE metadata->>'source' = 'bulk_load'")
        bulk = cur.fetchone()[0]
        
        cur.execute("SELECT created_at FROM memories ORDER BY created_at DESC LIMIT 1")
        last = cur.fetchone()
        
        cur.close()
        conn.close()
        
        stats_msg = f"""
📊 *Open Brain Stats*
• Total memories: `{total}`
• From Telegram: `{telegram}`
• From bulk load: `{bulk}`
• Last capture: `{last[0] if last else 'Never'}`
        """
        await update.message.reply_text(stats_msg, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        await update.message.reply_text(f"❌ Failed: {str(e)[:100]}")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Welcome message"""
    welcome = """
🧠 *Open Brain Ready!*

I'm your personal memory system. Store thoughts and query them later.

*Commands:*
/search <query> - Search your memories
/recent - Show recent memories
/stats - Show database stats
/start - This message

*Examples:*
/search why am I building this system
/search thoughts about AI
/recent

Just send me any message and I'll store it automatically!
"""
    await update.message.reply_text(welcome, parse_mode='Markdown')

def main():
    """Start the bot"""
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        print("❌ ERROR: TELEGRAM_BOT_TOKEN not set!")
        return
    
    # Create application
    app = Application.builder().token(token).build()
    
    # Add handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("search", search))
    app.add_handler(CommandHandler("recent", recent))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("🤖 Bot running with search commands...")
    print("Commands: /search, /recent, /stats")
    app.run_polling()

if __name__ == "__main__":
    main()
