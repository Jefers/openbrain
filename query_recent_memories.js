#!/usr/bin/env node

// Simple test to query the MCP server for recent memories
// This simulates what an MCP client would do

const { spawn } = require('child_process');
const readline = require('readline');

// Create a child process for the MCP server
const server = spawn('node', ['mcp-server/index.js'], {
  stdio: ['pipe', 'pipe', 'inherit']
});

// Set up readline for reading server output
const rl = readline.createInterface({
  input: server.stdout,
  terminal: false
});

// Buffer for server responses
let responseBuffer = '';
let inResponse = false;

// Send a request to the server
function sendRequest(request) {
  const requestStr = JSON.stringify(request) + '\n';
  console.log('Sending request:', requestStr);
  server.stdin.write(requestStr);
}

// Listen for responses
rl.on('line', (line) => {
  try {
    const data = JSON.parse(line);
    
    if (data.type === 'response') {
      console.log('\n=== Server Response ===');
      console.log(JSON.stringify(data, null, 2));
      
      if (data.result && data.result.content) {
        console.log('\n=== Formatted Output ===');
        data.result.content.forEach(content => {
          if (content.type === 'text') {
            console.log(content.text);
          }
        });
      }
      
      // Close after getting response
      setTimeout(() => {
        server.kill();
        process.exit(0);
      }, 1000);
    }
  } catch (e) {
    // Not JSON, probably log output
    if (line.includes('Connected to Open Brain database') || 
        line.includes('Open Brain MCP server running')) {
      console.log('Server:', line);
      
      // Send request after server is ready
      setTimeout(() => {
        // Request recent memories from the last 7 days
        sendRequest({
          type: 'request',
          id: '1',
          method: 'tools/call',
          params: {
            name: 'recent_memories',
            arguments: {
              days: 7,
              limit: 10
            }
          }
        });
      }, 1000);
    }
  }
});

// Handle server errors
server.on('error', (err) => {
  console.error('Server error:', err);
  process.exit(1);
});

// Handle server exit
server.on('close', (code) => {
  console.log(`Server exited with code ${code}`);
  process.exit(code);
});

// Start the process
console.log('Starting MCP server test...');