# Open Brain - Continue.dev MCP Integration Fix

## Problem
Continue.dev in VS Code not detecting the Open Brain MCP server despite it running correctly.

## Solution Approaches

### Option 1: Fix Continue.dev Configuration (Recommended)

Create or update `~/.continue/config.json`:

```json
{
  "allowAnonymousTelemetry": false,
  "models": [
    {
      "title": "Claude 3.5 Sonnet",
      "provider": "anthropic",
      "model": "claude-3-5-sonnet-20241022"
    }
  ],
  "tabAutocompleteModel": {
    "title": "Claude 3.5 Sonnet",
    "provider": "anthropic",
    "model": "claude-3-5-sonnet-20241022"
  },
  "experimental": {
    "mcpServers": {
      "openbrain": {
        "command": "node",
        "args": ["/Users/jeffgordon/LocalFile/openbrain/mcp-server/index.js"],
        "env": {
          "USER": "jeffgordon"
        }
      }
    }
  }
}
```

**Restart VS Code** after making this change.

### Option 2: Use Continue.dev's New MCP Format (v0.18+)

If the above doesn't work, try this format:

```json
{
  "mcpServers": {
    "openbrain": {
      "command": "node",
      "args": ["/Users/jeffgordon/LocalFile/openbrain/mcp-server/index.js"],
      "cwd": "/Users/jeffgordon/LocalFile/openbrain/mcp-server"
    }
  },
  "models": [
    {
      "title": "Claude 3.5 Sonnet",
      "provider": "anthropic",
      "model": "claude-3-5-sonnet-20241022"
    }
  ]
}
```

### Option 3: Create a Wrapper Script

Sometimes Continue.dev works better with a shell script wrapper:

Create `~/LocalFile/openbrain/mcp-server/start_mcp.sh`:
```bash
#!/bin/bash
cd /Users/jeffgordon/LocalFile/openbrain/mcp-server
node index.js
```

Make it executable:
```bash
chmod +x ~/LocalFile/openbrain/mcp-server/start_mcp.sh
```

Then in Continue config:
```json
{
  "mcpServers": {
    "openbrain": {
      "command": "/Users/jeffgordon/LocalFile/openbrain/mcp-server/start_mcp.sh"
    }
  }
}
```

## Alternative: Direct Python Integration (Skip MCP)

Since Continue.dev can run Python code directly, create a helper module:

### Step 1: Create Python Query Module

Create `~/LocalFile/openbrain/continue_helper.py`:
```python
import psycopg2
import os
import json
from datetime import datetime, timedelta

def get_recent_memories(days=7, limit=10):
    """Get recent memories for Continue.dev"""
    conn = psycopg2.connect(
        dbname="openbrain",
        user=os.getenv("USER"),
        host="localhost"
    )
    cur = conn.cursor()
    
    cur.execute("""
        SELECT content, created_at 
        FROM memories 
        WHERE created_at > NOW() - %s::interval 
        ORDER BY created_at DESC 
        LIMIT %s
    """, (f"{days} days", limit))
    
    results = []
    for content, created_at in cur.fetchall():
        results.append({
            "content": content,
            "date": created_at.strftime("%Y-%m-%d %H:%M")
        })
    
    cur.close()
    conn.close()
    
    return results

def search_memories(keyword, limit=10):
    """Search memories by keyword"""
    conn = psycopg2.connect(
        dbname="openbrain",
        user=os.getenv("USER"),
        host="localhost"
    )
    cur = conn.cursor()
    
    cur.execute("""
        SELECT content, created_at 
        FROM memories 
        WHERE content ILIKE %s 
        ORDER BY created_at DESC 
        LIMIT %s
    """, (f"%{keyword}%", limit))
    
    results = []
    for content, created_at in cur.fetchall():
        results.append({
            "content": content,
            "date": created_at.strftime("%Y-%m-%d %H:%M")
        })
    
    cur.close()
    conn.close()
    
    return results

def get_brain_stats():
    """Get brain statistics"""
    conn = psycopg2.connect(
        dbname="openbrain",
        user=os.getenv("USER"),
        host="localhost"
    )
    cur = conn.cursor()
    
    cur.execute("SELECT COUNT(*) FROM memories")
    total = cur.fetchone()[0]
    
    cur.execute("SELECT COUNT(*) FROM memories WHERE created_at > NOW() - INTERVAL '7 days'")
    last_week = cur.fetchone()[0]
    
    cur.execute("SELECT created_at FROM memories ORDER BY created_at DESC LIMIT 1")
    latest = cur.fetchone()
    
    cur.close()
    conn.close()
    
    return {
        "total_memories": total,
        "last_7_days": last_week,
        "latest_memory": latest[0].strftime("%Y-%m-%d %H:%M") if latest else "Never"
    }
```

