import pytest

from needful.calc.cost import (
    buying_pays_off_from,
    cost_per_use,
    energy_cost,
    extra_cost,
    real_cost_per_use,
    total_cost,
    total_uses,
    water_cost,
)


def test_pitch_example():
    assert cost_per_use(149, 3, 4) == 12.42


def test_single_use():
    assert cost_per_use(60, 1, 1) == 60.0


def test_invalid_price():
    with pytest.raises(ValueError):
        cost_per_use(0, 3, 4)


def test_invalid_uses():
    with pytest.raises(ValueError):
        cost_per_use(149, 0, 4)


def test_total_uses_pitch_example():
    assert total_uses(3, 4) == 12


def test_extra_cost_pitch_example():
    # stroom + water €2,20 per keer × 12 keer, onderhoud €8 per jaar × 4 jaar
    assert extra_cost(2.20, 8, 3, 4) == 58.40


def test_no_extra_costs_is_zero():
    assert extra_cost(0, 0, 3, 4) == 0


def test_real_cost_per_use_pitch_example():
    # (€149 + €58,40) ÷ 12 keer
    assert real_cost_per_use(149, 58.40, 3, 4) == 17.28


def test_real_cost_without_extra_is_the_normal_cost():
    assert real_cost_per_use(149, 0, 3, 4) == cost_per_use(149, 3, 4)


def test_real_cost_invalid_uses():
    with pytest.raises(ValueError):
        real_cost_per_use(149, 58.40, 0, 4)


def test_total_cost_one_time_purchase():
    # tuinslang en borstel: één keer kopen, verder niets
    assert total_cost(25, 0, 0, 3, 4) == 25


def test_total_cost_per_use():
    # wassalon €6 per keer, 3 keer per jaar, 4 jaar
    assert total_cost(0, 6, 0, 3, 4) == 72


def test_total_cost_all_parts():
    # €10 instap + €2 per keer × 12 + €5 per jaar × 4
    assert total_cost(10, 2, 5, 3, 4) == 54


def test_extra_cost_is_total_cost_without_one_time_part():
    assert extra_cost(2.20, 8, 3, 4) == total_cost(0, 2.20, 8, 3, 4)


def test_energy_cost_pitch_example():
    # hogedrukreiniger: 1,5 kWh aan €0,30
    assert energy_cost(1.5) == 0.45


def test_water_cost_pitch_example():
    # 350 liter aan €5 per m³
    assert water_cost(350) == 1.75


def test_washing_machine_usage():
    # 1 kWh en 50 liter per wasbeurt: €0,30 en €0,25 (een LLM rekende €0,90 en €1)
    assert energy_cost(1) == 0.30
    assert water_cost(50) == 0.25


def test_no_usage_costs_nothing():
    assert energy_cost(0) == 0
    assert water_cost(0) == 0


def test_laundromat_versus_washing_machine():
    # €600 + €0,79 per keer + €15 per jaar tegenover €7 per keer in de wassalon, 4 jaar
    assert buying_pays_off_from(600, 0.79, 15, 0, 7, 0, 4) == 27


def test_at_the_break_even_point_buying_really_is_cheaper():
    # 27 keer per jaar: kopen €745,32, wassalon €756; 26 keer: kopen €742,16, wassalon €728
    assert total_cost(600, 0.79, 15, 27, 4) < total_cost(0, 7, 0, 27, 4)
    assert total_cost(600, 0.79, 15, 26, 4) > total_cost(0, 7, 0, 26, 4)


def test_alternative_that_costs_nothing_per_use_always_stays_cheaper():
    # tuinslang en borstel: €25 eenmalig, geen stroom of water per keer
    assert buying_pays_off_from(149, 2.20, 8, 25, 0, 0, 4) is None


def test_alternative_dearer_upfront_and_per_use_means_buying_from_the_first_use():
    assert buying_pays_off_from(100, 0, 0, 200, 5, 0, 4) == 1
