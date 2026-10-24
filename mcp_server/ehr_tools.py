'''MCP wrappers around the EHR retrieval functions.

Identity comes from get_mcp_demo_identity() (operator env on the MCP
process). Tool arguments never include a user identity field.
'''

from dataclasses import asdict
from typing import Any, Callable

from ehr.auth import get_mcp_demo_identity
from ehr.exceptions import (
    MissingPatientDataError,
    PatientAccessDeniedError,
    PatientNotFoundError,
    UnknownDemoUserError,
)
from ehr.models import DemoIdentity
from ehr.retrieval import (
    get_allergies,
    get_diagnoses,
    get_lab_results,
    get_medications,
    get_patient_profile,
)

ERROR_CODES = {
    PatientNotFoundError: 'patient_not_found',
    MissingPatientDataError: 'missing_patient_data',
    PatientAccessDeniedError: 'patient_access_denied',
    UnknownDemoUserError: 'unknown_demo_user',
}

RetrieveFn = Callable[[DemoIdentity, str], Any]


def _serialize(value: Any) -> Any:
    if hasattr(value, '__dataclass_fields__'):
        return asdict(value)
    if isinstance(value, list):
        return [_serialize(item) for item in value]
    return value


def run_patient_tool(retrieve: RetrieveFn, patient_id: str) -> dict[str, Any]:
    try:
        identity = get_mcp_demo_identity()
        data = retrieve(identity, patient_id)
    except tuple(ERROR_CODES) as exc:
        payload: dict[str, Any] = {
            'ok': False,
            'error': ERROR_CODES[type(exc)],
            'message': str(exc),
            'data': None,
        }
        if getattr(exc, 'patient_id', None) is not None:
            payload['patient_id'] = exc.patient_id
        if getattr(exc, 'field', None) is not None:
            payload['field'] = exc.field
        if getattr(exc, 'user_id', None) is not None:
            payload['user_id'] = exc.user_id
        return payload

    return {
        'ok': True,
        'error': None,
        'message': None,
        'patient_id': patient_id,
        'data': _serialize(data),
    }


def get_patient_profile_tool(patient_id: str) -> dict[str, Any]:
    return run_patient_tool(get_patient_profile, patient_id)


def get_patient_medications_tool(patient_id: str) -> dict[str, Any]:
    return run_patient_tool(get_medications, patient_id)


def get_patient_allergies_tool(patient_id: str) -> dict[str, Any]:
    return run_patient_tool(get_allergies, patient_id)


def get_patient_diagnoses_tool(patient_id: str) -> dict[str, Any]:
    return run_patient_tool(get_diagnoses, patient_id)


def get_patient_lab_results_tool(patient_id: str) -> dict[str, Any]:
    return run_patient_tool(get_lab_results, patient_id)
