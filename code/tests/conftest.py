from pathlib import Path
import sys

import pytest

CODE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CODE))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from ghosttrace.demo import synthetic_cases
from ghosttrace.emit.operation_mapper import emit_decision


@pytest.fixture
def context():
    return synthetic_cases()


@pytest.fixture
def rows(context):
    return [emit_decision(d).as_dict() for d in context[1]]