### Step 2: Create Continue.dev Custom Commands

In Continue config, add custom commands:
```json
{
  "customCommands": [
    {
      "name": "brain-recent",
      "prompt": "Get recent memories from Open Brain. Use the Python helper to query the last 7 days.",
      "description": "Query recent Open Brain memories"
    },
    {
      "name": "brain-search",
      "prompt": "Search Open Brain memories for '{{input}}'. Use the Python helper to search by keyword.",
      "description": "Search Open Brain memories"
    },
    {
      "name": "brain-stats",
      "prompt": "Get Open Brain statistics. Use the Python helper to get counts and latest memory.",
      "description": "Get Open Brain statistics"
    }
  ]
}
```

## Alternative: Complete CLI Tool

Create a robust CLI tool that you can use from anywhere:

### Create `~/LocalFile/openbrain/brain`:
```bash
#!/bin/bash
# Open Brain CLI - Add to PATH or alias in .zshrc

OPENBRAIN_DIR="/Users/jeffgordon/LocalFile/openbrain"

case "$1" in
    "recent")
        psql openbrain -c "
            SELECT '[' || TO_CHAR(created_at, 'YYYY-MM-DD HH24:MI') || '] ' || 
                   LEFT(content, 100) || 
                   CASE WHEN LENGTH(content) > 100 THEN '...' ELSE '' END
            FROM memories 
            WHERE created_at > NOW() - INTERVAL '${2:-7} days'
            ORDER BY created_at DESC 
            LIMIT ${3:-10};
        " -t
        ;;
    "search")
        if [ -z "$2" ]; then
            echo "Usage: brain search <keyword> [limit]"
            exit 1
        fi
        psql openbrain -c "
            SELECT '[' || TO_CHAR(created_at, 'YYYY-MM-DD HH24:MI') || '] ' || 
                   content
            FROM memories 
            WHERE content ILIKE '%$2%'
            ORDER BY created_at DESC 
            LIMIT ${3:-10};
        " -t
        ;;
    "stats")
        echo "📊 Open Brain Statistics"
        echo "========================"
        psql openbrain -c "SELECT COUNT(*) as total FROM memories;" -t
        psql openbrain -c "SELECT COUNT(*) as last_week FROM memories WHERE created_at > NOW() - INTERVAL '7 days';" -t
        psql openbrain -c "SELECT TO_CHAR(created_at, 'YYYY-MM-DD HH24:MI') as latest FROM memories ORDER BY created_at DESC LIMIT 1;" -t
        ;;
    "add")
        if [ -z "$2" ]; then
            echo "Usage: brain add \"Your thought here\""
            exit 1
        fi
        cd "$OPENBRAIN_DIR"
        python3 -c "
import psycopg2, json, os, sys
conn = psycopg2.connect(dbname='openbrain', user=os.getenv('USER'), host='localhost')
cur = conn.cursor()
cur.execute('INSERT INTO memories (content) VALUES (%s) RETURNING id', (sys.argv[1],))
print(f'✅ Added memory with ID: {cur.fetchone()[0]}')
conn.commit()
cur.close()
conn.close()
        " "$2"
        ;;
    "help"|"")
        echo "Open Brain CLI"
        echo "=============="
        echo "Commands:"
        echo "  brain recent [days] [limit]  - Show recent memories"
        echo "  brain search <keyword> [limit] - Search memories"
        echo "  brain stats                  - Show statistics"
        echo "  brain add \"thought\"          - Add a memory"
        echo "  brain help                   - This help"
        ;;
    *)
        echo "Unknown command: $1"
        echo "Use 'brain help' for available commands"
        ;;
esac
```

