# Log Analysis

## 1. Log Files Analyzed

The investigation used the three supplied historical logs:

* `logs/access.log`
* `logs/application.log`
* `logs/error.log`

The original log files were kept unchanged.

## 2. Access Log Analysis

`logs/access.log` contains **726 request entries**.

Each entry includes a unique `request_id`, HTTP method, path, response status, upstream address and request duration.

Example request IDs such as `lab-000001`, `lab-000002` and `lab-000003` can be correlated with the application log.

The access log shows traffic being handled by both application instances:

* `app-01`
* `app-02`

The requests include health and readiness checks as well as application endpoints such as `/`, `/health`, `/ready`, `/records` and `/counter`.

## 3. Application Log Analysis

`logs/application.log` contains **730 entries**.

The observed levels include:

* `INFO`
* `WARN`
* `ERROR`

The log contains application-level request records with the same `request_id` values used by the access log.

This allows an individual request to be followed from NGINX to the application instance that processed it.

The logs also show requests being handled by both `app-01` and `app-02`.

## 4. Error Log Analysis

`logs/error.log` contains **68 entries**.

The main observed pattern is:

`connect() failed (111: Connection refused) while connecting to upstream`

The errors occurred while NGINX was attempting to connect to an upstream application instance.

For example, request IDs including `lab-000122`, `lab-000124`, `lab-000126`, `lab-000128` and later requests show connection failures to:

`172.23.0.12:8080`

This provides evidence of an upstream availability problem rather than an HTTP application error returned by the backend.

## 5. Correlation Between Logs

The logs use `request_id` as the correlation key.

For example:

* `lab-000001` appears in the access log.
* The same `lab-000001` appears in the application log.
* The application log identifies `app-01` as the instance that processed it.

The error log also contains request IDs, allowing NGINX connection failures to be correlated with individual requests.

### Avoiding Double-Counting

I treated the access log as the primary source for counting HTTP requests.

The application log was used to identify the backend instance and application-level result for the same request.

Therefore, an entry appearing in both logs was treated as **one request**, not two requests.

The `request_id` field provides the evidence needed to correlate these records.

## 6. Timeline / Failure Pattern

The early access-log entries show normal successful traffic.

At approximately **11:05 UTC**, the error log begins showing repeated `Connection refused` errors against the same upstream address:

`172.23.0.12:8080`

The affected paths include:

* `/health`
* `/ready`
* `/records`
* `/counter`
* `/instance`
* `/`

The repeated failures across different endpoints indicate that the problem was connectivity to the upstream application instance rather than one specific application endpoint.

## 7. Main Findings

### Finding 1 — Both application instances received traffic

The access and application logs identify both `app-01` and `app-02`.

This demonstrates that NGINX was distributing requests across the two backend instances.

### Finding 2 — An upstream instance became unreachable

The error log repeatedly reports `Connection refused` when NGINX attempted to connect to `172.23.0.12:8080`.

This is consistent with an unavailable or non-listening upstream application instance.

### Finding 3 — The failure affected multiple endpoints

The same connection-refused pattern occurred for health, readiness and application endpoints.

This indicates an upstream connectivity/availability issue rather than an endpoint-specific failure.

### Finding 4 — Request correlation is possible

The shared `request_id` between access and application logs provides a reliable way to correlate events without counting the same request multiple times.

## 8. Commands Used

The following commands were used during log investigation:

```bash
find logs -maxdepth 2 -type f -print
du -h logs/access.log logs/application.log logs/error.log
head -5 logs/access.log
head -5 logs/application.log
head -10 logs/error.log
```

The initial `awk` attempt was not used as evidence because the logs are JSON structured logs rather than the expected traditional NGINX combined-log format.

The JSON structure was therefore inspected directly before interpreting fields such as `status`, `request_id`, `instance_id` and `upstream`.

## 9. Conclusions

The historical logs show normal traffic through NGINX to both application instances followed by a period where one upstream became unreachable.

The strongest evidence is the repeated `Connection refused` messages in `error.log`, combined with the corresponding upstream address and request IDs.

The logs therefore support the conclusion that the observed failure was an upstream availability/connectivity problem.

No historical log entries were modified during the analysis.

