import os


class MissingVariableError(Exception):
    """
    Error type for missing required environment varibale
    """


def getenv(variable_name: str, default=None) -> str:
    """
    Returns environment variable or default value. If default is None, variable considered as required
    """
    value = os.getenv(variable_name, default)
    if default is None and not value:
        raise MissingVariableError(f'{variable_name} env variable is required')
    return value
