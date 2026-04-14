# ADR 002: Pivot to BFF Session Cookie Pattern over RAW JWT for Internal APIs

**Date:** 2026-04-14
**Status:** Accepted

## Context
Originally, the application's API endpoints (specifically the core `/chat` endpoint) were designed to expect a raw JWT Bearer token from the frontend. This required the frontend JS to hold onto the Opaque or JWT access token natively and explicitly attach it to every subsequent HTTP request representing a standard distributed API approach.

However, as captured in [ADR 001](./001-authlib-zitadel.md), our primary application login framework already heavily leverages Starlette’s signed `SessionMiddleware` to track OIDC identity state using a zero-database, cookie-bound mechanic for standard HTML web views.

## Decision
We actively evaluated maintaining separate strategies (API handles raw JWTs, web endpoints handle Cookies) versus unifying the backend under a single model.
We have decided to pivot all internal frontend-facing APIs to a **Backend-For-Frontend (BFF) Session Cookie pattern**. The `/chat` endpoint will simply read the secure `SessionMiddleware` cookie attached by the browser rather than validating a manually fetched authorization header. 

### Rationale
* **Massive XSS Risk Reduction**: By moving away from JWTs in the browser, the frontend no longer needs to query, persist, or inject access tokens in `localStorage` or Javascript memory. The session cookie is purely securely maintained and cannot be hijacked casually by malicious XSS payloads.
* **Radical Simplicity**: The frontend API calling mechanics transform from managing OIDC token refresh lifecycles into trivial `fetch('/chat')` calls, while the backend code drops complex JWKS network fetching code in favor of a 2-line session check.
* **Code Reusability**: The session logic explicitly mimics the `/api/me` and `/login` rendering handlers, entirely unifying our auth story under Starlette's umbrella.

## Consequences
* **CSRF Mitigation Required**: Cross-Site Request Forgery becomes an immediate threat because the browser automatically attaches the Auth Cookie. We mitigated this instantly by modifying our `SessionMiddleware` instantiation to use `same_site="strict"`, neutralizing CSRF natively because our UI and API endpoints share the exact same origin. 
* **API Portability Limitations**: This architecture couples the frontend and backend tightly together. If a 3rd party CLI script or a detached mobile application needs to hit `/chat` in the future, handling web cookies outside of a browser environment is highly cumbersome compared to raw JWT logic. Given our scope, this tradeoff was completely acceptable to adhere to Extreme Programming (XP) and KISS principles.
