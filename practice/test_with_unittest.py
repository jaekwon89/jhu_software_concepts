import pytest

@pytest.mark.slow
def test_heavy_computation():
    result = sum(i for i in range(10**6))
    assert result > 0

def test_fast():
    assert "py" in "pytest"