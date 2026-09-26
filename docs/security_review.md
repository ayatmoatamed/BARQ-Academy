# Security Review

## 1. Secrets in Image

**Risk:** Credentials copied into an image can remain in image layers.

**Implemented improvement:** Removed the application environment file from the Dockerfile COPY instructions.

**Production improvement:** Use a dedicated secrets manager such as AWS Secrets Manager, SSM Parameter Store, or another approved secret-management system.

---

## 2. Secrets in Git

**Risk:** Committing application credentials exposes them to repository users and potentially to public systems.

**Implemented improvement:** The local application environment file is not tracked by Git.

**Production improvement:** Enforce secret scanning and repository protection rules.

---

## 3. Database Host Exposure

**Risk:** Publishing PostgreSQL directly to the host increases the attack surface.

**Implemented improvement:** PostgreSQL has no host port mapping.

**Production improvement:** Keep the database inside a private network or private subnet and restrict access using firewall/security-group rules.

---

## 4. Redis Host Exposure

**Risk:** Directly exposing Redis increases the attack surface.

**Implemented improvement:** Redis has no host port mapping.

**Production improvement:** Keep Redis private and restrict access to trusted application components.

---

## 5. Root Container

**Risk:** A compromised process running as root has greater privileges inside the container.

**Implemented improvement:** The application runs as the dedicated `app` user.

**Production improvement:** Continue using least privilege and consider additional container security controls.

---

## 6. Network Isolation

**Risk:** Putting all services on one network makes unnecessary service-to-service access possible.

**Implemented improvement:** Frontend and backend networks are separated. The backend network is internal.

**Production improvement:** Apply network policies or cloud security controls where supported.

---

## 7. Image Security

**Risk:** Vulnerable dependencies or base images can introduce known security vulnerabilities.

**Implemented improvement:** Base images are pinned by digest in the Compose/Docker configuration.

**Production improvement:** Add image vulnerability scanning to CI and maintain an image update process.

---

## 8. Resource Exhaustion

**Risk:** A service can consume excessive CPU or memory and affect other services.

**Implemented improvement:** CPU and memory limits were added.

**Production improvement:** Set values based on measured workload requirements and monitor resource usage.

---

## 9. Backup Protection

**Risk:** Database backups can contain sensitive application data.

**Implemented improvement:** Backups are kept outside Git and are used only for the disposable lab.

**Production improvement:** Encrypt backups, restrict access, and store them off-host with retention policies.

---

## 10. Logging and Sensitive Data

**Risk:** Logs can accidentally contain credentials or sensitive application data.

**Implemented improvement:** Investigation uses application and service logs for troubleshooting.

**Production improvement:** Apply log redaction, centralized storage, access control, and retention policies.

---

## 11. Availability

**Risk:** The application currently depends on a small number of containers and local infrastructure.

**Implemented improvement:** Two application instances and failure/recovery testing were implemented.

**Production improvement:** Use multiple hosts or availability zones, health-aware load balancing, and highly available data services where required.

---

## 12. TLS

**Risk:** The lab uses HTTP locally.

**Implemented improvement:** None required for the local disposable lab.

**Production improvement:** Terminate TLS at the production load balancer or ingress and redirect HTTP traffic to HTTPS where appropriate.

---

## Implemented Fixes vs Production Plans

The implemented changes above are limited to the internship lab.

Production recommendations are intentionally separated from implemented fixes so that the repository does not claim that production controls were implemented when they were not.
