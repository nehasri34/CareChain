from dataclasses import dataclass


@dataclass(frozen=True)
class Demographics:
    full_name: str
    date_of_birth: str
    sex: str
    city: str
    state: str


@dataclass(frozen=True)
class PatientProfile:
    patient_id: str
    demographics: Demographics


@dataclass(frozen=True)
class Diagnosis:
    code: str
    description: str
    status: str
    onset_date: str


@dataclass(frozen=True)
class Medication:
    name: str
    dose: str
    route: str
    frequency: str
    status: str


@dataclass(frozen=True)
class Allergy:
    substance: str
    reaction: str
    severity: str


@dataclass(frozen=True)
class LabResult:
    test_name: str
    value: float
    unit: str
    reference_range: str
    collected_on: str


@dataclass(frozen=True)
class DemoIdentity:
    '''Authenticated demo principal. Patient access comes from this identity, not from a requested ID.'''
    user_id: str
    allowed_patient_ids: frozenset[str]
