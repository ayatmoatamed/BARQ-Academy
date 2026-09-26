<img src="assets/barq-logo.svg" alt="BARQ Systems" width="180">

# BARQ Systems — DevOps Internship Task

This repository contains my completed investigation, fixes, validation scripts, backup/restore tooling, CI configuration, and documentation for the BARQ Systems DevOps Internship technical task.

The application consists of:

* NGINX reverse proxy
* Two Flask application instances: `app-01` and `app-02`
* PostgreSQL
* Redis
* Docker Compose

The system was intentionally supplied with configuration and runtime issues. The approach was to investigate each issue, identify the root cause using evidence, apply the smallest appropriate fix, and retest.

---

## Current Architecture

The request flow is:

```text
Client
  |
  v
NGINX :80
  |
  +------> app-01 :8080
  |
  +------> app-02 :8080
             |
             +----> PostgreSQL :5432
             |
             +----> Redis :6379
```

### Networks

* `frontend`: NGINX + application instances
* `backend`: application instances + PostgreSQL + Redis
* `backend` is an internal Docker network.

NGINX is not connected directly to the backend network.

### Port Exposure

Only NGINX is published to the host.

Current lab configuration:

```text
Host: 127.0.0.1:8080
        |
        v
NGINX container:80
        |
        v
Application containers:8080
```

PostgreSQL and Redis are internal-only services.

---

## Main Fixes

The following issues were investigated and fixed:

1. Application healthcheck used `/healthz` instead of `/health`.
2. PostgreSQL internal port was incorrect.
3. Redis internal port was incorrect.
4. PostgreSQL credentials did not match the application configuration.
5. NGINX used an incorrect application upstream port.
6. Flask was bound to `127.0.0.1` instead of `0.0.0.0`.
7. NGINX was connected to the backend network unnecessarily.
8. PostgreSQL and Redis had unnecessary host port exposure.
9. Application containers were running as root.
10. Application credentials were being copied into the Docker image.
11. PostgreSQL did not have persistent storage configured.
12. Redis persistence was not configured.
13. Container resource limits were missing.

Detailed investigation notes are available in:

* `docs/issues.md`
* `docs/troubleshooting.md`
* `docs/log_analysis.md`
* `docs/decisions.md`
* `docs/security_review.md`

---

# Setup

## Requirements

The project requires:

* Linux or WSL2
* Docker Engine
* Docker Compose
* Python 3.12 for local script execution
* Git

Use synthetic lab credentials only.

Do not commit real secrets.

---

## Configuration

The application uses:

```text
config/app.env
```

This file contains environment-specific credentials and must not be committed.

The application configuration is injected into the containers using Docker Compose `env_file`.

The credentials are not copied into the Docker image.

---

# Build and Start

Before starting the application, check the repository state:

```bash
git status
```

Build the application images and start all services:

```bash
docker compose -p barq-assessment up --build -d
```

Check the service state:

```bash
docker compose -p barq-assessment ps
```

View service logs:

```bash
docker compose -p barq-assessment logs --no-color
```

---

# Application Endpoints

The current public endpoint is:

```text
http://127.0.0.1:8080
```

Test the main application:

```bash
curl http://127.0.0.1:8080/
```

Check application health:

```bash
curl http://127.0.0.1:8080/health
```

Check application readiness:

```bash
curl http://127.0.0.1:8080/ready
```

Check which application instance handled the request:

```bash
curl http://127.0.0.1:8080/instance
```

Check the counter:

```bash
curl http://127.0.0.1:8080/counter
```

Check stored records:

```bash
curl http://127.0.0.1:8080/records
```

---

# Validation

The project includes:

```text
validate.py
```

The validation script checks:

* Application health
* Application readiness
* Required endpoints
* Record creation
* Multiple application instances
* Docker service state
* Host port exposure
* Backend network isolation

Run:

```bash
python3 validate.py
```

The validation was successfully completed with:

```text
Validation finished: 0 failure(s)
```

The validation result confirms that the checks implemented by `validate.py` passed in the tested environment.

It does not claim that every possible production failure mode has been tested.

---

# Failure and Recovery Test

The project includes:

```text
failure_test.py
```

The test intentionally stops `app-01`, sends requests through NGINX, and then restores the application instance.

Run:

```bash
python3 failure_test.py
```

Observed result:

```text
Traffic during failure: successes=10, errors=10
PASS: Traffic remained available during app-01 failure
PASS: app-01 recovered and serves requests
Failure/recovery test completed successfully
```

The test demonstrates that the remaining application instance can continue receiving traffic while one backend instance is unavailable.

---

# Persistence

PostgreSQL uses a named Docker volume:

```text
postgres-data
```

Redis uses:

```text
redis-data
```

Redis is configured with AOF persistence.

Persistence was tested by creating a record, recreating the application and PostgreSQL containers, and checking the records again.

The test record remained available after container recreation.

This demonstrates persistence across container recreation while the named volume is retained.

---

# Backup

The project includes:

```text
backup.sh
```

The script creates a PostgreSQL SQL dump in the `backups/` directory.

Run:

```bash
./backup.sh
```

Example output:

```text
Creating PostgreSQL backup...
Backup created: backups/barq_tasks_YYYYMMDD_HHMMSS.sql
```

Backups should not be committed to Git.

---

# Restore Verification

