import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from ehr.auth import (
    get_current_demo_identity,
    require_patient_access,
    resolve_demo_identity,
)
from ehr.exceptions import (
    PatientAccessDeniedError,
    PatientNotFoundError,
    UnknownDemoUserError,
)
from ehr.models import DemoIdentity
from ehr.retrieval import get_patient_profile


def test_resolve_known_demo_identity():
    identity = resolve_demo_identity('demo-user-pat002')
    assert identity.user_id == 'demo-user-pat002'
    assert identity.allowed_patient_ids == frozenset({'PAT-002'})


def test_resolve_unknown_demo_identity():
    with pytest.raises(UnknownDemoUserError):
        resolve_demo_identity('not-a-user')


def test_patient_id_is_not_authorization():
    identity = resolve_demo_identity('demo-user-pat001')
    require_patient_access(identity, 'PAT-001')
    with pytest.raises(PatientAccessDeniedError) as denied:
        require_patient_access(identity, 'PAT-002')
    assert denied.value.patient_id == 'PAT-002'
    assert denied.value.user_id == 'demo-user-pat001'


def test_cross_patient_retrieval_denied(identity_pat001):
    with pytest.raises(PatientAccessDeniedError):
        get_patient_profile(identity_pat001, 'PAT-002')
    with pytest.raises(PatientAccessDeniedError):
        get_patient_profile(identity_pat001, 'PAT-003')


def test_denied_before_unknown_patient_lookup(identity_pat001):
    '''Authorization is checked before dataset lookup, so a guessed ID is not an access grant.'''
    with pytest.raises(PatientAccessDeniedError):
        get_patient_profile(identity_pat001, 'PAT-999')
    with pytest.raises(PatientNotFoundError):
        get_patient_profile(
            DemoIdentity(
                user_id='demo-user-pat001',
                allowed_patient_ids=frozenset({'PAT-999'})
            ),
            'PAT-999'
        )


def _demo_app() -> FastAPI:
    app = FastAPI()

    @app.get('/ehr/patients/{patient_id}/profile')
    def profile(
        patient_id: str,
        identity: DemoIdentity = Depends(get_current_demo_identity)
    ):
        result = get_patient_profile(identity, patient_id)
        return {
            'patient_id': result.patient_id,
            'full_name': result.demographics.full_name
        }

    return app


def test_fastapi_dependency_allows_matching_patient():
    client = TestClient(_demo_app())
    response = client.get(
        '/ehr/patients/PAT-001/profile',
        headers={'X-Demo-User': 'demo-user-pat001'}
    )
    assert response.status_code == 200
    assert response.json()['patient_id'] == 'PAT-001'


def test_fastapi_dependency_denies_cross_patient_access():
    client = TestClient(_demo_app())
    with pytest.raises(PatientAccessDeniedError):
        client.get(
            '/ehr/patients/PAT-002/profile',
            headers={'X-Demo-User': 'demo-user-pat001'}
        )


def test_fastapi_dependency_rejects_missing_and_unknown_identity():
    client = TestClient(_demo_app())
    missing = client.get('/ehr/patients/PAT-001/profile')
    assert missing.status_code == 401
    unknown = client.get(
        '/ehr/patients/PAT-001/profile',
        headers={'X-Demo-User': 'attacker'}
    )
    assert unknown.status_code == 401
