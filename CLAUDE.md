# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Trustable Workspace is a serverless application with a TypeScript/React frontend and a Python backend. The application is a Kubernetes dashboard called Truk8s that allows users to upload kubeconfig files and monitor their Kubernetes clusters through a web interface.

**Main Features:**
- Upload and validate kubeconfig files
- Monitor pods, PVCs, and nodes in Kubernetes clusters
- AI-powered chat interface for cluster queries
- Serverless backend with S3 storage for kubeconfig persistence

## Commands

Never start a development environment.

Always assume there is a continuous deployment environment running.

## Architecture

**Frontend Stack:**

- React 18 with TypeScript
- Vite build tool
- React Router v6 (HashRouter for serverless compatibility)
- React Query for server state
- shadcn/ui components (Radix UI + Tailwind)
- Sonner for toast notifications

**Backend Stack:**

- Python serverless actions
- Kubernetes Python client (`kubernetes` library)
- S3 storage for kubeconfig persistence
- Redis for caching (optional)
- PostgreSQL for data storage (optional)

**Project Structure:**

```
src/
├── components/ui/  # shadcn/ui wrapped components
├── pages/          # Page components (routed in App.tsx)
├── hooks/          # Custom React hooks
├── lib/utils.ts    # Utility functions (cn() for classnames)
├── App.tsx         # Root component with providers and routing
└── main.tsx        # Entry point

packages/v1/        # Public backend actions
├── upload-kubeconfig/   # Endpoint to upload and validate kubeconfig
├── cluster-monitor/     # Endpoint to monitor cluster resources
└── .../           # Other API endpoints
```

## Conventions

- Use `@/` path alias for imports from `src/`
- Add new routes in [App.tsx](src/App.tsx) above the catch-all `*` route
- TypeScript is configured with relaxed settings (`noImplicitAny: false`, `strictNullChecks: false`)
- Styling uses TailwindCSS with CSS variables for theming (defined in `index.css`)

## Backend Actions

### Creating New Actions

- Use `action-new` to create new API endpoints
- Use `action-add-secret` to add environment variables/secrets
- Use `action-add-s3` to add S3 storage access
- Use `action-add-postgresql` to add PostgreSQL database access
- Use `action-add-redis` to add Redis cache access
- Use `action-requirements` to add Python dependencies

### Public vs Private Actions

- Public actions are exposed as HTTP endpoints at `/api/my/v1/<action>`
- Private actions (created with `public: false`) are used for initialization tasks
- Private actions are not exposed as HTTP endpoints
- Invoke private actions with `action-invoke`

### Initializations

Create private actions in the `init` package for:
- Creating database schemas (use `CREATE TABLE IF NOT EXISTS`)
- Adding database fields (use `ALTER TABLE ... ADD COLUMN IF NOT EXISTS`)
- Adding files to S3 buckets
- Initializing cache objects

Make init actions:
- Incremental
- Idempotent
- Not destructive

### API Endpoints

- Public actions: `/api/my/v1/<action>`
- Private actions: invoked via `action-invoke`
- Streaming: POST to `/api/stream/v1/<action>` for streaming output

## Kubernetes Integration

The application uses the Python Kubernetes client library to interact with Kubernetes clusters. Kubeconfig files are uploaded by users, validated, and stored in S3 for persistence. The cluster-monitor endpoint loads the kubeconfig from S3 and connects to the cluster.

## S3 Storage

- `ctx.S3_CLIENT` - S3 client for file operations
- `ctx.S3_DATA` - Private data bucket for sensitive files (kubeconfigs)
- `ctx.S3_WEB` - Public web bucket for static assets
- `ctx.S3_PUBLIC` - Public URL base for accessing S3 objects

## Error Handling

- Always return JSON responses with `error` and `message` fields
- Use `print()` statements for debugging backend logs
- Validate user input before processing
- Handle exceptions gracefully with meaningful error messages
