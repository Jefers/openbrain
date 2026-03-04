import { spawn } from 'child_process';

const mcp = spawn('node', ['index.js']);

let messageId = 1;

function sendRequest(method, params = {}) {
  const request = {
    jsonrpc: '2.0',
    method: method,
    params: params,
    id: messageId++
  };
  mcp.stdin.write(JSON.stringify(request) + '\n');
}

mcp.stdout.on('data', (data) => {
  console.log('Response:', data.toString());
});

// Wait for server to start
setTimeout(() => {
  console.log('Requesting tools list...');
  sendRequest('tools/list');
}, 2000);

setTimeout(() => {
  console.log('Requesting recent memories...');
  sendRequest('tools/call', {
    name: 'recent_memories',
    arguments: { limit: 5 }
  });
}, 4000);

setTimeout(() => {
  mcp.kill();
}, 8000);
