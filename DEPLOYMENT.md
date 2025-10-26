# Ensenia Deployment Guide

This guide explains how to deploy all components of the Ensenia AI Teaching Assistant.

## Quick Start

### Development Deployment (Local)

```bash
# Deploy all services in development mode
./deploy.sh

# Or explicitly specify development mode
./deploy.sh development
```

This will:
- ✅ Set up and migrate the PostgreSQL database
- ✅ Start the Cloudflare Worker (port 8787)
- ✅ Start the React frontend (port 5173)
- ✅ Start the FastAPI backend (port 8001)

### Stop All Services

```bash
./stop.sh
```

### Production Deployment

```bash
./deploy.sh production
```

This will:
- ✅ Apply database migrations
- ✅ Deploy Worker to Cloudflare
- ✅ Build frontend (output in `app/web/dist/`)
- ⚠️  Show instructions for backend deployment

## Components

### 1. PostgreSQL Database

**Default Configuration:**
- Host: `localhost`
- Port: `5432`
- Database: `ensenia`
- User: `postgres`

**Custom Configuration:**
```bash
export DB_HOST=your-db-host
export DB_PORT=5432
export DB_NAME=ensenia
export DB_USER=postgres
export DB_PASSWORD=your-password
./deploy.sh
```

**Manual Database Setup:**
```bash
# Create database
createdb ensenia

# Run migrations
uv run alembic upgrade head
```

### 2. Cloudflare Worker

**Development:**
- Runs locally on port `8787`
- Hot-reload enabled
- Logs: `app/worker/worker.log`

**Production:**
```bash
cd app/worker
npm run deploy
```

**Configuration:**
- Edit `app/worker/wrangler.toml`
- Required: D1 database, Vectorize index, KV namespace
- See `app/worker/scripts/setup.sh` for CloudFlare resource setup

### 3. React Frontend

**Development:**
- Runs on port `5173` (Vite dev server)
- Hot-reload enabled
- Logs: `app/web/frontend.log`

**Production Build:**
```bash
cd app/web
npm run build
# Output: app/web/dist/
```

**Deploy to:**
- **Vercel**: `vercel --prod`
- **Netlify**: `netlify deploy --prod`
- **Cloudflare Pages**: `wrangler pages publish dist`

**Environment Variables:**
```env
VITE_API_URL=http://localhost:8001
VITE_WS_URL=ws://localhost:8001
```

Update these for production deployment.

### 4. FastAPI Backend

**Development:**
- Runs on port `8001`
- Hot-reload enabled
- Logs: `backend.log`

**Production Deployment Options:**

**Option 1: Systemd (Linux)**
```bash
# Create service file: /etc/systemd/system/ensenia.service
[Unit]
Description=Ensenia Backend API
After=network.target postgresql.service

[Service]
Type=simple
User=www-data
WorkingDirectory=/path/to/ensenia
Environment="PATH=/path/to/.venv/bin"
ExecStart=/path/to/.venv/bin/uvicorn app.ensenia.main:app --host 0.0.0.0 --port 8001 --workers 4
Restart=always

[Install]
WantedBy=multi-user.target

# Enable and start
sudo systemctl enable ensenia
sudo systemctl start ensenia
```

**Option 2: Docker**
```bash
docker build -t ensenia-backend .
docker run -d -p 8001:8001 --env-file .env ensenia-backend
```

**Option 3: PM2 (Node.js process manager)**
```bash
npm install -g pm2
pm2 start "uv run uvicorn app.ensenia.main:app --host 0.0.0.0 --port 8001 --workers 4" --name ensenia-backend
pm2 save
pm2 startup
```

## Environment Configuration

### Backend (.env)

