from copy import deepcopy

import pytest

from fixture_support import load_fixture_set


@pytest.fixture(scope="session")
def baseline():
    return load_fixture_set()


@pytest.fixture
def fixtures(baseline):
    # Negative tests must not mutate the session baseline or another scenario.
    return deepcopy(baseline)
