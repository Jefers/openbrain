#!/bin/bash

# Test the Open Brain MCP server directly
echo "Testing Open Brain MCP Server..."
echo ""

# First, let's check if the server can start
cd mcp-server

echo "1. Starting MCP server in background..."
node index.js &
SERVER_PID=$!

# Give server time to start
sleep 2

echo "2. Server PID: $SERVER_PID"
echo "3. Checking if server is running..."
if ps -p $SERVER_PID > /dev/null; then
    echo "✅ Server is running"
else
    echo "❌ Server failed to start"
    exit 1
fi

echo ""
echo "4. Testing database connection via direct query..."
psql openbrain -c "SELECT COUNT(*) as total_memories, MAX(created_at) as latest_memory FROM memories;"

echo ""
echo "5. Showing recent memories from database:"
psql openbrain -c "SELECT id, LEFT(content, 50) as preview, created_at FROM memories ORDER BY created_at DESC LIMIT 3;"

echo ""
echo "6. Stopping MCP server..."
kill $SERVER_PID
wait $SERVER_PID 2>/dev/null

echo ""
echo "✅ Test completed successfully!"
echo ""
echo "Next steps for Continue.dev integration:"
echo "1. Check Continue.dev MCP configuration"
echo "2. Ensure the MCP server is in your PATH or configured with absolute path"
echo "3. Verify Continue.dev can spawn the server process"