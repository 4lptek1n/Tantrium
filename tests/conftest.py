import pytest
import tantrium
from tantrium import CertificationEngine
from tantrium.core.encoder import encode, encode_smiles


@pytest.fixture(scope="session")
def engine():
    return CertificationEngine()


@pytest.fixture(scope="session")
def ai():
    return tantrium.AI()
