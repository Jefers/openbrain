#!/usr/bin/env python3
import sys
import psycopg2
from psycopg2.extras import Json
from sentence_transformers import SentenceTransformer
import os

if len(sys.argv) < 2:
    print("Usage: add_file filename.txt")
    print("File format: each line = content|category")
    sys.exit(1)

filename = sys.argv[1]
thoughts = []

with open(filename, 'r') as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith('#'):
            if '|' in line:
                content, category = line.split('|', 1)
                thoughts.append((content.strip(), category.strip()))
            else:
                thoughts.append((line, "general"))

print(f"📚 Loading {len(thoughts)} thoughts from {filename}...")
conn = psycopg2.connect(dbname='openbrain', user=os.getenv('USER'), host='localhost')
cur = conn.cursor()

model = SentenceTransformer('all-MiniLM-L6-v2')

for i, (content, category) in enumerate(thoughts, 1):
    embedding = model.encode(content).tolist()
    cur.execute(
        "INSERT INTO memories (content, embedding, metadata) VALUES (%s, %s, %s)",
        (content, embedding, Json({"source": "file", "category": category}))
    )
    print(f"  {i}. [{category}] {content[:50]}...")

conn.commit()
cur.close()
conn.close()
print(f"✅ Added {len(thoughts)} thoughts!")
