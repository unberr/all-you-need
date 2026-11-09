---
name: fullstack-integration
description: Keep frontend, backend and database in agreement: one contract, auth sync, error propagation, retries, real time, file transfer, session expiry, end-to-end tests. Use when a feature spans UI, API and data.
---

# fullstack-integration

A feature is finished when the whole path works: UI, request, server logic, database, response, UI update, and the failure paths in between. Components that work alone but do not connect are not done.

## Build the whole path
- Implement the complete workflow, not one layer. Before coding, write the path as a short list: user action, request (method, URL, body), validation, authorization, data change, response, UI update, and what the user sees on each failure.
- Keep a ledger for multi-layer work (see `finish-the-job`): migration, model, endpoint, schema, client call, UI, tests, docs each as an item.

## One contract
- The API schema (OpenAPI, GraphQL schema, tRPC or shared TypeScript types, protobuf) is the single source of truth. Generate client types and server validators from it, or validate both sides against it, so the frontend request and the backend schema cannot drift. Change the schema first, then both sides, in the same change.
- Keep field names, types, nullability, enums, date formats (ISO 8601, UTC), money representation (integer minor units or decimal strings), error shapes and pagination formats identical on both sides.
- Reading an API response is a trust boundary too: validate it in the client when the data drives logic (a schema parse), or rely on generated types and a contract test.
- Do not break existing clients: additive changes, versioned breaking changes (see `backend-api`).

## Authentication and authorization
- The server is the authority. The frontend tracks "who am I" from the server (session cookie or a token flow), refreshes it on load, and handles `401` by re-authenticating and `403` by showing a permission message, never by trusting stored client state.
- UI permissions mirror backend rules but never replace them. When the rule changes, change the backend first and derive the UI from it (for example, the server returns the actions the user may take).
- Logout clears client state and invalidates the server session. Role or tenant changes refresh the client's view.
- Session expiry: detect `401` mid-flow, keep unsaved user input where possible (draft in memory, prompt to sign in again, retry the action), and never silently drop data.

## Data flow and errors
- Follow each piece of data from input to storage to display: validation at the entry, one representation in transit, correct escaping at display, consistent formatting. Check timezone and locale handling end to end.
- Propagate errors usefully: the server returns a stable error code, field errors and a correlation id; the client maps codes to messages and shows field-level problems at the field. Network failure, timeout, 4xx, 5xx and partial success all have a UI outcome.
- Retries: retry only idempotent requests, or `POST`s with an idempotency key; use exponential backoff with jitter and a cap; do not retry validation errors; show the user that something is retrying and let them cancel. Prevent double submission in the UI as well.

## Real time
- Use WebSockets or server-sent events when the user needs live updates; plain requests or polling when they do not. Authenticate the connection, authorize every subscription and message server-side, validate incoming messages, limit message size and rate, handle reconnection with backoff and resynchronize state after a gap, and clean up connections on logout and unmount.

## Files
- Uploads and downloads follow `secure-code` (type and size checks from content, generated names, storage outside the web root, authorized downloads, safe `Content-Disposition`). Show progress, allow cancel, support retry or resume for large files, and clean up partial uploads. Large downloads stream; signed, expiring URLs for private objects.

## Verify end to end
- Run an integration test for each workflow across the real boundary (API plus database; browser plus API for critical paths): the happy path, validation failure, unauthorized and forbidden, not found, conflict, server error and timeout. Use real network calls to a test server, not a mocked client, for at least the critical flows.
- Check the contract from both directions: the client's requests are accepted by the server, and the server's responses parse in the client.
- Report which layers you ran and which you could only reason about.
