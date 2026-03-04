#!/usr/bin/env python3
import sys
import psycopg2
from psycopg2.extras import Json
from sentence_transformers import SentenceTransformer
import os

if len(sys.argv) < 2:
    print("Usage: add_single 'your thought' [category]")
    sys.exit(1)

content = sys.argv[1]
category = sys.argv[2] if len(sys.argv) > 2 else "general"

print(f"🔄 Adding: {content[:50]}...")
conn = psycopg2.connect(dbname='openbrain', user=os.getenv('USER'), host='localhost')
cur = conn.cursor()

model = SentenceTransformer('all-MiniLM-L6-v2')
embedding = model.encode(content).tolist()

cur.execute(
    "INSERT INTO memories (content, embedding, metadata) VALUES (%s, %s, %s)",
    (content, embedding, Json({"source": "manual", "category": category}))
)

conn.commit()
cur.close()
conn.close()
print("✅ Done!")
