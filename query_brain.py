#!/usr/bin/env python3
"""
Direct Open Brain Query Tool
Query your Open Brain database directly without MCP server
"""

import psycopg2
import sys
import os
from datetime import datetime, timedelta
import argparse

def get_db_connection():
    """Connect to the Open Brain database"""
    try:
        conn = psycopg2.connect(
            dbname="openbrain",
            user=os.getenv("USER"),
            host="localhost"
        )
        return conn
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        sys.exit(1)

def show_recent_memories(days=7, limit=10):
    """Show recent memories from the database"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute("""
            SELECT id, content, created_at 
            FROM memories 
            WHERE created_at > NOW() - %s::interval 
            ORDER BY created_at DESC 
            LIMIT %s
        """, (f"{days} days", limit))
        
        rows = cur.fetchall()
        
        if not rows:
            print(f"\n📝 No memories found in the last {days} days.")
            return
        
        print(f"\n📝 Recent Memories (last {days} days):")
        print("=" * 60)
        
        for i, (id, content, created_at) in enumerate(rows, 1):
            date_str = created_at.strftime("%Y-%m-%d %H:%M")
            print(f"\n{i}. [{date_str}] (ID: {id})")
            print(f"   {content[:100]}{'...' if len(content) > 100 else ''}")
        
        print(f"\n📊 Total: {len(rows)} memories")
        
    finally:
        cur.close()
        conn.close()

def search_memories(keyword, limit=10):
    """Search memories by keyword"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute("""
            SELECT id, content, created_at 
            FROM memories 
            WHERE content ILIKE %s 
            ORDER BY created_at DESC 
            LIMIT %s
        """, (f"%{keyword}%", limit))
        
        rows = cur.fetchall()
        
        if not rows:
            print(f'\n🔍 No memories found containing "{keyword}".')
            return
        
        print(f'\n🔍 Memories containing "{keyword}":')
        print("=" * 60)
        
        for i, (id, content, created_at) in enumerate(rows, 1):
            date_str = created_at.strftime("%Y-%m-%d %H:%M")
            
            # Highlight keyword in content
            highlighted = content.replace(
                keyword, f"\033[1;33m{keyword}\033[0m"
            ).replace(
                keyword.lower(), f"\033[1;33m{keyword.lower()}\033[0m"
            ).replace(
                keyword.upper(), f"\033[1;33m{keyword.upper()}\033[0m"
            )
            
            print(f"\n{i}. [{date_str}] (ID: {id})")
            print(f"   {highlighted[:100]}{'...' if len(highlighted) > 100 else ''}")
        
        print(f"\n📊 Total: {len(rows)} matches")
        
    finally:
        cur.close()
        conn.close()

def show_stats():
    """Show database statistics"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        # Total memories
        cur.execute("SELECT COUNT(*) FROM memories")
        total = cur.fetchone()[0]
        
        # Last week
        cur.execute("SELECT COUNT(*) FROM memories WHERE created_at > NOW() - INTERVAL '7 days'")
        last_week = cur.fetchone()[0]
        
        # Last month
        cur.execute("SELECT COUNT(*) FROM memories WHERE created_at > NOW() - INTERVAL '30 days'")
        last_month = cur.fetchone()[0]
        
        # Latest memory
        cur.execute("SELECT created_at FROM memories ORDER BY created_at DESC LIMIT 1")
        latest = cur.fetchone()
        
        print("\n📊 Open Brain Statistics")
        print("=" * 40)
        print(f"Total memories:      {total}")
        print(f"Last 7 days:         {last_week}")
        print(f"Last 30 days:        {last_month}")
        
        if latest:
            latest_date = latest[0].strftime("%Y-%m-%d %H:%M")
            print(f"Latest memory:       {latest_date}")
        else:
            print("Latest memory:       Never")
        
        # Show table info
        cur.execute("""
            SELECT 
                COUNT(*) as total,
                COUNT(embedding) as with_embeddings,
                COUNT(metadata) as with_metadata
            FROM memories
        """)
        table_stats = cur.fetchone()
        
        print(f"\n📈 Table Details:")
        print(f"Memories with embeddings: {table_stats[1]} ({table_stats[1]/total*100:.1f}%)")
        print(f"Memories with metadata:   {table_stats[2]} ({table_stats[2]/total*100:.1f}%)")
        
    finally:
        cur.close()
        conn.close()

def main():
    parser = argparse.ArgumentParser(description="Open Brain Query Tool")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Recent command
    recent_parser = subparsers.add_parser("recent", help="Show recent memories")
    recent_parser.add_argument("--days", type=int, default=7, help="Number of days to look back")
    recent_parser.add_argument("--limit", type=int, default=10, help="Maximum number of results")
    
    # Search command
    search_parser = subparsers.add_parser("search", help="Search memories by keyword")
    search_parser.add_argument("keyword", help="Keyword to search for")
    search_parser.add_argument("--limit", type=int, default=10, help="Maximum number of results")
    
    # Stats command
    subparsers.add_parser("stats", help="Show database statistics")
    
    # If no command, show recent memories
    if len(sys.argv) == 1:
        show_recent_memories()
        return
    
    args = parser.parse_args()
    
    if args.command == "recent":
        show_recent_memories(args.days, args.limit)
    elif args.command == "search":
        search_memories(args.keyword, args.limit)
    elif args.command == "stats":
        show_stats()
    else:
        parser.print_help()

if __name__ == "__main__":
    main()