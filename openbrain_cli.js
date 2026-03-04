#!/usr/bin/env node

/**
 * Open Brain CLI Tool
 * Query your Open Brain directly from command line
 */

const { spawn } = require('child_process');
const readline = require('readline');

class OpenBrainCLI {
  constructor() {
    this.server = null;
    this.requestId = 1;
  }

  async startServer() {
    return new Promise((resolve, reject) => {
      console.log('🚀 Starting Open Brain MCP server...');
      
      this.server = spawn('node', ['mcp-server/index.js'], {
        stdio: ['pipe', 'pipe', 'inherit'],
        cwd: process.cwd()
      });

      const rl = readline.createInterface({
        input: this.server.stdout,
        terminal: false
      });

      rl.on('line', (line) => {
        if (line.includes('✅ Connected to Open Brain database')) {
          console.log('✅ Server ready');
          resolve();
        } else if (line.includes('Open Brain MCP server running')) {
          console.log('🧠 MCP server started');
        }
      });

      this.server.on('error', (err) => {
        console.error('❌ Server error:', err);
        reject(err);
      });

      // Timeout after 5 seconds
      setTimeout(() => {
        reject(new Error('Server startup timeout'));
      }, 5000);
    });
  }

  async sendRequest(method, params) {
    return new Promise((resolve, reject) => {
      if (!this.server) {
        reject(new Error('Server not started'));
        return;
      }

      const request = {
        type: 'request',
        id: this.requestId++,
        method,
        params
      };

      const rl = readline.createInterface({
        input: this.server.stdout,
        terminal: false
      });

      const responseHandler = (line) => {
        try {
          const data = JSON.parse(line);
          if (data.type === 'response' && data.id === request.id) {
            rl.removeListener('line', responseHandler);
            resolve(data);
          }
        } catch (e) {
          // Not JSON, ignore
        }
      };

      rl.on('line', responseHandler);

      // Send the request
      this.server.stdin.write(JSON.stringify(request) + '\n');

      // Timeout after 10 seconds
      setTimeout(() => {
        rl.removeListener('line', responseHandler);
        reject(new Error('Request timeout'));
      }, 10000);
    });
  }

  async queryRecentMemories(days = 7, limit = 10) {
    console.log(`🔍 Querying recent memories (last ${days} days)...`);
    
    const response = await this.sendRequest('tools/call', {
      name: 'recent_memories',
      arguments: { days, limit }
    });

    if (response.result?.content?.[0]?.text) {
      console.log('\n' + response.result.content[0].text);
    } else {
      console.log('No memories found or error in response');
    }
  }

  async searchByTopic(keyword, limit = 10) {
    console.log(`🔍 Searching for "${keyword}"...`);
    
    const response = await this.sendRequest('tools/call', {
      name: 'search_by_topic',
      arguments: { keyword, limit }
    });

    if (response.result?.content?.[0]?.text) {
      console.log('\n' + response.result.content[0].text);
    } else {
      console.log('No results found');
    }
  }

  async getStats() {
    console.log('📊 Getting brain statistics...');
    
    const response = await this.sendRequest('tools/call', {
      name: 'brain_stats',
      arguments: {}
    });

    if (response.result?.content?.[0]?.text) {
      console.log('\n' + response.result.content[0].text);
    }
  }

  async stop() {
    if (this.server) {
      this.server.kill();
      this.server = null;
      console.log('🛑 Server stopped');
    }
  }
}

// Command line interface
async function main() {
  const cli = new OpenBrainCLI();
  
  try {
    await cli.startServer();
    
    // Parse command line arguments
    const args = process.argv.slice(2);
    
    if (args.length === 0) {
      // Default: show recent memories
      await cli.queryRecentMemories();
    } else if (args[0] === 'recent') {
      const days = args[1] ? parseInt(args[1]) : 7;
      const limit = args[2] ? parseInt(args[2]) : 10;
      await cli.queryRecentMemories(days, limit);
    } else if (args[0] === 'search') {
      if (args.length < 2) {
        console.log('Usage: node openbrain_cli.js search <keyword> [limit]');
        return;
      }
      const limit = args[2] ? parseInt(args[2]) : 10;
      await cli.searchByTopic(args[1], limit);
    } else if (args[0] === 'stats') {
      await cli.getStats();
    } else if (args[0] === 'help') {
      console.log(`
Open Brain CLI Commands:
  node openbrain_cli.js                    Show recent memories (last 7 days)
  node openbrain_cli.js recent [days] [limit]  Show recent memories
  node openbrain_cli.js search <keyword> [limit] Search by keyword
  node openbrain_cli.js stats              Show brain statistics
  node openbrain_cli.js help               Show this help
      `);
    } else {
      console.log(`Unknown command: ${args[0]}`);
      console.log('Use "node openbrain_cli.js help" for available commands');
    }
    
    // Small delay before stopping
    setTimeout(() => {
      cli.stop();
    }, 1000);
    
  } catch (error) {
    console.error('❌ Error:', error.message);
    await cli.stop();
    process.exit(1);
  }
}

// Run if called directly
if (require.main === module) {
  main();
}

module.exports = OpenBrainCLI;