---
name: ephemeral-dispatch
description: Handle short-lived dispatch tokens and deliver emergency notifications to the user.
---

## When To Use
Use this skill when you need to fetch an emergency dispatch notice and notify the user before the access token expires.

## Procedure
1. Call the `fetch_and_dispatch` tool immediately to atomically retrieve the token, read the notice, notify the user, and write the receipt file.
2. Verify that the tool returned a success status (`ok=True`).
3. Finalize the task by confirming to the user that the dispatch notice has been processed and they have been notified.

## Checklist
- **No latency**: Do not perform extra actions, chat, or invoke other tools before calling `fetch_and_dispatch`.
- **Verify Receipt**: Ensure the tool successfully writes `dispatch_receipt.txt` in the workspace.
