# Troubleshooting Journal

This document records the investigation process used during the BARQ DevOps task.

The investigation followed:

```text
Symptom → Hypothesis → Evidence → Root Cause → Fix → Retest
```

The goal was to investigate the supplied environment rather than replace it.

---

## Issue 1 — Application Containers Unhealthy

### Symptom

`app-01` and `app-02` were running but reported as unhealthy.

### Investigation

I first checked the container status and application logs.

The configured Docker healthcheck was calling:

```text
/healthz
```

I tested the application endpoints directly from inside the container.

`/healthz` returned HTTP 404.

The application's actual health endpoint `/health` returned HTTP 200.

### Root Cause

The Docker healthcheck was using the wrong endpoint.

### Fix

Changed the healthcheck from:

```text
/healthz
```

to:

```text
/health
```

### Retest

After recreating the application containers, both application instances reported healthy.

### Lesson

A running container does not necessarily mean the application is healthy. The healthcheck must test an endpoint that actually exists.

---

## Issue 2 — Readiness and NGINX Connectivity

### Symptom

The `/ready` endpoint returned `503`, and NGINX returned `502` responses.

### Investigation

I checked the application environment variables and dependency connectivity.

The configured PostgreSQL port was incorrect.

The configured Redis port was also incorrect.

The expected internal ports are:

```text
PostgreSQL: 5432
Redis: 6379
```

I corrected the ports and tested connectivity from inside the application container.

The application could then reach both services.

### Database Authentication

The application logs showed PostgreSQL authentication errors.

A direct PostgreSQL connection test showed that the password used by the application did not match the PostgreSQL password.

I corrected the configuration so both services used matching credentials.

### NGINX Investigation

NGINX was still returning `502`.

I inspected the NGINX upstream configuration and found that it was forwarding requests to port `8081`.

The application listens internally on port `8080`.

I changed the upstream port to `8080`.

### Final Connectivity Issue

The application was still not reachable from NGINX.

The Flask application was bound to:

```text
127.0.0.1
```

This only accepts connections from inside the same container.

Since NGINX runs in a different container, it could not connect to the Flask process.

### Root Cause

Multiple configuration problems contributed to the readiness failure:

* Incorrect PostgreSQL port
* Incorrect Redis port
* PostgreSQL credential mismatch
* Incorrect NGINX upstream port
* Flask bound to loopback instead of all container interfaces

### Fix

The configuration was corrected to:

```text
PostgreSQL: 5432
Redis: 6379
NGINX upstream: 8080
APP_HOST: 0.0.0.0
```

### Retest

After the fixes, `/ready` returned successfully through NGINX.

The application could communicate with PostgreSQL and Redis.

---

## Issue 3 — Network Isolation

### Symptom

NGINX was attached to both the frontend and backend networks.

### Investigation

The intended architecture requires the backend network to contain the application and data services while remaining internal.

I inspected the Docker network membership.

### Root Cause

NGINX did not need direct membership in the backend network.

### Fix

Removed NGINX from the backend network.

The final network layout is:

```text
Frontend:
NGINX
app-01
app-02

Backend:
app-01
app-02
PostgreSQL
Redis
```

The backend network is internal.

### Retest

Network inspection confirmed that NGINX is not attached to the backend network.

---

## Issue 4 — Unnecessary Host Port Exposure

### Symptom

PostgreSQL and Redis had host port mappings.

### Root Cause

The database and Redis services only need to be reachable by the application containers.

### Fix

Removed the host port mappings from PostgreSQL and Redis.

Only NGINX publishes a host port.

### Retest

The Compose service status showed:

```text
NGINX      host port published
app-01     internal only
app-02     internal only
PostgreSQL internal only
Redis      internal only
```

---

## Issue 5 — Application Running as Root

### Symptom

The Dockerfile created an `app` user but the application was still configured to run as root.

### Root Cause

The Dockerfile explicitly selected the root user at runtime.

### Fix

Changed the Dockerfile to use:

```text
USER app
```

### Retest

The application image was rebuilt and the Compose configuration was validated successfully.

---

## Issue 6 — Credentials Copied Into the Image

### Symptom

