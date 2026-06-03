import pytest
import tantrium
from tantrium.agi import CertificationEngine
from tantrium.agi.core.encoder import encode, encode_smiles


@pytest.fixture(scope="session")
def engine():
    return CertificationEngine()


@pytest.fixture(scope="session")
def ai():
    return tantrium.AI()
