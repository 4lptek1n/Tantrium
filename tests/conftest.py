import pytest

import tantrium
from tantrium import CertificationEngine


@pytest.fixture(scope="session")
def engine():
    return CertificationEngine()


@pytest.fixture(scope="session")
def ai():
    return tantrium.AI()
