#!/usr/bin/env python3
import psycopg2
from psycopg2.extras import Json
from sentence_transformers import SentenceTransformer
import os

def add_thoughts(thoughts_list):
    conn = psycopg2.connect(dbname='openbrain', user=os.getenv('USER'), host='localhost')
    cur = conn.cursor()
    
    print("🔄 Loading model...")
    model = SentenceTransformer('all-MiniLM-L6-v2')
    
    for content, category in thoughts_list:
        embedding = model.encode(content).tolist()
        cur.execute(
            "INSERT INTO memories (content, embedding, metadata) VALUES (%s, %s, %s)",
            (content, embedding, Json({"source": "llm", "category": category}))
        )
        print(f"  Added: {content[:50]}...")
    
    conn.commit()
    cur.close()
    conn.close()
    print(f"✅ Added {len(thoughts_list)} thoughts")

# PASTE YOUR LLM-GENERATED LIST HERE:
thoughts = [
    # ("content", "category"),
]

if __name__ == "__main__":
    if len(thoughts) == 0:
        print("❌ No thoughts found! Edit this file and paste your LLM-generated list.")
    else:
        add_thoughts(thoughts)
