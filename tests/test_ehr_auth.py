import pytest
from fastapi import HTTPException

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


def test_fastapi_dependency_allows_matching_patient():
    identity = get_current_demo_identity(x_demo_user='demo-user-pat001')
    result = get_patient_profile(identity, 'PAT-001')
    assert result.patient_id == 'PAT-001'
    assert result.demographics.full_name == 'Mira Langford'


def test_fastapi_dependency_denies_cross_patient_access():
    identity = get_current_demo_identity(x_demo_user='demo-user-pat001')
    with pytest.raises(PatientAccessDeniedError):
        get_patient_profile(identity, 'PAT-002')


def test_fastapi_dependency_rejects_missing_and_unknown_identity():
    with pytest.raises(HTTPException) as missing:
        get_current_demo_identity(x_demo_user=None)
    assert missing.value.status_code == 401
    with pytest.raises(HTTPException) as unknown:
        get_current_demo_identity(x_demo_user='attacker')
    assert unknown.value.status_code == 401
