### Issue 1 — App containers are unhealthy

**Symptoms:**
`app-01` and `app-02` are `Up (unhealthy)`.

**Hypothesis:**
The Docker healthcheck may be using the wrong endpoint.

**Commands:**

```bash
docker compose -p barq-assessment ps -a
docker compose -p barq-assessment logs --no-color --tail 30 app-01 app-02
docker exec app-01 python -c "import urllib.request; print(urllib.request.urlopen('http://127.0.0.1:8080/health').status)"
```

**Results:**

* `/healthz` → `404`
* `/health` → `200`

**Failed attempt:**
The initial full app-log command produced too much output, so `--tail 30` was used.

**Root cause:**
The Docker healthcheck uses `/healthz`, while the application health endpoint is `/health`.

**Fix:**
Changed the Docker healthcheck endpoint from `/healthz` to `/health`.

**Retest:**
Command:
`docker compose -p barq-assessment ps -a`

Result:
`app-01` and `app-02` are both `healthy` after recreating the containers.

**Commit:**
`fix: change healthcheck from /healthz to /health`

### Issue 2 — `/ready` fails and NGINX cannot reach the app

**Symptoms:**
`/ready` initially returned `503`. After fixing the application dependencies, requests through NGINX still failed with connection/reset errors and then `502 Bad Gateway`.

**Hypotheses:**

1. The application may be using incorrect PostgreSQL and Redis internal ports.
2. PostgreSQL authentication may be failing.
3. NGINX may be using an incorrect upstream port or port mapping.
4. Flask may only be listening on the container loopback interface.

**Commands:**

```bash
docker exec app-01 env | grep -E 'DATABASE_URL|REDIS_URL'
```

```bash
docker exec app-01 python -c "import socket; print('postgres:', socket.create_connection(('postgres', 5432), 5)); print('redis:', socket.create_connection(('redis', 6379), 5))"
```

```bash
docker exec app-01 pg_isready -U barq_app -d barq_tasks -p 5432
```

```bash
docker exec app-01 redis-cli -h redis -p 6379 ping
```

```bash
docker compose -p barq-assessment logs --no-color --tail 30 app-01
```

```bash
docker exec app-01 python -c "import psycopg; psycopg.connect('postgresql://barq_app:<password>@postgres:5432/barq_tasks'); print('connected')"
```

```bash
grep -nE 'DATABASE_URL|REDIS_URL|POSTGRES_PASSWORD' config/app.env docker-compose.yml
```

**Results:**

* The application initially used PostgreSQL port `5433` and Redis port `6380`.
* PostgreSQL internal port is `5432` and Redis internal port is `6379`.
* TCP connectivity to both services succeeded after correcting the ports.
* `pg_isready` reported that PostgreSQL was accepting connections.
* Redis returned `PONG`.
* Application logs showed a PostgreSQL `OperationalError`.
* The direct PostgreSQL connection test showed a password authentication failure.
* The PostgreSQL password configured for the database did not match the password used by the application.

**Fix:**

* Changed PostgreSQL port from `5433` to `5432`.
* Changed Redis port from `6380` to `6379`.
* Corrected the PostgreSQL password mismatch.
* Recreated `app-01` and `app-02`.

**Retest:**

Command:

```bash
docker exec app-01 python -c "import urllib.request; r=urllib.request.urlopen('http://127.0.0.1:8080/ready'); print(r.status); print(r.read().decode())"
```

Result:

`200`

Both PostgreSQL and Redis were reported as `ready`.

---

### NGINX connectivity investigation

**Symptom:**

The `/ready` endpoint worked directly from the application container but failed when accessed through NGINX.

**Commands:**

```bash
curl -i http://127.0.0.1:8080/ready
```

```bash
docker compose -p barq-assessment logs --no-color --tail 30 nginx
```

```bash
grep -nE 'upstream|server |listen' nginx/nginx.conf
```

**Results:**

* NGINX initially returned `502 Bad Gateway`.
* NGINX logs showed `Connection refused` while connecting to the upstream.
* The upstream configuration used `app-01:8081` instead of `app-01:8080`.
* NGINX listened on port `80`, while the Compose port mapping published container port `81`.

**Fix:**

* Changed `app-01:8081` to `app-01:8080`.
* Changed the NGINX port mapping from `:81` to `:80`.

NGINX still could not connect to the application.

**Root cause:**

Flask was configured with:

`APP_HOST=127.0.0.1`

This made Flask listen only on the application container's loopback interface. NGINX runs in a different container and therefore could not reach Flask through the Docker network.

**Fix:**

Changed:

`APP_HOST=127.0.0.1`

to:

`APP_HOST=0.0.0.0`

Then recreated `app-01` and `app-02`.

**Retest:**

The `/ready` endpoint was successfully accessed through NGINX and returned HTTP `200`, with PostgreSQL and Redis reported as ready.

**Final result:**

The request path works correctly:

`Client → NGINX → Flask → PostgreSQL / Redis`