Make it executable and add to PATH:
```bash
chmod +x ~/LocalFile/openbrain/brain
echo "alias brain='~/LocalFile/openbrain/brain'" >> ~/.zshrc
source ~/.zshrc
```

## Testing Steps

### 1. First, verify MCP server works standalone:
```bash
cd ~/LocalFile/openbrain/mcp-server
node index.js
# Should see: "✅ Connected to Open Brain database"
# Then: "🧠 Open Brain MCP server running on stdio"
```

### 2. Test database directly:
```bash
psql openbrain -c "SELECT COUNT(*) FROM memories;"
psql openbrain -c "SELECT content, created_at FROM memories ORDER BY created_at DESC LIMIT 3;"
```

### 3. Test Continue.dev integration:
1. Update Continue config with one of the formats above
2. Restart VS Code completely
3. Open Continue.dev sidebar
4. Try asking: "What are my recent memories?"
5. Or use `/brain-recent` if you set up custom commands

## Fallback: Simple Web Interface

If MCP continues to be problematic, create a minimal web interface:

```python
# ~/LocalFile/openbrain/web_interface.py
from flask import Flask, jsonify, request
import psycopg2
import os

app = Flask(__name__)

def get_db():
    return psycopg2.connect(
        dbname="openbrain",
        user=os.getenv("USER"),
        host="localhost"
    )

@app.route('/api/memories/recent')
def recent_memories():
    days = request.args.get('days', 7, type=int)
    limit = request.args.get('limit', 10, type=int)
    
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, content, created_at 
        FROM memories 
        WHERE created_at > NOW() - %s::interval 
        ORDER BY created_at DESC 
        LIMIT %s
    """, (f"{days} days", limit))
    
    results = []
    for row in cur.fetchall():
        results.append({
            "id": row[0],
            "content": row[1],
            "created_at": row[2].isoformat()
        })
    
    cur.close()
    conn.close()
    return jsonify(results)

if __name__ == '__main__':
    app.run(port=5001, debug=True)
```

Run with:
```bash
cd ~/LocalFile/openbrain
python3 web_interface.py
# Access at http://localhost:5001/api/memories/recent
```

## Immediate Next Steps

1. **Try Option 1 first** - Update Continue config with the experimental MCP format
2. **Restart VS Code completely** - Not just reload, full restart
3. **Check Continue.dev logs** - Look for MCP-related errors
4. **Test with CLI tool** - Use the `brain` command as backup
5. **Add more test data** - Use Telegram bot to add real thoughts

## Long-term Vision Alignment

Your system already achieves the core goals:
- ✅ **Local control** - Everything runs on your MacBook
- ✅ **Open source** - All components are open source
- ✅ **Portable** - PostgreSQL database can be backed up/restored
- ✅ **AI-accessible** - MCP protocol is standard for AI tools

Once Continue.dev integration works, you'll have:
- Claude in VS Code accessing your full memory
- Future AI agents can use the same MCP interface
- No need to re-explain context to new chats
- Permanent storage of thoughts/decisions/learnings

## Troubleshooting Tips

If Continue.dev still doesn't work:

1. **Check Continue.dev version**: Ensure you're on v0.18+ which has better MCP support
2. **Look at VS Code developer console**: `Help → Toggle Developer Tools → Console`
3. **Check for MCP errors**: Look for "MCP" or "openbrain" in console logs
4. **Try different MCP server examples**: Continue.dev docs have working examples
5. **Join Continue.dev Discord**: Ask in #mcp channel for specific help

Remember: The **CLI tool** (`brain` command) gives you immediate access while debugging Continue integration.