'''
Prototype authorization for the CareChain EHR data layer.

This is NOT production authentication.
- There are no passwords, sessions, tokens, or identity providers.
- Demo callers present a known user id (X-Demo-User when used with FastAPI).
- Access is decided only from that authenticated demo identity's allow-list.
- A user-supplied patient ID is never treated as proof of access.
'''

from fastapi import Header, HTTPException

from ehr.exceptions import PatientAccessDeniedError, UnknownDemoUserError
from ehr.models import DemoIdentity

# Each demo user may access only the listed fictional patient IDs.
DEMO_ACCESS = {
    'demo-user-pat001': frozenset({'PAT-001'}),
    'demo-user-pat002': frozenset({'PAT-002'}),
    'demo-user-pat003': frozenset({'PAT-003'}),
}


def resolve_demo_identity(user_id: str) -> DemoIdentity:
    allowed = DEMO_ACCESS.get(user_id)
    if allowed is None:
        raise UnknownDemoUserError(user_id)
    return DemoIdentity(user_id=user_id, allowed_patient_ids=allowed)


def require_patient_access(identity: DemoIdentity, patient_id: str) -> None:
    '''Raise if the authenticated identity is not allowed to read this patient.'''
    if patient_id not in identity.allowed_patient_ids:
        raise PatientAccessDeniedError(identity.user_id, patient_id)


def get_current_demo_identity(
    x_demo_user: str | None = Header(default=None, alias='X-Demo-User')
) -> DemoIdentity:
    '''
    FastAPI dependency: map X-Demo-User to a DemoIdentity.

    Prototype only. Do not use this pattern for real clinical systems.
    '''
    if not x_demo_user or not x_demo_user.strip():
        raise HTTPException(
            status_code=401,
            detail='Missing X-Demo-User header. Prototype auth only; not production.'
        )
    try:
        return resolve_demo_identity(x_demo_user.strip())
    except UnknownDemoUserError as exc:
        raise HTTPException(
            status_code=401,
            detail=str(exc)
        ) from exc
