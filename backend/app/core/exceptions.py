"""
SAR Irrigation Scheduling System — Custom Exceptions.
"""

class AppError(Exception):
    """Base class for application specific exceptions."""
    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)

class ModelNotTrainedError(AppError):
    def __init__(self, model_name: str):
        super().__init__(f"Model '{model_name}' has not been trained yet.", status_code=404)

class DatasetNotFoundError(AppError):
    def __init__(self, dataset_path: str):
        super().__init__(f"Dataset not found at path: {dataset_path}", status_code=404)

class ValidationFailedError(AppError):
    def __init__(self, detail: str):
        super().__init__(f"Validation failed: {detail}", status_code=422)

class ResourceConflictError(AppError):
    def __init__(self, detail: str):
        super().__init__(detail, status_code=409)
