import pytest

from ehr.auth import resolve_demo_identity


@pytest.fixture
def identity_pat001():
    return resolve_demo_identity('demo-user-pat001')


@pytest.fixture
def identity_pat002():
    return resolve_demo_identity('demo-user-pat002')


@pytest.fixture
def identity_pat003():
    return resolve_demo_identity('demo-user-pat003')