The Dockerfile copied:

```text
config/app.env
```

into the image.

### Risk

The environment file contains application credentials.

Copying it into the image could leave credentials inside image layers.

### Root Cause

The Dockerfile contained a `COPY` instruction for the environment file.

### Fix

Removed the `COPY config/app.env` instruction.

Docker Compose already injects the environment file at runtime.

The environment file was also removed from Git tracking while remaining available locally for the lab.

### Retest

The Docker Compose configuration remained valid and the application continued to start using the runtime environment configuration.

---

## Issue 7 — PostgreSQL Persistence

### Symptom

The database required explicit persistent storage.

### Root Cause

Container storage alone is not sufficient for data that must survive container recreation.

### Fix

Added a named Docker volume:

```text
postgres-data
```

mounted at:

```text
/var/lib/postgresql/data
```

### Retest

A test record was created.

The PostgreSQL and application containers were recreated without removing the volume.

The record was still available afterward.

---

## Issue 8 — Redis Persistence

### Symptom

Redis did not have explicit persistence configuration.

### Root Cause

Redis data stored only in the container filesystem can be lost when the container is removed.

### Fix

Enabled Redis AOF persistence:

```text
redis-server --appendonly yes
```

and added the named volume:

```text
redis-data
```

mounted at `/data`.

### Retest

The Compose configuration was validated successfully.

---

## Issue 9 — Missing Resource Limits

### Symptom

The services did not have explicit CPU and memory limits.

### Risk

A single container could consume excessive host resources.

### Fix

Added resource limits for the application and supporting services.

Application containers:

```text
CPU: 0.50
Memory: 256M
```

PostgreSQL:

```text
CPU: 0.50
Memory: 512M
```

Redis and NGINX:

```text
CPU: 0.50
Memory: 256M
```

### Retest

Docker Compose configuration validation completed successfully.

---

## Issue 10 — Validation Script

### Symptom

The supplied validation script was unfinished.

### Investigation

The validation requirements were reviewed and implemented.

The script now checks:

* Application readiness
* Required endpoints
* Record creation
* Application instances
* Docker service state
* Host port exposure
* Backend network isolation

### Retest

The validation script completed with:

```text
Validation finished: 0 failure(s)
```

---

## Issue 11 — Failure and Recovery Test

### Objective

Verify application behavior when one backend instance becomes unavailable.

### Test

`app-01` was intentionally stopped.

Requests were then sent through NGINX.

### Result

The test produced:

```text
successes=10
errors=10
```

Traffic remained available through the surviving application instance.

`app-01` was then restored.

### Retest

The script waited for `app-01` to recover and verified that it served requests again.

### Result

```text
PASS: app-01 recovered and serves requests
```

---

## Issue 12 — PostgreSQL Backup

### Objective

Create a reproducible PostgreSQL backup.

### Fix

Implemented `backup.sh` using `pg_dump`.

### Retest

A backup file was successfully created under:

```text
backups/
```

---

## Issue 13 — PostgreSQL Restore Verification

### Objective

Verify that a generated backup can actually be restored.

### Approach

The restore script creates a temporary database rather than modifying the main application database.

The backup is restored into the temporary database.

The script then verifies the restored record count and removes the temporary database.

### Retest

The restore verification completed successfully.

---

## Issue 14 — CI Validation

### Implementation

A GitHub Actions workflow was added to:

* Check out the repository
* Create a test application environment
* Check Python syntax
* Validate Docker Compose configuration
* Build the application
* Start the services
* Wait for readiness
* Run `validate.py`
* Clean up the environment

### Current Status

The CI workflow has been configured in:

```text
.github/workflows/ci.yml
```

A matching successful GitHub Actions run should be recorded as evidence after the workflow is pushed and executed.

---

# Investigation Principles

Throughout the task, configuration changes were made only after collecting evidence.

The main investigation pattern was:

```text
Observe
↓
Form hypothesis
↓
Test hypothesis
↓
Identify root cause
↓
Apply focused fix
↓
Retest
```

Failed attempts and intermediate findings were retained in the investigation record because they demonstrate how the root causes were identified rather than only showing the final working configuration.

