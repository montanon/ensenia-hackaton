/**
 * Ensenia CloudFlare Worker - Main Entry Point
 * MCP Server for AI Search in Chilean Education
 */

import { Env } from './types/env';
import { handleSearch } from './routes/search';
import { handleFetch } from './routes/fetch';
import { handleGenerate } from './routes/generate';
import { handleValidate } from './routes/validate';
import { jsonResponse, errorResponse, corsPreflightResponse } from './utils/responses';

/**
 * Main worker handler
 */
export default {
  async fetch(request: Request, env: Env, ctx: ExecutionContext): Promise<Response> {
    const url = new URL(request.url);
    const path = url.pathname;

    // Handle CORS preflight requests
    if (request.method === 'OPTIONS') {
      return corsPreflightResponse();
    }

    // Health check endpoint
    if (path === '/health' && request.method === 'GET') {
      return handleHealthCheck(env);
    }

    // Route to appropriate handler based on path and method
    try {
      switch (path) {
        case '/search':
          if (request.method === 'POST') {
            return await handleSearch(request, env);
          }
          break;

        case '/fetch':
          if (request.method === 'POST') {
            return await handleFetch(request, env);
          }
          break;

        case '/generate':
          if (request.method === 'POST') {
            return await handleGenerate(request, env);
          }
          break;

        case '/validate':
          if (request.method === 'POST') {
            return await handleValidate(request, env);
          }
          break;

        default:
          return errorResponse(404, 'NOT_FOUND', `Endpoint ${path} not found`);
      }

      // If we get here, method not allowed
      return errorResponse(
        405,
        'METHOD_NOT_ALLOWED',
        `Method ${request.method} not allowed for ${path}`
      );
    } catch (error: any) {
      console.error('Worker error:', error);
      return errorResponse(
        500,
        'INTERNAL_ERROR',
        error.message || 'Internal server error'
      );
    }
  },
};

/**
 * Health check endpoint
 * Returns status of all services
 */
async function handleHealthCheck(env: Env): Promise<Response> {
  const health = {
    status: 'healthy',
    timestamp: new Date().toISOString(),
    environment: env.ENVIRONMENT,
    services: {
      ai: 'available',
      database: 'unknown',
      vectorize: 'available',
      cache: 'available',
    },
  };

  // Test database connection
  try {
    await env.DB.prepare('SELECT 1').first();
    health.services.database = 'healthy';
  } catch (error) {
    health.services.database = 'unhealthy';
    health.status = 'degraded';
  }

  return jsonResponse(health);
}
