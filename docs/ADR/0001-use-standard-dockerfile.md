# 1. Use Standard Dockerfile over pycontainer-build

Date: 2026-04-13

## Status

Accepted

## Context

We initially attempted to use `pycontainer-build` as specified by the architecture constraints: `Dockerfile-free containerization`. This tool reads `pyproject.toml` and programmatically builds an OCI layout and pushes the image directly via registry API without requiring a Docker daemon.
However, we hit two roadblocks during the GitHub Actions deployment:
1. `push` command via the CI pipeline was failing manually because `pycontainer-build` requires API-based registry integration. We circumvented manual pushes with the `--push` flag natively.
2. Even after bypassing, `pycontainer-build` experienced 403 authorization errors during the Blob Upload capability to Google Artifact Registry.
While this was a GCP permission error rather than a tool error, relying on an experimental tool obscures CI process standard practices and makes debugging significantly harder compared to traditional containerization. It also severely limits GitHub Actions layer caching.

## Decision

We will pivot back to a standard `Dockerfile` strategy instead of `pycontainer-build`. We will rely on standard `docker build` and `docker push` commands within our GitHub Actions pipeline, leveraging `uv` internal caching methods for optimal builds.

## Consequences

* **Pros:** Easier CI/CD integrations utilizing standard Actions, native `docker` syntax caching rules, well-known patterns for future scale.
* **Cons:** Introduces a `Dockerfile` to the repository, slightly increasing configuration overhead compared to a zero-configuration codebase.
