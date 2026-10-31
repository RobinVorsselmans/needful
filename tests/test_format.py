from needful.calc.format import euro, km


def test_euro_whole_amount_has_no_decimals():
    assert euro(149) == "€149"


def test_euro_uses_decimal_separator():
    assert euro(12.42) == "€12,42"


def test_euro_keeps_two_decimals():
    assert euro(12.4) == "€12,40"


def test_km_whole_amount_has_no_decimals():
    assert km(149) == "149 km"


def test_km_uses_decimal_separator():
    assert km(12.42) == "12,4 km"


def test_euro_whole_thousands_has_dot_separator():
    assert euro(1234) == "€1.234"


def test_euro_thousands_with_decimals_has_dot_and_comma_separator():
    assert euro(1234.56) == "€1.234,56"
