/// <reference types="@cloudflare/workers-types" />

/**
 * Utility functions for HTTP responses
 */

import { ErrorResponse } from '../types/schemas';

/**
 * Create a JSON response with proper headers
 */
export function jsonResponse(data: any, status: number = 200): Response {
  return new Response(JSON.stringify(data), {
    status,
    headers: {
      'Content-Type': 'application/json',
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type',
    },
  });
}

/**
 * Create an error response
 */
export function errorResponse(
  status: number,
  code: string,
  message: string,
  details?: any
): Response {
  const error: ErrorResponse = {
    error: 'Error',
    code,
    message,
    ...(details && { details }),
  };
  return jsonResponse(error, status);
}

/**
 * Handle CORS preflight requests
 */
export function corsPreflightResponse(): Response {
  return new Response(null, {
    status: 204,
    headers: {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type',
      'Access-Control-Max-Age': '86400',
    },
  });
}

/**
 * Validate request body exists
 */
export async function parseJsonBody<T>(request: Request): Promise<T> {
  try {
    const body = await request.json();
    return body as T;
  } catch (error) {
    throw new Error('Invalid JSON body');
  }
}