The project includes:

```text
restore.sh
```

The restore script does not overwrite the main application database.

Instead, it:

1. Creates a temporary test database.
2. Restores the backup into that database.
3. Counts the restored records.
4. Removes the temporary database.

Run:

```bash
./restore.sh backups/<backup-file>.sql
```

Successful restore verification confirms that the generated PostgreSQL backup can be restored successfully.

---

# Docker Security

The application containers run using a dedicated non-root user:

```text
app
```

The Docker image does not copy `config/app.env`.

PostgreSQL and Redis do not expose host ports.

Only NGINX is published to the host.

Resource limits are configured for the application and supporting services.

---

# Network Isolation

The application uses two networks.

### Frontend

Contains:

```text
nginx
app-01
app-02
```

### Backend

Contains:

```text
app-01
app-02
postgres
redis
```

The backend network is internal.

This prevents direct host access to PostgreSQL and Redis.

---

# Health and Readiness

The application healthcheck uses:

```text
/health
```

The readiness endpoint verifies application dependencies.

The distinction is intentional:

* `health` checks whether the application process is responding.
* `ready` checks whether the application is ready to serve traffic with its required dependencies.

Docker Compose healthchecks use bounded intervals, timeouts, retries, and a startup period.

---

# CI

The repository includes:

```text
.github/workflows/ci.yml
```

The workflow performs:

1. Repository checkout
2. Application environment creation
3. Python syntax checks
4. Docker Compose configuration validation
5. Application image build
6. Service startup
7. Readiness check
8. Automated validation
9. Cleanup

The CI environment uses test credentials and does not contain real secrets.

A successful CI run proves that the configured checks passed in the CI environment. It does not prove production readiness or cover every possible failure scenario.

---

# Investigation Approach

The investigation followed this general process:

```text
Observe symptom
      |
      v
Form hypothesis
      |
      v
Collect evidence
      |
      v
Identify root cause
      |
      v
Apply focused fix
      |
      v
Retest
      |
      v
Document result
```

The investigation deliberately included failed attempts and intermediate findings instead of only documenting the final configuration.

Detailed investigation records are available in:

```text
docs/troubleshooting.md
docs/issues.md
```

---

# Log Analysis

Historical logs were analyzed separately from live application testing.

The analysis includes:

* Request patterns
* Error patterns
* Correlated events
* Counts
* Commands used to investigate
* Avoiding duplicate counting of the same request

See:

```text
docs/log_analysis.md
```

---

# Design Decisions

The following design decisions were made during the task:

* Use NGINX as the only public entry point.
* Keep PostgreSQL and Redis internal.
* Separate frontend and backend networks.
* Run the application as a non-root user.
* Keep credentials outside the Docker image.
* Use named volumes for persistent data.
* Enable Redis AOF persistence.
* Add resource limits.
* Use health and readiness checks separately.
* Use automated validation with explicit failure codes.

Detailed reasoning, alternatives, trade-offs, and production considerations are documented in:

```text
docs/decisions.md
```

---

# Security Review

The security review covers:

* Secrets management
* Host port exposure
* Container privileges
* Image contents
* Network isolation
* Persistent data
* Backup handling
* Logging
* Availability
* Resource limits
* Dependency exposure
* Production improvements

See:

```text
docs/security_review.md
```

---

# AI Usage

AI assistance was used during the task for:

* Technical explanations
* Troubleshooting guidance
* Documentation structure
* Reviewing configuration
* Explaining Docker and networking behavior

All suggested changes were reviewed and verified against the actual environment using commands, logs, tests, and service behavior.

AI-generated suggestions were not treated as evidence by themselves.

See:

```text
AI_USAGE.md
```

---

# Stop and Cleanup

To stop the application containers without deleting persistent volumes:

```bash
docker compose -p barq-assessment down
```

Do not use `--volumes` when testing persistence.

Avoid global Docker cleanup commands such as:

```text
docker system prune
```

because they can remove unrelated Docker resources.

---

# Production Considerations

The current implementation is a disposable internship lab environment.

For production, additional improvements would be required, including:

* Proper secret management
* TLS termination
* Centralized logging
* Monitoring and alerting
* Externalized persistent storage
* Tested off-host backups
* Backup encryption
* Database high availability
* Redis high availability where required
* Container image vulnerability scanning
* Stronger access control
* Resource requests and limits based on measurements
* Multiple availability zones
* Load balancer or production ingress
* Disaster recovery testing

These are documented separately from the fixes implemented in this lab.

---

# Part 5 Final-State Requirements

The recorded demonstration will verify the final runtime state required by the task.

The final demonstration is expected to include:

* Continuous screen recording
* Live terminal commands
* Service health
* Application endpoint tests
* `/instance` traffic
* Backend failure and recovery
* Persistence verification
* Validation
* Historical log analysis
* Runtime challenge
* Public port change from `8080` to `8090`
* Addition of a third application instance
* Final validation
* Git diff and commit history

The `8090` port and third application instance should only be documented as completed after they are actually implemented and verified during Part 5.

---

# Evidence

The final submission will include an evidence index connecting:

```text
Requirement
    |
    v
File / command output
    |
    v
Git commit
    |
    v
Video timestamp
```

The evidence index is maintained in:

```text
docs/evidence_index.md
```

All evidence should correspond to the actual final repository and video state.

