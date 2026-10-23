class EhrError(Exception):
    '''Base error for the CareChain EHR data layer.'''


class PatientNotFoundError(EhrError):
    def __init__(self, patient_id: str):
        self.patient_id = patient_id
        super().__init__(f'Unknown patient_id: {patient_id}')


class MissingPatientDataError(EhrError):
    def __init__(self, patient_id: str, field: str):
        self.patient_id = patient_id
        self.field = field
        super().__init__(
            f'Patient {patient_id} has no {field} data in the EHR dataset'
        )


class UnknownDemoUserError(EhrError):
    def __init__(self, user_id: str):
        self.user_id = user_id
        super().__init__(f'Unknown demo identity: {user_id}')


class PatientAccessDeniedError(EhrError):
    def __init__(self, user_id: str, patient_id: str):
        self.user_id = user_id
        self.patient_id = patient_id
        super().__init__(
            f'Demo identity {user_id} is not authorized for patient {patient_id}'
        )
