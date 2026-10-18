# python_gateway — FastAPI worker for Spring Boot

Thin HTTP layer over [`python_filter`](../python_filter/) and [`python_derived`](../python_derived/). Spring Boot (default profile) calls **`POST /jobs`** or **`POST /derived-jobs`**, then **`GET /jobs/{id}`** on `PYTHON_SERVICE_BASE_URL` (default `http://127.0.0.1:8000`).

## Setup

From repository root (same as `python_filter`):

```bash
pip install -r python_filter/requirements.txt -r python_gateway/requirements.txt
```

## Run

```bash
cd /path/to/pcfps
PYTHONPATH=. uvicorn python_gateway.main:app --host 0.0.0.0 --port 8000
```

- **`GET /health`** — liveness.
- **`POST /jobs`** — body fields match `delta/1.req/integration-python/entity.md` (snake_case). Writes **`output_result_path`** (must end in `.las` or `.laz`), typically `{taskOutputDir}/filtered.las`.
- **`POST /derived-jobs`** — segment/classify on an existing LAS: `job_kind` (`segment` \| `classify`), `algorithm`, merged snake_case params in the same JSON body. Writes **`output_result_path`** (typically `{taskOutputDir}/derived.las`).
- **`GET /jobs/{external_python_job_uuid}`** — `lifecycle_state_machine_token`: `RUNNING` | `SUCCEEDED` | `FAILED`.

Jobs run in a **single-worker** thread pool so large LAS runs do not overlap by default.

## Without this service

Start Spring with **`--spring.profiles.active=mock-python`** to use `MockPythonGatewayService` (no real filtering; `TaskService` falls back to minimal ASCII PLY for `FILTERED_LAS`).
