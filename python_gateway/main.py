"""
FastAPI job API for LAS filtering. Spring Boot calls POST /jobs then GET /jobs/{id}.

Run from repository root (``python_derived`` shares deps with ``python_filter``)::

    pip install -r python_gateway/requirements.txt -r python_filter/requirements.txt
    PYTHONPATH=. uvicorn python_gateway.main:app --host 0.0.0.0 --port 8000
"""

from __future__ import annotations

import logging
import threading
import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any, Dict, Literal, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, model_validator

from python_derived.pipeline import process_derived
from python_filter.pipeline import process

_LOGGER = logging.getLogger(__name__)

_DERIVED_RESERVED_BODY_KEYS: frozenset[str] = frozenset(
    {
        "external_business_task_id",
        "input_las_path",
        "output_result_path",
        "job_kind",
        "algorithm",
    }
)

_executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="las-filter-job")
_job_lock = threading.Lock()
_job_state_map: Dict[str, Dict[str, Any]] = {}


class JobSubmitPayload(BaseModel):
    """JSON body aligned with delta ``integration-python`` contract (snake_case)."""

    external_business_task_id: str = Field(..., description="Spring task UUID as string")
    input_las_path: str
    output_result_path: str = Field(
        ...,
        description="Absolute path to output LAS/LAZ file (e.g. .../filtered.las)",
    )
    filter_method: Literal["sor", "ror"] = "sor"
    sor_neighbor_count: Optional[int] = Field(default=20, ge=1)
    sor_std_ratio: Optional[float] = Field(default=1.0, gt=0)
    ror_radius: Optional[float] = Field(default=None, gt=0)
    ror_min_neighbors: Optional[int] = Field(default=None, ge=0)

    @model_validator(mode="after")
    def validate_method_parameters(self) -> JobSubmitPayload:
        if self.filter_method == "ror":
            if self.ror_radius is None or self.ror_min_neighbors is None:
                raise ValueError("ror_radius and ror_min_neighbors are required when filter_method is ror")
        return self


def _run_filter_job_worker(
    job_uuid: str,
    external_business_task_id: str,
    input_las_path: str,
    output_result_path: str,
    filter_method: str,
    sor_neighbor_count: Optional[int],
    sor_std_ratio: Optional[float],
    ror_radius: Optional[float],
    ror_min_neighbors: Optional[int],
) -> None:
    input_path = Path(input_las_path)
    output_path = Path(output_result_path)
    try:
        if not input_path.is_file():
            raise FileNotFoundError(f"Input LAS not found or not a file: {input_path}")
        output_path.parent.mkdir(parents=True, exist_ok=True)

        filter_kwargs: dict[str, Any] = {}
        if filter_method == "sor":
            filter_kwargs["k"] = sor_neighbor_count if sor_neighbor_count is not None else 20
            filter_kwargs["std_ratio"] = sor_std_ratio if sor_std_ratio is not None else 1.0
        else:
            filter_kwargs["radius"] = ror_radius
            filter_kwargs["min_neighbors"] = ror_min_neighbors

        metrics_mapping = process(
            str(input_path),
            str(output_path),
            filtering_method_keyword=filter_method,
            **filter_kwargs,
        )
        filtered_absolute_path = str(output_path.resolve())
        with _job_lock:
            _job_state_map[job_uuid] = {
                "external_python_job_uuid": job_uuid,
                "lifecycle_state_machine_token": "SUCCEEDED",
                "metrics_bundle": {str(key): value for key, value in metrics_mapping.items()},
                "artifact_path_dictionary": {"FILTERED_LAS": filtered_absolute_path},
                "error_code_stable_string_optional": None,
                "error_message_human_plain_optional": None,
            }
        _LOGGER.info(
            "Job finished job_uuid=%s external_business_task_id=%s output=%s",
            job_uuid,
            external_business_task_id,
            filtered_absolute_path,
        )
    except Exception as exception:
        _LOGGER.exception("Job failed job_uuid=%s", job_uuid)
        with _job_lock:
            _job_state_map[job_uuid] = {
                "external_python_job_uuid": job_uuid,
                "lifecycle_state_machine_token": "FAILED",
                "metrics_bundle": None,
                "artifact_path_dictionary": None,
                "error_code_stable_string_optional": "FILTER_RUNTIME_ERROR",
                "error_message_human_plain_optional": str(exception),
            }


