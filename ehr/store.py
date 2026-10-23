import json
from functools import lru_cache
from pathlib import Path

from ehr.exceptions import PatientNotFoundError

DATASET_PATH = Path(__file__).parent / 'data' / 'patients.json'


@lru_cache(maxsize=1)
def load_dataset() -> dict:
    with DATASET_PATH.open(encoding='utf-8') as handle:
        return json.load(handle)


def get_patient_record(patient_id: str) -> dict:
    '''Return the raw JSON object for a patient ID.'''
    for patient in load_dataset()['patients']:
        if patient.get('patient_id') == patient_id:
            return patient
    raise PatientNotFoundError(patient_id)
