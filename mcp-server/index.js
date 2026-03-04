#!/usr/bin/env node
/**
 * Open Brain MCP Server
 * Allows AI agents to query your local memory database
 */

import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import { CallToolRequestSchema, ListToolsRequestSchema } from '@modelcontextprotocol/sdk/types.js';
import pg from 'pg';
import dotenv from 'dotenv';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

// Load environment variables
dotenv.config();

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

// PostgreSQL connection
const pool = new pg.Pool({
  database: 'openbrain',
  user: process.env.USER || 'jeffgordon',
  host: 'localhost',
  // If you need password, add it here
});

// Test database connection on startup
pool.query('SELECT NOW()', (err, res) => {
  if (err) {
    console.error('❌ Database connection failed:', err.message);
    process.exit(1);
  }
  console.log('✅ Connected to Open Brain database');
});

// Create MCP server
const server = new Server(
  {
    name: 'openbrain',
    version: '1.0.0',
  },
  {
    capabilities: {
      tools: {},
    },
  }
);

// List available tools
server.setRequestHandler(ListToolsRequestSchema, async () => ({
  tools: [
    {
      name: 'semantic_search',
      description: 'Search memories by meaning (semantic similarity)',
      inputSchema: {
        type: 'object',
        properties: {
          query: {
            type: 'string',
            description: 'The meaning to search for',
          },
          limit: {
            type: 'number',
            description: 'Maximum number of results (default: 10)',
            default: 10,
          },
          threshold: {
            type: 'number',
            description: 'Similarity threshold 0-1 (default: 0.7)',
            default: 0.7,
          },
        },
        required: ['query'],
      },
    },
    {
      name: 'recent_memories',
      description: 'Get most recent memories',
      inputSchema: {
        type: 'object',
        properties: {
          days: {
            type: 'number',
            description: 'Number of days to look back (default: 7)',
            default: 7,
          },
          limit: {
            type: 'number',
            description: 'Maximum number of results (default: 20)',
            default: 20,
          },
        },
      },
    },
    {
      name: 'search_by_topic',
      description: 'Search memories by topic or keyword (simple text search)',
      inputSchema: {
        type: 'object',
        properties: {
          keyword: {
            type: 'string',
            description: 'Keyword to search for in memory content',
          },
          limit: {
            type: 'number',
            description: 'Maximum number of results (default: 20)',
            default: 20,
          },
        },
        required: ['keyword'],
      },
    },
    {
      name: 'brain_stats',
      description: 'Get statistics about your Open Brain',
      inputSchema: {
        type: 'object',
        properties: {},
      },
    },
  ],
}));

// Handle tool calls
server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;

  try {
    switch (name) {
      case 'semantic_search': {
        const { query, limit = 10, threshold = 0.7 } = args;
        
        // For semantic search, we need embeddings
        // Since we can't generate embeddings in Node.js easily,
        // we'll return a helpful message and suggest using the metadata search instead
        
        return {
          content: [
            {
              type: 'text',
              text: `⚠️ Semantic search requires generating embeddings, which is better done in Python.\n\nHere are recent memories you can search through manually:\n\n${await getRecentMemories(limit)}`,
            },
          ],
        };
      }

      case 'recent_memories': {
        const { days = 7, limit = 20 } = args;
        const result = await pool.query(
          `SELECT id, content, metadata, created_at 
           FROM memories 
           WHERE created_at > NOW() - $1::interval 
           ORDER BY created_at DESC 
           LIMIT $2`,
          [`${days} days`, limit]
        );

        if (result.rows.length === 0) {
          return {
            content: [
              {
                type: 'text',
                text: `No memories found in the last ${days} days.`,
              },
            ],
          };
        }

        const formatted = result.rows.map(row => {
          const date = new Date(row.created_at).toLocaleString();
          return `[${date}]\n${row.content}\n`;
        }).join('\n---\n\n');

        return {
          content: [
            {
              type: 'text',
              text: `📝 **Recent Memories (last ${days} days)**\n\n${formatted}`,
            },
          ],
        };
      }

      case 'search_by_topic': {
        const { keyword, limit = 20 } = args;
        const result = await pool.query(
          `SELECT id, content, metadata, created_at 
           FROM memories 
           WHERE content ILIKE $1 
           ORDER BY created_at DESC 
           LIMIT $2`,
          [`%${keyword}%`, limit]
        );

        if (result.rows.length === 0) {
          return {
            content: [
              {
                type: 'text',
                text: `No memories found containing "${keyword}".`,
              },
            ],
          };
        }

        const formatted = result.rows.map(row => {
          const date = new Date(row.created_at).toLocaleString();
          // Highlight the keyword in the content
          const highlighted = row.content.replace(
            new RegExp(keyword, 'gi'),
            match => `**${match}**`
          );
          return `[${date}]\n${highlighted}`;
        }).join('\n\n---\n\n');

        return {
          content: [
            {
              type: 'text',
              text: `🔍 **Memories containing "${keyword}"**\n\n${formatted}`,
            },
          ],
        };
      }

      case 'brain_stats': {
        const total = await pool.query('SELECT COUNT(*) FROM memories');
        const lastWeek = await pool.query(
          "SELECT COUNT(*) FROM memories WHERE created_at > NOW() - INTERVAL '7 days'"
        );
        const lastMonth = await pool.query(
          "SELECT COUNT(*) FROM memories WHERE created_at > NOW() - INTERVAL '30 days'"
        );
        const latest = await pool.query(
          'SELECT created_at FROM memories ORDER BY created_at DESC LIMIT 1'
        );

        const stats = `📊 **Open Brain Statistics**

• Total memories: ${total.rows[0].count}
• Last 7 days: ${lastWeek.rows[0].count}
• Last 30 days: ${lastMonth.rows[0].count}
• Last capture: ${latest.rows[0] ? new Date(latest.rows[0].created_at).toLocaleString() : 'Never'}

**Quick Commands:**
• Use "recent_memories" to see your latest thoughts
• Use "search_by_topic" to find specific memories
• Full semantic search coming soon with local embeddings!`;

        return {
          content: [
            {
              type: 'text',
              text: stats,
            },
          ],
        };
      }

      default:
        throw new Error(`Unknown tool: ${name}`);
    }
  } catch (error) {
    console.error('Error handling tool call:', error);
    return {
      content: [
        {
          type: 'text',
          text: `❌ Error: ${error.message}`,
        },
      ],
    };
  }
});

// Helper function to get recent memories (for semantic search fallback)
async function getRecentMemories(limit = 10) {
  const result = await pool.query(
    `SELECT content, created_at 
     FROM memories 
     ORDER BY created_at DESC 
     LIMIT $1`,
    [limit]
  );

  if (result.rows.length === 0) {
    return 'No memories found.';
  }

  return result.rows.map(row => {
    const date = new Date(row.created_at).toLocaleString();
    return `[${date}]\n${row.content}`;
  }).join('\n\n---\n\n');
}

// Start the server
async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error('🧠 Open Brain MCP server running on stdio');
}

main().catch((error) => {
  console.error('Server error:', error);
  process.exit(1);
});