app = FastAPI(title="PCFPS Python filter gateway", version="0.1.0")


@app.get("/health")
def health_check() -> Dict[str, str]:
    return {"status": "UP"}


@app.post("/jobs", status_code=202)
def submit_filter_job(payload: JobSubmitPayload) -> Dict[str, str]:
    input_path = Path(payload.input_las_path)
    if not input_path.is_file():
        _LOGGER.warning("Reject job: missing input path=%s", input_path)
        raise HTTPException(
            status_code=400,
            detail={"code": "LAS_IO_PATH_UNREADABLE", "message": f"Input path is not a readable file: {input_path}"},
        )
    output_suffix = Path(payload.output_result_path).suffix.lower()
    if output_suffix not in {".las", ".laz"}:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "FILTER_PAYLOAD_INVALID",
                "message": "output_result_path must end with .las or .laz",
            },
        )

    job_uuid = str(uuid.uuid4())
    with _job_lock:
        _job_state_map[job_uuid] = {
            "external_python_job_uuid": job_uuid,
            "lifecycle_state_machine_token": "RUNNING",
            "metrics_bundle": None,
            "artifact_path_dictionary": None,
            "error_code_stable_string_optional": None,
            "error_message_human_plain_optional": None,
            "task_trace": payload.external_business_task_id,
        }

    _LOGGER.info(
        "Accepted job job_uuid=%s external_business_task_id=%s input=%s output=%s method=%s",
        job_uuid,
        payload.external_business_task_id,
        payload.input_las_path,
        payload.output_result_path,
        payload.filter_method,
    )
    _executor.submit(
        _run_filter_job_worker,
        job_uuid,
        payload.external_business_task_id,
        payload.input_las_path,
        payload.output_result_path,
        payload.filter_method,
        payload.sor_neighbor_count,
        payload.sor_std_ratio,
        payload.ror_radius,
        payload.ror_min_neighbors,
    )
    return {"external_python_job_uuid": job_uuid}


def _run_derived_job_worker(
    job_uuid: str,
    external_business_task_id: str,
    input_las_path: str,
    output_result_path: str,
    job_kind: str,
    algorithm: str,
    algorithm_parameter_mapping: Dict[str, Any],
) -> None:
    input_path = Path(input_las_path)
    output_path = Path(output_result_path)
    try:
        if not input_path.is_file():
            raise FileNotFoundError(f"Input LAS not found or not a file: {input_path}")
        output_path.parent.mkdir(parents=True, exist_ok=True)

        metrics_mapping = process_derived(
            str(input_path),
            str(output_path),
            job_kind=job_kind,
            algorithm=algorithm,
            algorithm_parameter_mapping=algorithm_parameter_mapping,
        )
        derived_absolute_path = str(output_path.resolve())
        with _job_lock:
            _job_state_map[job_uuid] = {
                "external_python_job_uuid": job_uuid,
                "lifecycle_state_machine_token": "SUCCEEDED",
                "metrics_bundle": {str(key): value for key, value in metrics_mapping.items()},
                "artifact_path_dictionary": {"DERIVED_LAS": derived_absolute_path},
                "error_code_stable_string_optional": None,
                "error_message_human_plain_optional": None,
            }
        _LOGGER.info(
            "Derived job finished job_uuid=%s external_business_task_id=%s output=%s",
            job_uuid,
            external_business_task_id,
            derived_absolute_path,
        )
    except Exception as exception:
        _LOGGER.exception("Derived job failed job_uuid=%s", job_uuid)
        with _job_lock:
            _job_state_map[job_uuid] = {
                "external_python_job_uuid": job_uuid,
                "lifecycle_state_machine_token": "FAILED",
                "metrics_bundle": None,
                "artifact_path_dictionary": None,
                "error_code_stable_string_optional": "DERIVED_RUNTIME_ERROR",
                "error_message_human_plain_optional": str(exception),
            }


