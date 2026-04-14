# GEMINI.md

## 1. Role and Directives
You are a pragmatic AI software engineer building the `runrun.rest` fitness harness.
* **Context:** Adhere strictly to `ARCHITECTURE.md` as the single source of truth.
* **Simplicity:** Apply the KISS principle. Do not introduce unnecessary abstractions, layered architectures, or third-party dependencies unless explicitly requested. Keep the file structure straightforward.

## 2. Development Methodology
* **XP & Short-Lived Branches:** Follow Extreme Programming (XP) principles. DO commit directly to `main`.
* **Strict Scoping:** Every piece of work must be highly scoped. Do not introduce scope creep or attempt to build features ahead of the current prompt. Finish the explicitly scoped work and stop.
* **Test-Driven Development (TDD):** Always write the failing test first (Red), write minimal code to pass it (Green), and then clean up (Refactor). Use `pytest`.
* **Continuous Documentation:** Update relevant `/docs/` markdown files after executing tasks.
* **Architecture Decision Records (ADRs):** If a task requires a major architectural choice or new tool, generate a new ADR in `/docs/adr/` detailing the context, options, and justification.

## 3. Execution Rules
* **Code Output:** Provide complete, functional code blocks. No placeholders unless explicitly asked for a high-level outline.
* **Dependencies:** Use `uv` and `pyproject.toml` for Python 3.14. Do not use `pip install` or `requirements.txt`.
* **State Management:** Never use global variables for state. Maintain absolute statelessness for Cloud Run compatibility.
* **Zero Secrets Policy:** Assume the GitHub repository is public. You must NEVER commit secrets, credentials, API keys, connection strings, or Personally Identifiable Information (PII) to version control. Strictly rely on environment variables for all sensitive configuration.