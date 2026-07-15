from supermarket_pos.domain.common.money import Money


def test_rounds_half_up_to_two_decimal_places():
    assert Money("10.005") == Money("10.01")


def test_addition():
    assert Money("10.00") + Money("5.50") == Money("15.50")


def test_subtraction():
    assert Money("10.00") - Money("3.00") == Money("7.00")


def test_multiplication_by_quantity():
    assert Money("4.00") * 3 == Money("12.00")


def test_ordering():
    assert Money("5.00") < Money("10.00")
    assert Money("10.00") > Money("5.00")


def test_equality_is_value_based():
    assert Money("18.00") == Money(18.0)
    assert Money("18.00") == Money("18")


def test_string_representation_uses_kwacha_prefix():
    assert str(Money("18.00")) == "K18.00"


def test_is_negative():
    assert Money("-5.00").is_negative()
    assert not Money("5.00").is_negative()