@app.post("/derived-jobs", status_code=202)
def submit_derived_job(payload: Dict[str, Any]) -> Dict[str, str]:
    for required_key in ("external_business_task_id", "input_las_path", "output_result_path", "job_kind", "algorithm"):
        if required_key not in payload:
            raise HTTPException(
                status_code=400,
                detail={"code": "DERIVED_PAYLOAD_INVALID", "message": f"Missing field: {required_key}"},
            )
    input_path = Path(str(payload["input_las_path"]))
    if not input_path.is_file():
        _LOGGER.warning("Reject derived job: missing input path=%s", input_path)
        raise HTTPException(
            status_code=400,
            detail={"code": "LAS_IO_PATH_UNREADABLE", "message": f"Input path is not a readable file: {input_path}"},
        )
    output_suffix = Path(str(payload["output_result_path"])).suffix.lower()
    if output_suffix not in {".las", ".laz"}:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "DERIVED_PAYLOAD_INVALID",
                "message": "output_result_path must end with .las or .laz",
            },
        )
    job_kind = str(payload["job_kind"]).lower().strip()
    if job_kind not in {"segment", "classify", "semantic_prune"}:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "DERIVED_PAYLOAD_INVALID",
                "message": "job_kind must be segment, classify, or semantic_prune",
            },
        )
    algorithm = str(payload["algorithm"]).lower().strip()
    algorithm_parameter_mapping: Dict[str, Any] = {
        key: value for key, value in payload.items() if key not in _DERIVED_RESERVED_BODY_KEYS
    }

    job_uuid = str(uuid.uuid4())
    with _job_lock:
        _job_state_map[job_uuid] = {
            "external_python_job_uuid": job_uuid,
            "lifecycle_state_machine_token": "RUNNING",
            "metrics_bundle": None,
            "artifact_path_dictionary": None,
            "error_code_stable_string_optional": None,
            "error_message_human_plain_optional": None,
            "task_trace": str(payload["external_business_task_id"]),
        }

    _LOGGER.info(
        "Accepted derived job job_uuid=%s external_business_task_id=%s input=%s output=%s job_kind=%s algorithm=%s",
        job_uuid,
        payload["external_business_task_id"],
        payload["input_las_path"],
        payload["output_result_path"],
        job_kind,
        algorithm,
    )
    _executor.submit(
        _run_derived_job_worker,
        job_uuid,
        str(payload["external_business_task_id"]),
        str(payload["input_las_path"]),
        str(payload["output_result_path"]),
        job_kind,
        algorithm,
        algorithm_parameter_mapping,
    )
    return {"external_python_job_uuid": job_uuid}


@app.get("/jobs/{external_python_job_uuid}")
def get_job_status(external_python_job_uuid: str) -> Dict[str, Any]:
    with _job_lock:
        snapshot = _job_state_map.get(external_python_job_uuid)
    if snapshot is None:
        raise HTTPException(status_code=404, detail={"code": "JOB_NOT_FOUND", "message": external_python_job_uuid})
    return {
        "external_python_job_uuid": snapshot["external_python_job_uuid"],
        "lifecycle_state_machine_token": snapshot["lifecycle_state_machine_token"],
        "metrics_bundle": snapshot["metrics_bundle"],
        "artifact_path_dictionary": snapshot["artifact_path_dictionary"],
        "error_code_stable_string_optional": snapshot["error_code_stable_string_optional"],
        "error_message_human_plain_optional": snapshot["error_message_human_plain_optional"],
    }
