import pytest
from nova.calculator import CalculationError, calculate


def test_safe_arithmetic():
    assert calculate("(12 * 8) + 4") == 100
    assert calculate("2 ** 3") == 8


@pytest.mark.parametrize("expression", ["__import__('os').system('whoami')", "open('x')", "1 / 0", "2 ** 1000", "True + 1"])
def test_rejects_unsafe_or_invalid_expressions(expression):
    with pytest.raises(CalculationError):
        calculate(expression)
