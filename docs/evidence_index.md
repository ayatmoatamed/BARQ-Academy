# Evidence Index

This document maps task requirements to repository evidence.

Video timestamps and final commit hashes will be filled after the recorded demonstration and final commits.

| Requirement | Evidence | Commit | Video Timestamp |
|---|---|---|---|
| Application health | Docker healthcheck and `/health` | To be filled | To be filled |
| Application readiness | `/ready` and dependency checks | To be filled | To be filled |
| Network isolation | `docker-compose.yml` and network inspection | To be filled | To be filled |
| Host port restriction | `docker-compose.yml` | To be filled | To be filled |
| Non-root application | `Dockerfile` | To be filled | To be filled |
| Secrets outside image | `Dockerfile` and environment configuration | To be filled | To be filled |
| PostgreSQL persistence | `postgres-data` volume and persistence test | To be filled | To be filled |
| Redis persistence | AOF configuration and `redis-data` volume | To be filled | To be filled |
| Resource limits | `docker-compose.yml` | To be filled | To be filled |
| Automated validation | `validate.py` | To be filled | To be filled |
| Failure and recovery | `failure_test.py` | To be filled | To be filled |
| PostgreSQL backup | `backup.sh` | To be filled | To be filled |
| PostgreSQL restore | `restore.sh` | To be filled | To be filled |
| CI | `.github/workflows/ci.yml` | To be filled | To be filled |
| Historical log analysis | `docs/log_analysis.md` | To be filled | To be filled |
| Design decisions | `docs/decisions.md` | To be filled | To be filled |
| Security review | `docs/security_review.md` | To be filled | To be filled |
| AI disclosure | `AI_USAGE.md` | To be filled | To be filled |
| Architecture | `architecture.png` or `architecture.pdf` | To be filled | To be filled |
| Runtime challenge | `video_challenge.sh` | To be filled | To be filled |
| Public port change | Final Part 5 state | To be filled | To be filled |
| Third application instance | Final Part 5 state | To be filled | To be filled |

## Evidence Rules

Evidence must correspond to the actual repository and recorded video.

No commit hashes or video timestamps should be fabricated.

Documentation-only changes should be identified as such when relevant.
