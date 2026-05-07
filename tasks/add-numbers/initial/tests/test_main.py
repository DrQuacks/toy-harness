from main import add_numbers


def test_adds_positive_numbers():
    assert add_numbers(2, 3) == 5


def test_adds_negative_numbers():
    assert add_numbers(-2, -3) == -5


def test_adds_mixed_numbers():
    assert add_numbers(-2, 3) == 1