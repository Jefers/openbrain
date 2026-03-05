#!/usr/bin/env python3
"""
Add thoughts to Open Brain
Usage: add_thoughts "content" "category"
   or: add_thoughts --file filename.txt (one thought per line, format: content|category)
"""

import psycopg2
from psycopg2.extras import Json
from sentence_transformers import SentenceTransformer
import os
import sys
import argparse

def add_single_thought(content, category="general"):
    """Add a single thought to the database"""
    
    # Connect to database
    conn = psycopg2.connect(
        dbname="openbrain",
        user=os.getenv("USER"),
        host="localhost"
    )
    cur = conn.cursor()
    
    # Load model (first time might be slow)
    print("🔄 Loading embedding model...", end="", flush=True)
    model = SentenceTransformer('all-MiniLM-L6-v2')
    print("✅")
    
    # Generate embedding
    embedding = model.encode(content).tolist()
    
    # Insert
    cur.execute(
        "INSERT INTO memories (content, embedding, metadata) VALUES (%s, %s, %s)",
        (content, embedding, Json({
            "source": "manual",
            "category": category
        }))
    )
    
    conn.commit()
    cur.close()
    conn.close()
    print(f"✅ Added [{category}]: {content[:50]}...")

def add_from_file(filename):
    """Add thoughts from a file (format: content|category per line)"""
    with open(filename, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                if '|' in line:
                    content, category = line.split('|', 1)
                    add_single_thought(content.strip(), category.strip())
                else:
                    add_single_thought(line, "general")

def add_bulk(thoughts_list):
    """Add a list of (content, category) tuples"""
    conn = psycopg2.connect(
        dbname="openbrain",
        user=os.getenv("USER"),
        host="localhost"
    )
    cur = conn.cursor()
    
    print("🔄 Loading embedding model...", end="", flush=True)
    model = SentenceTransformer('all-MiniLM-L6-v2')
    print("✅")
    
    for content, category in thoughts_list:
        embedding = model.encode(content).tolist()
        cur.execute(
            "INSERT INTO memories (content, embedding, metadata) VALUES (%s, %s, %s)",
            (content, embedding, Json({"source": "bulk", "category": category}))
        )
        print(f"  ✅ [{category}] {content[:50]}...")
    
    conn.commit()
    cur.close()
    conn.close()
    print(f"\n✅ Added {len(thoughts_list)} thoughts!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Add thoughts to Open Brain')
    parser.add_argument('content', nargs='?', help='Thought content')
    parser.add_argument('category', nargs='?', default='general', help='Thought category')
    parser.add_argument('--file', '-f', help='File with thoughts (format: content|category per line)')
    parser.add_argument('--bulk', '-b', help='Python-style list of tuples (for advanced use)')
    
    args = parser.parse_args()
    
    if args.file:
        add_from_file(args.file)
    elif args.content:
        add_single_thought(args.content, args.category)
    else:
        print("Usage:")
        print("  add_thoughts 'content' 'category'")
        print("  add_thoughts --file thoughts.txt")
        print("\nFile format (thoughts.txt):")
        print("  This is a thought|category")
        print("  Another thought|lesson")
        sys.exit(1)
