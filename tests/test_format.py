from needful.calc.format import euro, kg, km, kwh, liters, price_text


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


def test_kg_whole_number():
    assert kg(40) == "40 kg"


def test_kg_with_decimal():
    assert kg(2.5) == "2,5 kg"


def test_price_text_one_time():
    assert price_text(once=25) == "€25"


def test_price_text_per_use_and_per_year():
    assert price_text(per_use=6, per_year=10) == "€6 per keer + €10 per jaar"


def test_price_text_nothing_is_free():
    assert price_text() == "gratis"


def test_kwh_with_decimal():
    assert kwh(1.5) == "1,5 kWh"


def test_liters_whole_number():
    assert liters(350) == "350 liter"


def test_liters_thousands():
    assert liters(1200) == "1.200 liter"
