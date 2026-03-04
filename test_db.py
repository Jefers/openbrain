import psycopg2
import json
import os
from datetime import datetime

# Connect to database
try:
    conn = psycopg2.connect(
        dbname="openbrain",
        user=os.getenv("USER"),
        host="localhost"
    )
    print("✅ Connected to database successfully")
    
    # Test insert
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO memories (content, metadata) 
        VALUES (%s, %s) RETURNING id
    """, ("Test entry", json.dumps({"test": True, "timestamp": str(datetime.now())})))
    conn.commit()
    inserted_id = cur.fetchone()[0]
    print(f"✅ Inserted test entry with ID: {inserted_id}")
    
    # Test query
    cur.execute("SELECT id, content, created_at FROM memories ORDER BY created_at DESC LIMIT 5")
    rows = cur.fetchall()
    print(f"\n📝 Last {len(rows)} entries in database:")
    for row in rows:
        print(f"  ID: {row[0]} | {row[1][:50]}... (at {row[2]})")
    
    cur.close()
    conn.close()
    print("\n✅ All tests passed!")
    
except Exception as e:
    print(f"❌ Error: {e}")
