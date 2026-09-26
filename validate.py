#!/usr/bin/env python3
import json
import socket
import sys
import time
import urllib.error
import urllib.request

BASE = "http://127.0.0.1:8080"
TIMEOUT = 3
WAIT_SECONDS = 30
failures = 0


def check(name, condition, detail=""):
    global failures
    if condition:
        print(f"PASS: {name}")
    else:
        failures += 1
        print(f"FAIL: {name}" + (f" - {detail}" if detail else ""))


def get(path):
    with urllib.request.urlopen(BASE + path, timeout=TIMEOUT) as r:
        return r.status, json.loads(r.read().decode())


def wait_ready():
    deadline = time.time() + WAIT_SECONDS
    while time.time() < deadline:
        try:
            status, body = get("/ready")
            if status == 200 and body.get("status") == "ready":
                return True
        except Exception:
            pass
        time.sleep(1)
    return False


print("=== BARQ Validation ===")

check("NGINX public access", wait_ready(), "readiness timeout")

try:
    status, body = get("/")
    check("GET /", status == 200)
except Exception as e:
    check("GET /", False, str(e))

for path in ["/health", "/ready", "/instance", "/counter"]:
    try:
        status, body = get(path)
        check(f"GET {path}", status == 200, f"HTTP {status}")
    except Exception as e:
        check(f"GET {path}", False, str(e))

try:
    status, body = get("/records")
    check("GET /records", status == 200 and isinstance(body.get("records"), list))
except Exception as e:
    check("GET /records", False, str(e))

try:
    req = urllib.request.Request(
        BASE + "/records",
        data=json.dumps({"title": "validation-test"}).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
        body = json.loads(r.read().decode())
        check("POST /records", r.status == 201 and "record" in body)
except Exception as e:
    check("POST /records", False, str(e))

try:
    # Prove the two backend identities exist behind NGINX.
    identities = set()
    for _ in range(10):
        status, body = get("/instance")
        if status == 200:
            identities.add(body.get("instance_id") or body.get("instance"))
    check(
        "Both backend instances serve traffic",
        {"app-01", "app-02"}.issubset(identities),
        f"observed={sorted(identities)}",
    )
except Exception as e:
    check("Both backend instances serve traffic", False, str(e))

try:
    ps = __import__("subprocess").run(
        ["docker", "compose", "-p", "barq-assessment", "ps", "--format", "json"],
        capture_output=True,
        text=True,
        timeout=10,
        check=True,
    )
    services = []
    for line in ps.stdout.splitlines():
        if line.strip():
            services.append(json.loads(line))

    names = {x.get("Service") for x in services}
    check(
        "Required services exist",
        {"app-01", "app-02", "nginx", "postgres", "redis"}.issubset(names),
        f"services={sorted(names)}",
    )

    published = []
    for x in services:
        if x.get("Service") in {"app-01", "app-02", "postgres", "redis"}:
            ports = x.get("Publishers") or []
            host_ports = [
                p for p in ports
                if p.get("PublishedPort") > 0
            ]
            if host_ports:
                published.append(x.get("Service"))

    check("No prohibited host ports", not published, f"published={published}")
except Exception as e:
    check("Docker service/port checks", False, str(e))

try:
    backend = __import__("subprocess").run(
        ["docker", "network", "inspect", "barq-assessment_backend"],
        capture_output=True,
        text=True,
        timeout=10,
        check=True,
    )
    data = json.loads(backend.stdout)[0]
    containers = data.get("Containers", {})
    names = {v.get("Name") for v in containers.values()}
    check(
        "Backend network isolation",
        {"app-01", "app-02", "postgres", "redis"}.issubset(names)
        and "nginx" not in names,
        f"backend={sorted(names)}",
    )
except Exception as e:
    check("Backend network isolation", False, str(e))

print(f"\nValidation finished: {failures} failure(s)")
sys.exit(1 if failures else 0)