**Commit:**

`fix: resolve app readiness and reverse proxy issues`

### Issue 3 — Network isolation

**Symptoms:**
The initial Docker network configuration attached NGINX to both `frontend` and `backend`.

**Hypothesis:**
NGINX should only communicate with the application containers through the `frontend` network. It should not have direct network access to PostgreSQL or Redis.

**Investigation:**

The required network topology is:

```text
frontend → nginx + app-01 + app-02
backend  → app-01 + app-02 + postgres + redis
```

The backend network was configured as an internal network.

**Fix:**
Changed the NGINX service to use only the `frontend` network:

```yaml
nginx:
  networks: [frontend]
```

The application containers remain connected to both networks, while PostgreSQL and Redis remain connected only to `backend`.

**Retest:**

Command:

```bash
docker network inspect barq-assessment_backend
```

Result:

The backend network contains:

* `postgres`
* `redis`
* `app-01`
* `app-02`

`nginx` is not attached to the backend network.

Command:

```bash
docker network inspect barq-assessment_frontend
```

Result:

The frontend network contains:

* `nginx`
* `app-01`
* `app-02`

**Conclusion:**
The network isolation requirement is satisfied: NGINX can reach the application layer through `frontend`, while PostgreSQL and Redis remain isolated on the internal `backend` network.

---

### Issue 4 — Prohibited host port exposure

**Symptoms:**
PostgreSQL and Redis initially had host port mappings, which exposed their internal service ports to the Docker host.

**Hypothesis:**
Only NGINX should be accessible through a host-published port. PostgreSQL, Redis, and the Flask application containers should remain internal to the Docker networks.

**Investigation:**

The initial configuration exposed PostgreSQL and Redis using host port mappings.

The application containers also use port `8080`, but this is an internal container port and does not need to be published to the host.

**Fix:**
Removed the `ports` mappings from:

* `postgres`
* `redis`

Only NGINX keeps a host port mapping:

```yaml
ports: ["127.0.0.1:${PUBLIC_PORT:-8080}:80"]
```

**Retest:**

Command:

```bash
docker compose -p barq-assessment ps
```

Result:

NGINX is the only service with a host-published port:

```text
127.0.0.1:8080->80/tcp
```

The other services expose only their internal container ports:

```text
app-01      8080/tcp
app-02      8080/tcp
postgres    5432/tcp
redis       6379/tcp
```

**Conclusion:**
Only NGINX is published to the host. PostgreSQL, Redis, and the application containers are accessible only through the Docker networks.

---

### Issue 5 — Application containers running as root

**Symptoms:**
The Dockerfile explicitly switched the application container back to the `root` user.

**Hypothesis:**
The application should run as a non-root user where practical to reduce the impact of a potential container compromise.

**Investigation:**

The Dockerfile already created a dedicated user:

```dockerfile
RUN groupadd --gid 10001 app && useradd --uid 10001 --gid app --no-create-home app
```

However, it later contained:

```dockerfile
USER root
```

This caused the application process to run as root.

**Fix:**
Changed the Dockerfile to run the application as the existing `app` user:

```dockerfile
USER app
```

**Retest:**

The Docker image was rebuilt after the Dockerfile change.

The Compose configuration was validated successfully:

```text
Compose config: OK
```

**Conclusion:**
The application is configured to run as the dedicated non-root `app` user instead of root.

---

### Issue 6 — Application secrets copied into the Docker image

**Symptoms:**
The Dockerfile copied `config/app.env` directly into the application image.

**Hypothesis:**
Secrets should not be embedded in Docker images because anyone with access to the image may potentially inspect its filesystem.

**Investigation:**

The Dockerfile originally contained:

```dockerfile
COPY config/app.env /srv/app.env
```

`config/app.env` contains application configuration including database credentials.

The Compose configuration already provides the application's environment using:

```yaml
env_file: ./config/app.env
```

Therefore, copying the same file into the image was unnecessary and created an additional secret exposure.

**Fix:**
Removed:

```dockerfile
COPY config/app.env /srv/app.env
```

The application receives its environment variables through Docker Compose instead.

The secret configuration file was also removed from Git tracking:

```bash
git rm --cached config/app.env
```

The local file remains available for the running environment but is no longer tracked by Git.

**Retest:**

Checked the Git working tree to verify that `config/app.env` is no longer tracked.

The Compose configuration was also validated successfully:

```text
Compose config: OK
```

**Conclusion:**
Application secrets are no longer copied into the Docker image or tracked as a Git file. Runtime configuration is supplied through the Compose environment.

---

### Issue 7 — PostgreSQL data storage configuration

**Symptoms:**
The original PostgreSQL storage configuration used an inappropriate temporary filesystem configuration for the database data directory.

**Hypothesis:**
PostgreSQL data must survive container recreation, so the database should use a persistent named Docker volume.

**Investigation:**

The PostgreSQL data directory is:

```text
/var/lib/postgresql/data
```

