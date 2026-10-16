---
name: dokploy-deploy
description: Deploy applications with Dokploy, Docker images, GitHub Actions and GHCR; troubleshoot image builds, routing and deployment failures.
---
# Portable Dokploy deployment

## Establish the target
Read the application's existing deployment files first. Determine the user's Dokploy base URL, project/application identifiers, image registry, hostname, deployment branch and runtime port from its documentation or authenticated dashboard. Do not assume a server, DNS provider, SSH account, registry ID or credential location. If these are not available, ask for the missing target information, never secret values in chat.

Use the installed Dokploy version's API documentation or dashboard to obtain the exact create/update/deploy request schemas. Authenticate using the user's existing secret mechanism and `x-api-key` header where supported. Never commit credentials or edit global MCP/client settings.

## Build the actual application
1. Identify its package manager and lockfile, build command, runtime dependencies and health endpoint.
2. Add a multi-stage Dockerfile using supported pinned base images, a non-root runtime and only required runtime files. For Next.js standalone output, enable `output: "standalone"`, copy the standalone server, `.next/static` and public assets, and bind to `0.0.0.0` on the application's documented port.
3. Keep secrets out of build arguments and image layers. Browser-exposed build variables are public and require rebuilding when changed.
4. Build in CI and publish an immutable commit tag or digest to GHCR. GitHub Actions needs `contents: read` and `packages: write`; use its ephemeral token for publication. Preserve the project's existing checks and deployment concurrency policy.

## Configure and deploy
Create/select the Dokploy project and application; configure the Docker image source, registry pull authorization, runtime environment, port, domain and TLS. Keep database/storage volumes and health checks explicit. Configure DNS only with authorization and verify its destination before requesting certificates.

Prefer the platform's documented deployment mechanism with an immutable image reference. If an existing system uses SSH/Swarm updates, verify its service name and image digest first. Use a pre-verified SSH host key, a least-privileged deployment account and registry credentials outside the repository. Do not disable host-key verification or overwrite an unrelated service. Mutable tags require an explicit pull; do not assume a restart fetches an image.

## Acceptance and rollback
Watch the CI run, Dokploy deployment events and container logs; verify health, HTTPS and a representative real request. Report the deployed image digest and evidence, not merely successful API submission. Retain the prior image reference and document how to redeploy it. Back up persistent state before migrations; rolling back an image does not reverse database changes.
