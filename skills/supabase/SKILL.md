---
name: supabase
description: Operate self-hosted Supabase, including Docker services, PostgreSQL schemas, permissions, RLS, backups and connectivity troubleshooting.
---
# Self-hosted Supabase operations

## Discover before changing
Read the deployment's Compose files, version, service names, exposed ports and backup instructions. Use its existing authorized connection method. Never assume a host, filesystem path, password, schema list or credential source. Keep service-role keys server-side; anon/publishable keys do not replace row-level security.

## Diagnose safely
From the actual Compose directory, inspect `docker compose ps` and logs for the failing service. Trace the request through reverse proxy, API gateway, PostgREST/Auth/Storage and database. Distinguish authentication failure, missing exposed schema, missing SQL privileges and RLS policy rejection. Never fix an access issue by disabling RLS or exposing internal database ports.

## Add an application schema
1. Choose and quote a valid schema identifier. Inspect existing roles, grants and migration conventions.
2. Create the schema through a reviewed migration. Grant only the schema/table/sequence/routine privileges needed by each application role. Do not grant all objects to anonymous users by default.
3. Set default privileges for the role that actually creates future objects. Enable RLS on exposed tables and define authenticated/anonymous policies with explicit ownership constraints.
4. Add the schema to the PostgREST exposed-schema configuration only if REST access is intended. Apply changed environment with `docker compose up -d rest` using the deployment's actual service name; a simple restart does not reload Compose environment definitions.
5. Test allowed and denied operations using appropriate anon and authenticated clients. A service-role-only test cannot establish that RLS works.

## Client and proxy boundaries
Initialize clients where runtime configuration is available; validate required environment before serving traffic. Never send a service-role key to a browser. Route API paths to the gateway and protect administrative Studio separately; an extra site-wide Basic Auth challenge may break legitimate API clients.

## Backups and maintenance
Use the deployment's PostgreSQL-compatible backup tooling and versions. Capture database roles/globals and application schemas, plus storage objects and configuration through their respective backup systems. Encrypt backups, restrict access, set retention and prove restoration in an isolated environment. Database dumps alone do not preserve object storage files.

Before upgrades, record image versions and take a consistent backup. Read release migration instructions, apply changes in a maintenance window where required and verify Auth, REST, Storage and Realtime separately. Restore is destructive: confirm the target and obtain authorization before replacing data.
