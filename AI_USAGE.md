# AI Usage Disclosure

## AI Tool 1

* **Tool/model:** ChatGPT (OpenAI)
* **Purpose:** Used as a support tool during investigation, troubleshooting, documentation, and understanding Docker, Docker Compose, NGINX, PostgreSQL, Redis, validation, backup/restore, and CI configuration.
* **Files or decisions affected:** `Dockerfile`, `docker-compose.yml`, `validate.py`, `failure_test.py`, `backup.sh`, `restore.sh`, `.github/workflows/ci.yml`, and documentation files under `docs/`.
* **What you changed or rejected:** AI suggestions were reviewed before use. I made the final changes myself, rejected suggestions that did not match the actual environment, and adjusted commands/configuration based on the observed terminal output and task requirements.
* **How you independently verified it:** I ran the relevant commands and tests in the local VM, inspected Docker Compose status and logs, tested application endpoints, verified network isolation, checked persistence, ran backup/restore verification, and ran the validation and failure/recovery tests.
* **Related commit:** Changes are included across the investigation and implementation commits in the repository history.

