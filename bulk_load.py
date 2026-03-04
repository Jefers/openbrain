#!/usr/bin/env python3
import psycopg2
from psycopg2.extras import Json
from sentence_transformers import SentenceTransformer
import os

# Connect to database
conn = psycopg2.connect(
    dbname="openbrain",
    user=os.getenv("USER"),
    host="localhost"
)
cur = conn.cursor()

# Load model
print("Loading embedding model...")
model = SentenceTransformer('all-MiniLM-L6-v2')
print("Model loaded!")

# Messages to insert
messages = [
    # Project Context & Decisions
    ("Project: Open Brain - A local, agent-readable memory system built with PostgreSQL + pgvector", "project"),
    ("Decision: Using all-MiniLM-L6-v2 for embeddings (384-dim) - good balance of speed/quality on MacBook Air", "decision"),
    ("Decision: Telegram for capture because it's lightweight, cross-platform, no new account needed", "decision"),
    ("Decision: Rejected Slack/Supabase/cloud services - prioritizing local control and open source", "decision"),
    ("Decision: Using passive bot (run manually) not always-on - matches my once-daily usage pattern", "decision"),
    ("Architecture: Thoughts → Telegram → Python bot (embeddings) → PostgreSQL → MCP server → AI tools", "architecture"),
    ("Location: All code in ~/LocalFile/openbrain/", "location"),
    
    # Workflow Preferences
    ("Working style: I prefer CLI tools and VS Code over dedicated apps", "preferences"),
    ("Working style: I value open source and local control over convenience", "preferences"),
    ("Working style: I'm a developer who spends lots of time in terminal and VS Code", "preferences"),
    ("Working style: I use many different AI models and need context to persist between them", "preferences"),
    ("Working style: I prefer nano for editing over cat/echo for large code blocks", "preferences"),
    ("Working style: I like tools that compound in value over time", "preferences"),
    ("Working style: I'm willing to invest setup time for long-term efficiency gains", "preferences"),
    
    # Technical Lessons
    ("Lesson: PostgreSQL 14 on Mac installs via Homebrew - need to start service with brew services", "lesson"),
    ("Lesson: pgvector extension must be installed separately after PostgreSQL", "lesson"),
    ("Lesson: Virtual environments (venv) are essential for Python package isolation", "lesson"),
    ("Lesson: Telegram bot tokens with ! need special handling (set +H in zsh)", "lesson"),
    ("Lesson: MCP servers use stdio protocol - they just sit there waiting for connections", "lesson"),
    ("Lesson: The all-MiniLM-L6-v2 model gives 384-dim embeddings - must match VECTOR(384) in DB", "lesson"),
    ("Lesson: PostgreSQL connection from Python: use os.getenv(\"USER\") for local Mac auth", "lesson"),
    
    # How-To Guides
    ("How-to: Check if PostgreSQL is running - brew services list | grep postgresql", "howto"),
    ("How-to: Connect to database - psql openbrain", "howto"),
    ("How-to: View recent memories - SELECT content, created_at FROM memories ORDER BY created_at DESC LIMIT 5;", "howto"),
    ("How-to: Run capture bot - cd ~/LocalFile/openbrain && source venv/bin/activate && python3 capture_bot_passive.py", "howto"),
    ("How-to: Start MCP server - cd ~/LocalFile/openbrain/mcp-server && node index.js", "howto"),
    ("How-to: Test database connection - python3 test_db.py", "howto"),
    ("How-to: Set Telegram token - export TELEGRAM_BOT_TOKEN='token' (with set +H first if it has !)", "howto"),
    
    # Project Roadmap
    ("Idea: Eventually build CLI tool \"brain\" with commands: search, recent, add, stats", "idea"),
    ("Idea: Could export memories to Obsidian for visual knowledge graph", "idea"),
    ("Idea: Future agents should query this brain automatically for context", "idea"),
    ("Idea: Might add metadata extraction using local LLM (Ollama) to tag people/topics", "idea"),
    ("Idea: Could build simple web interface with Flask for searching", "idea"),
    ("Idea: Would like MCP server to do real semantic search (currently keyword only)", "idea"),
    
    # Personal Context
    ("About me: Developer who values efficiency and hates repeating myself", "personal"),
    ("About me: Skeptical of corporate AI - prefer open source, local-first tools", "personal"),
    ("About me: Willing to invest time in systems that compound over time", "personal"),
    ("About me: I think in terms of workflows and architectures", "personal"),
    ("About me: I like understanding how things work, not just using them", "personal"),
    ("About me: I'm building Open Brain to solve context fragmentation across AI tools", "personal"),
    
    # Philosophy
    ("Why Open Brain: AI models forget between sessions. I don't want to repeat myself.", "philosophy"),
    ("Why local-first: My knowledge shouldn't be hostage to any company's business model.", "philosophy"),
    ("Why now: Agents are becoming mainstream - they need persistent memory to be useful.", "philosophy"),
    ("The goal: Every AI I use (Claude, GPT, Cursor, future agents) should know my context.", "philosophy"),
    ("The principle: Compounding advantage - every thought stored makes future interactions smarter.", "philosophy"),
]

print(f"Inserting {len(messages)} messages...")

for content, category in messages:
    # Generate embedding
    embedding = model.encode(content).tolist()
    
    # Insert
    cur.execute(
        "INSERT INTO memories (content, embedding, metadata) VALUES (%s, %s, %s)",
        (content, embedding, Json({"source": "bulk_load", "category": category}))
    )

conn.commit()
cur.close()
conn.close()

print("✅ Done! All messages inserted with embeddings.")