```env
# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/ensenia

# API Keys
CLOUDFLARE_API_TOKEN=xxx
ELEVENLABS_API_KEY=xxx
OPENAI_API_KEY=xxx

# CloudFlare Resources
CLOUDFLARE_ACCOUNT_ID=xxx
CLOUDFLARE_R2_BUCKET=ensenia-hackaton
CLOUDFLARE_R2_ACCESS_KEY=xxx
CLOUDFLARE_R2_SECRET_KEY=xxx
CLOUDFLARE_R2_ENDPOINT_URL=xxx

# Server Config
BACKEND_PORT=8001
ENVIRONMENT=production
DEBUG=false
```

### Frontend (app/web/.env)

```env
VITE_API_URL=https://api.yourdomain.com
VITE_WS_URL=wss://api.yourdomain.com
```

## Custom Port Configuration

Override default ports:

```bash
export BACKEND_PORT=8000
export WORKER_PORT=8787
export FRONTEND_PORT=3000
./deploy.sh
```

## Monitoring & Logs

### View Logs (Development)

```bash
# Backend
tail -f backend.log

# Worker
tail -f app/worker/worker.log

# Frontend
tail -f app/web/frontend.log
```

### Process Management

All PIDs are saved in `.pid` files:
- `backend.pid`
- `app/worker/worker.pid`
- `app/web/frontend.pid`

```bash
# Check if service is running
kill -0 $(cat backend.pid) && echo "Running" || echo "Not running"

# Restart a service
kill $(cat backend.pid)
# Service will auto-restart if using systemd/PM2
```

## Production Checklist

- [ ] Update all API keys in `.env`
- [ ] Set `ENVIRONMENT=production` and `DEBUG=false`
- [ ] Configure database with connection pooling
- [ ] Set up reverse proxy (nginx/Caddy)
- [ ] Enable SSL/TLS certificates
- [ ] Configure CORS settings
- [ ] Set up monitoring (Sentry, CloudWatch, etc.)
- [ ] Configure log rotation
- [ ] Set up automated backups
- [ ] Deploy CloudFlare Worker
- [ ] Build and deploy frontend
- [ ] Configure CDN for static assets
- [ ] Set up health check endpoints
- [ ] Configure rate limiting
- [ ] Test WebSocket connections through proxy

## Troubleshooting

### Database Connection Issues

```bash
# Test database connection
psql -h localhost -U postgres -d ensenia

# Check if migrations are up to date
uv run alembic current
uv run alembic upgrade head
```

### Port Already in Use

```bash
# Find process using port
lsof -i :8001

# Kill process
kill -9 <PID>
```

### Worker Not Starting

```bash
# Check Worker logs
cat app/worker/worker.log

# Verify CloudFlare resources
cd app/worker
wrangler d1 list
wrangler vectorize list
wrangler kv:namespace list
```

### Frontend Build Errors

```bash
# Clear cache and rebuild
cd app/web
rm -rf node_modules dist .vite
npm install
npm run build
```

### Backend Health Check Failed

```bash
# Test health endpoint
curl http://localhost:8001/health

# Check backend logs
tail -100 backend.log

# Verify dependencies
uv sync
```

## Architecture Overview

```
┌─────────────────────────────────────────────────┐
│                   Frontend                      │
│            (React + Vite + TypeScript)          │
│              http://localhost:5173              │
└─────────────────┬───────────────────────────────┘
                  │ HTTP/WebSocket
┌─────────────────▼───────────────────────────────┐
│                  Backend                        │
│          (FastAPI + Python + PostgreSQL)        │
│              http://localhost:8001              │
└─────────────────┬───────────────────────────────┘
                  │ HTTP
┌─────────────────▼───────────────────────────────┐
│             CloudFlare Worker                   │
│    (Deep Research + D1 + Vectorize + KV)        │
│              http://localhost:8787              │
└─────────────────────────────────────────────────┘
```

## Support

For issues or questions:
1. Check logs for error messages
2. Review this deployment guide
3. Check `README.md` for general documentation
4. Review component-specific READMEs:
   - `app/worker/README.md`
   - `app/web/README.md`

## License

See LICENSE file for details.
