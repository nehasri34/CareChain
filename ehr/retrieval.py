from ehr.auth import require_patient_access
from ehr.exceptions import MissingPatientDataError
from ehr.models import (
    Allergy,
    DemoIdentity,
    Demographics,
    Diagnosis,
    LabResult,
    Medication,
    PatientProfile,
)
from ehr.store import get_patient_record


def _authorized_record(identity: DemoIdentity, patient_id: str) -> dict:
    require_patient_access(identity, patient_id)
    return get_patient_record(patient_id)


def _require_field(record: dict, field: str) -> object:
    if field not in record:
        raise MissingPatientDataError(record['patient_id'], field)
    return record[field]


def get_patient_profile(identity: DemoIdentity, patient_id: str) -> PatientProfile:
    record = _authorized_record(identity, patient_id)
    demographics = _require_field(record, 'demographics')
    return PatientProfile(
        patient_id=record['patient_id'],
        demographics=Demographics(**demographics)
    )


def get_medications(identity: DemoIdentity, patient_id: str) -> list[Medication]:
    record = _authorized_record(identity, patient_id)
    medications = _require_field(record, 'medications')
    return [Medication(**item) for item in medications]


def get_diagnoses(identity: DemoIdentity, patient_id: str) -> list[Diagnosis]:
    record = _authorized_record(identity, patient_id)
    diagnoses = _require_field(record, 'diagnoses')
    return [Diagnosis(**item) for item in diagnoses]


def get_allergies(identity: DemoIdentity, patient_id: str) -> list[Allergy]:
    record = _authorized_record(identity, patient_id)
    allergies = _require_field(record, 'allergies')
    return [Allergy(**item) for item in allergies]


def get_lab_results(identity: DemoIdentity, patient_id: str) -> list[LabResult]:
    record = _authorized_record(identity, patient_id)
    lab_results = _require_field(record, 'lab_results')
    return [LabResult(**item) for item in lab_results]