A named volume is appropriate because it stores database data outside the container lifecycle.

**Fix:**
Changed the PostgreSQL storage configuration to:

```yaml
volumes:
  - postgres-data:/var/lib/postgresql/data
  - ./database/init.sql:/docker-entrypoint-initdb.d/01-init.sql:ro
```

The temporary filesystem configuration was removed.

The named volume was declared at the bottom of the Compose file:

```yaml
volumes:
  postgres-data:
```

**Retest:**

The Compose configuration was validated successfully:

```text
Compose config: OK
```

**Conclusion:**
PostgreSQL now uses a named persistent volume instead of temporary container storage.

---

### Issue 8 — Redis persistence configuration

**Symptoms:**
Redis did not have explicit persistent storage configuration.

**Hypothesis:**
Redis data should persist across container recreation where persistence is required by the application.

**Fix:**
Enabled Redis Append Only File persistence:

```yaml
command: ["redis-server", "--appendonly", "yes"]
```

Added a named volume:

```yaml
volumes:
  - redis-data:/data
```

And declared the volume:

```yaml
volumes:
  redis-data:
```

**Retest:**

The Compose configuration was validated successfully:

```text
Compose config: OK
```

**Conclusion:**
Redis is configured with AOF persistence and a named Docker volume.

---

### Issue 9 — Missing resource limits

**Symptoms:**
The application and supporting services did not have explicit CPU and memory limits.

**Hypothesis:**
Each container should have reasonable resource boundaries to prevent one service from consuming unlimited host resources.

**Fix:**
Added resource limits to the shared application definition so both `app-01` and `app-02` inherit the same limits:

```yaml
deploy:
  resources:
    limits:
      cpus: "0.50"
      memory: 256M
```

Added service-specific limits for PostgreSQL:

```yaml
deploy:
  resources:
    limits:
      cpus: "0.50"
      memory: 512M
```

Added limits for Redis and NGINX:

```yaml
deploy:
  resources:
    limits:
      cpus: "0.50"
      memory: 256M
```

**Retest:**

Command:

```bash
docker compose -p barq-assessment config >/dev/null && echo "Compose config: OK"
```

Result:

```text
Compose config: OK
```

**Conclusion:**
The Compose configuration now contains explicit CPU and memory limits for the application and supporting services.

## Part 3 — Validation, Persistence, Recovery and CI

### Issue 10 — No Automated Validation

**Symptoms:**
`validate.py` was only a placeholder and did not validate the environment.

**Hypothesis:**
The application may be working, but there is no automated validation to confirm endpoint availability, backend health, network isolation, or prohibited host ports.

**Root Cause:**
No automated checks were implemented for these requirements.

**Fix:**
Implemented bounded validation with PASS/FAIL output and non-zero exit on failure.

**Verification:**
`Validation finished: 0 failure(s)`.

---

### Issue 11 — No Failure/Recovery Test

**Symptoms:**
There was no automated proof that the application remains available when one backend fails or that the failed backend recovers afterward.

**Hypothesis:**
If `app-01` is stopped, NGINX should continue routing requests to `app-02`; after restoration, `app-01` should become available again.

**Root Cause:**
`failure_test.py` was not implemented.

**Fix:**
Added a test that stops `app-01`, measures successful/failed requests, restores it, and verifies recovery.

**Verification:**
10 successful requests and 10 errors during the failure test; `app-01` successfully recovered.

---

### Issue 12 — No PostgreSQL Backup/Restore

**Symptoms:**
Backup and restore scripts were placeholders.

**Hypothesis:**
A PostgreSQL backup should be created with `pg_dump` and should be restorable into a clean database.

**Root Cause:**
No automated PostgreSQL backup/recovery procedure was implemented.

**Fix:**
Implemented `backup.sh` using `pg_dump` and `restore.sh` using a temporary restore database.

**Verification:**
PostgreSQL backup was created successfully and restore verification succeeded.

---

### Issue 13 — PostgreSQL Persistence Not Proven

**Symptoms:**
There was no evidence that PostgreSQL data survives container recreation.

**Hypothesis:**
If PostgreSQL uses a named persistent volume, records should remain available after recreating the PostgreSQL and application containers.

**Root Cause:**
No end-to-end persistence test had been performed.

**Fix:**
Created a record, recreated the application and PostgreSQL containers while retaining the named volume, then queried the application again.

**Verification:**
`persistence-test-2026` remained available after container recreation.

---

### Issue 14 — No CI Validation

**Symptoms:**
There was no automated CI pipeline to validate the application and infrastructure configuration.

**Hypothesis:**
A GitHub Actions workflow can automatically detect syntax, Compose configuration, build, startup, readiness, and validation failures on every push or pull request.

**Root Cause:**
`.github/workflows/ci.yml` was missing.

**Fix:**
Added a GitHub Actions workflow for syntax checks, Compose validation, image build, service startup, readiness checks, and application validation.

**Verification:**
CI workflow configured to run automatically on push and pull request.

