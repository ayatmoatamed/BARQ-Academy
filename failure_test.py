#!/usr/bin/env python3

import json
import subprocess
import time
import urllib.request

BASE = "http://127.0.0.1:8080"
REQUESTS = 20
TIMEOUT = 2


def request_instance():
    try:
        with urllib.request.urlopen(
            BASE + "/instance",
            timeout=TIMEOUT
        ) as response:
            body = json.loads(response.read().decode())
            return response.status, body
    except Exception as exc:
        return None, str(exc)


def wait_for_instance(instance, timeout=30):
    deadline = time.time() + timeout

    while time.time() < deadline:
        status, body = request_instance()

        if status == 200 and body.get("instance_id") == instance:
            return True

        time.sleep(1)

    return False


print("=== BARQ Failure / Recovery Test ===")

# Stop app-01
print("Stopping app-01...")
subprocess.run(
    ["docker", "stop", "app-01"],
    check=True,
    capture_output=True,
    text=True,
)

try:
    successes = 0
    errors = 0

    print(f"Sending {REQUESTS} requests while app-01 is stopped...")

    for _ in range(REQUESTS):
        status, body = request_instance()

        if status == 200:
            successes += 1
        else:
            errors += 1

    print(f"Traffic during failure: successes={successes}, errors={errors}")

    if successes == 0:
        print("FAIL: No traffic survived backend failure")
        raise SystemExit(1)

    print("PASS: Traffic remained available during app-01 failure")

finally:
    print("Restoring app-01...")
    subprocess.run(
        ["docker", "start", "app-01"],
        check=True,
        capture_output=True,
        text=True,
    )

print("Waiting for app-01 to recover...")

if not wait_for_instance("app-01"):
    print("FAIL: app-01 did not recover")
    raise SystemExit(1)

print("PASS: app-01 recovered and serves requests")
print("Failure/recovery test completed successfully")
