---
name: twenty-crm
description: Manage Twenty CRM people, companies, opportunities, metadata and self-hosted services with authorized APIs or existing MCP tools.
---
# Portable Twenty CRM management

## Discover the workspace
Use the user's existing authenticated Twenty MCP connection when available; otherwise consult the installed version's REST, GraphQL and metadata documentation. Determine the base URL, workspace, available objects, field names, relations, pipeline values and limits. Do not assume custom fields, lead sources, container names or API limits from another deployment. Keep API tokens in the user's existing secret mechanism, never in chat or committed files.

## Data operations
Search before creating people or companies. Match using stable identifiers and confirm ambiguous matches rather than merging by display name. Fetch current metadata before writing custom fields or selecting enum/pipeline values. Preserve fields not requested by the user. Associate people, companies, opportunities, tasks and notes using actual record identifiers and documented relation fields.

For bulk updates, preview the exact filter and affected records, use the server's documented pagination and batch size, and handle partial failures explicitly. Honor rate limits and retry guidance without duplicating creations. Require explicit authorization before destructive deletes, merges or mass reassignment. Report record IDs and actual outcomes, not merely a submitted request.

## Self-hosted operations
Inspect the deployment's Compose configuration and pinned versions first. From its actual project directory, inspect `docker compose ps` and service logs. Identify server, worker, database and cache services rather than guessing container names. Investigate unhealthy dependencies, migration errors and queue failures separately.

Back up the database, uploaded files and required configuration before upgrades or schema changes. Keep backup credentials separate, restrict file permissions and test restoration in isolation. Follow the installed version's migration/upgrade path; do not blindly pull unpinned latest images. Restores overwrite data and require confirmed target and authorization.

## Verify
After changes, check the API response and re-read the affected records. After infrastructure changes, verify health, login, a representative read/write and background processing. Distinguish a healthy HTTP endpoint from a fully functioning workspace. Summarize completed actions and any failures without exposing customer data or credentials.
