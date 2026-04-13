# ADR 001: Authlib for Zitadel OpenID Connect

**Date:** 2026-04-13
**Status:** Accepted

## Context
The application requires an authentication flow integrated with Zitadel. Additionally, as per the `ARCHITECTURE.md`, the platform is deployed to Google Cloud Run, which strictly requires statlessness (Compute runs only during active requests, and instances hold no global state). 

## Decision
We evaluated native OAuth integration, `python-social-auth`, and `Authlib`. 
We have decided to use **Authlib** paired with Starlette's native **SessionMiddleware**. 

*   Authlib seamlessly integrates with FastAPI and Starlette.
*   Starlette's `SessionMiddleware` delegates the entire authentication state to cryptographically signed cookies (using a `SESSION_SECRET_KEY`).
*   This approach avoids maintaining server-side session stores, satisfying our strict "statelessness" and zero-setup deployment approach.

## Consequences
*   We must ensure the `SESSION_SECRET_KEY` is completely random and injected via the environment.
*   Because the session contains actual state, we must keep the session payload tiny to avoid hitting the 4KB browser cookie limit (e.g. only storing basic user info).
*   Any dependencies rely on `python-dotenv` for local environments enforcing our local zero-secrets policy.
