# ADR 003: Session Cookie SameSite Configuration (Lax vs Strict)

## Context
Our application utilizes a backend-for-frontend (BFF) authentication setup leveraging Starlette's `SessionMiddleware` to store user session data and OAuth UI flow state (such as the CSRF parameter `state` for Zitadel login).
Normally, we would prefer configuring `SameSite=Strict` for our session cookies in production because it provides robust defense against Cross-Site Request Forgery (CSRF) attacks by ensuring the browser ignores the session cookie on any cross-site request. 
However, since we are using a hosted Identity Provider (IDP, i.e., Zitadel) on a completely different top-level domain from our application, the OAuth callback redirect that lands users back at `/auth/callback` constitutes a cross-site navigation. When `SameSite=Strict` is active, the browser will refuse to attach the session cookie during this redirect, leading to an empty Starlette session and a consequent `authlib.integrations.base_client.errors.MismatchingStateError` because AuthLib cannot retrieve the original `state` variable to validate against the callback payload.

## Decision
We elected to set `SameSite=Lax` on our `SessionMiddleware` globally, for both local development and production. 

```python
app.add_middleware(
    SessionMiddleware, 
    secret_key=os.environ.get("SESSION_SECRET_KEY", "fallback-secret"),
    same_site="lax",
    https_only=os.environ.get("ENVIRONMENT") == "production"
)
```
We chose this over attempting to bind the IDP to a subdomain of our application (e.g., `login.runrun.rest`) to avoid the setup overhead and cost associated with custom domains on third-party IDPs right now.

## Consequences
- **Positive:** Our OpenID Connect authorization code flow resolves successfully locally and in production without throwing state mismatch errors.
- **Negative (Security Trade-off):** `SameSite=Lax` makes the application more vulnerable to certain CSRF attack vectors than `Strict` (specifically attacks operating through top-level navigations from other malicious sites, though modern browsers generally enforce `Lax` stringently).
  
## Future Considerations
If our security posture necessitates `SameSite=Strict`, we must reconsider our IDP alignment. We can host the IDP on a shared top-level domain with this application (e.g., placing the app at `runrun.rest` and the IDP at `login.runrun.rest`), which allows the identity redirect to qualify as a same-site request for cookie purposes. This requirement acts as technical debt that will need to be plugged later.
