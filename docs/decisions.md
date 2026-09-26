# Design Decisions

## 1. NGINX as the Only Host-Published Service

**Decision:** Use NGINX as the only service published to the host.

**Reason:** NGINX is the public entry point and forwards requests to the application instances.

**Alternative:** Publish application ports directly.

**Trade-off:** NGINX becomes an entry-point dependency, but the application and data services remain isolated from direct host access.

---

## 2. Separate Frontend and Backend Networks

**Decision:** Use separate frontend and backend Docker networks.

**Reason:** NGINX only needs to communicate with the application layer. PostgreSQL and Redis should remain behind the application layer.

**Alternative:** Put all services on one network.

**Trade-off:** The two-network design is slightly more configuration, but provides better network isolation.

---

## 3. Internal Backend Network

**Decision:** Configure the backend network as internal.

**Reason:** PostgreSQL and Redis do not need direct host access.

**Alternative:** Publish database and Redis ports.

**Trade-off:** Troubleshooting from the host requires connecting through the application or Docker network instead of directly using host ports.

---

## 4. Non-Root Application User

**Decision:** Run the Flask application using the dedicated `app` user.

**Reason:** The application does not require root privileges.

**Alternative:** Run the container as root.

**Trade-off:** Running as a non-root user can require additional permission configuration, but reduces container privilege.

---

## 5. Runtime Environment Variables

**Decision:** Do not copy `config/app.env` into the Docker image.

**Reason:** The file contains credentials and should not become part of image layers.

**Alternative:** Copy the file during image build.

**Trade-off:** The runtime environment must provide the required variables, but credentials are kept outside the image.

---

## 6. PostgreSQL Named Volume

**Decision:** Store PostgreSQL data in a named Docker volume.

**Reason:** Database data must survive container recreation.

**Alternative:** Store data only inside the container filesystem.

**Trade-off:** The volume must be managed and backed up separately.

---

## 7. Redis AOF Persistence

**Decision:** Enable Redis append-only-file persistence and use a named volume.

**Reason:** This provides persistence beyond the lifetime of a Redis container.

**Alternative:** Run Redis without persistence.

**Trade-off:** Persistence introduces additional disk I/O and storage requirements.

---

## 8. Resource Limits

**Decision:** Configure CPU and memory limits for services.

**Reason:** A single container should not be allowed to consume unlimited resources.

**Alternative:** Leave resource usage unlimited.

**Trade-off:** Limits can cause a service to be constrained if the selected values are too low, so production values should be based on measurements.

---

## 9. Separate Health and Readiness

**Decision:** Use `/health` for container health and `/ready` for dependency readiness.

**Reason:** A process can be alive while still being unable to serve requests because a dependency is unavailable.

**Alternative:** Use only one endpoint.

**Trade-off:** Two checks add configuration but provide clearer failure information.

---

## 10. Automated Validation

**Decision:** Implement `validate.py` as an executable validation tool.

**Reason:** Important requirements should be repeatable and machine-checkable.

**Alternative:** Verify everything manually.

**Trade-off:** Automated checks improve repeatability but only cover the conditions explicitly implemented in the script.

---

## 11. Separate Failure Testing

**Decision:** Keep failure/recovery testing in `failure_test.py`.

**Reason:** Failure behavior should be tested independently from normal validation.

**Alternative:** Include failure testing inside the normal validation script.

**Trade-off:** A separate test is easier to run intentionally without making normal validation destructive.

---

## 12. Restore Into a Temporary Database

**Decision:** Restore backups into a temporary verification database.

**Reason:** Restore testing should not overwrite the application's main database.

**Alternative:** Restore directly into the application database.

**Trade-off:** The verification process requires creation and removal of an additional database, but avoids risking application data.

---

## Assumptions and Limitations

This is a disposable internship lab environment.

The configuration is not intended to represent a complete production deployment.

Production would require additional considerations such as external secret management, TLS, centralized logging, monitoring, highly available data services, off-host backups, and disaster recovery procedures.
