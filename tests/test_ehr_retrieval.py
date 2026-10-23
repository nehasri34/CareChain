import pytest

from ehr.exceptions import MissingPatientDataError, PatientNotFoundError
from ehr.models import Allergy, DemoIdentity, LabResult, Medication, PatientProfile
from ehr.retrieval import (
    get_allergies,
    get_diagnoses,
    get_lab_results,
    get_medications,
    get_patient_profile,
)


def test_get_patient_profile_success(identity_pat001):
    profile = get_patient_profile(identity_pat001, 'PAT-001')
    assert isinstance(profile, PatientProfile)
    assert profile.patient_id == 'PAT-001'
    assert profile.demographics.full_name == 'Mira Langford'
    assert profile.demographics.date_of_birth == '1978-06-21'


def test_get_medications_success(identity_pat001):
    medications = get_medications(identity_pat001, 'PAT-001')
    assert len(medications) == 2
    assert all(isinstance(item, Medication) for item in medications)
    names = {item.name for item in medications}
    assert names == {'metformin', 'atorvastatin'}


def test_get_diagnoses_success(identity_pat001):
    diagnoses = get_diagnoses(identity_pat001, 'PAT-001')
    codes = {item.code for item in diagnoses}
    assert 'E11.9' in codes
    assert 'E78.5' in codes


def test_get_allergies_success(identity_pat001):
    allergies = get_allergies(identity_pat001, 'PAT-001')
    assert allergies == [
        Allergy(substance='penicillin', reaction='urticaria', severity='moderate')
    ]


def test_get_lab_results_include_units_and_ranges(identity_pat001):
    labs = get_lab_results(identity_pat001, 'PAT-001')
    assert labs[0] == LabResult(
        test_name='HbA1c',
        value=7.1,
        unit='%',
        reference_range='4.0-5.6',
        collected_on='2026-08-15'
    )
    assert labs[1].unit == 'mg/dL'
    assert labs[1].reference_range == '<100'


def test_unknown_patient_id_raises():
    identity = DemoIdentity(
        user_id='demo-user-pat001',
        allowed_patient_ids=frozenset({'PAT-001', 'PAT-999'})
    )
    with pytest.raises(PatientNotFoundError) as exc:
        get_patient_profile(identity, 'PAT-999')
    assert exc.value.patient_id == 'PAT-999'


def test_missing_allergies_field_raises(identity_pat002):
    with pytest.raises(MissingPatientDataError) as exc:
        get_allergies(identity_pat002, 'PAT-002')
    assert exc.value.field == 'allergies'
    assert exc.value.patient_id == 'PAT-002'


def test_missing_lab_results_field_raises(identity_pat003):
    with pytest.raises(MissingPatientDataError) as exc:
        get_lab_results(identity_pat003, 'PAT-003')
    assert exc.value.field == 'lab_results'


def test_other_sections_still_work_when_allergies_missing(identity_pat002):
    profile = get_patient_profile(identity_pat002, 'PAT-002')
    assert profile.demographics.full_name == 'Julian Okonkwo'
    meds = get_medications(identity_pat002, 'PAT-002')
    assert meds[0].name == 'albuterol'
