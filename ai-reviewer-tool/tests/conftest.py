import warnings
import pytest

# Suppress Pydantic deprecation warnings
warnings.filterwarnings("ignore", category=DeprecationWarning, module="pydantic")
warnings.filterwarnings("ignore", message=".*PydanticDeprecatedSince20.*")

@pytest.fixture(autouse=True)
def suppress_warnings():
    """Suppress specific warnings during tests."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        yield 