from needful.flow.answers import Answers


def test_defaults_are_the_pitch_example():
    answers = Answers()
    assert answers.product == "hogedrukreiniger"
    assert answers.price == 149
    assert answers.total_uses == 12


def test_saving_and_loading_gives_the_same_answers():
    original = Answers(product="boormachine", need="concreet", uses_per_year=10)
    loaded, missing = Answers.from_dict(original.to_dict())
    assert loaded == original
    assert missing == []


def test_missing_fields_fall_back_to_defaults_and_are_reported():
    loaded, missing = Answers.from_dict({"product": "ladder"})
    assert loaded.product == "ladder"
    assert loaded.price == 149
    assert "price" in missing
    assert "product" not in missing


def test_unknown_keys_are_ignored():
    loaded, _ = Answers.from_dict({"product": "ladder", "old_field": 1})
    assert loaded.product == "ladder"


def test_choice_on_question_3_tells_the_rules_what_is_allowed():
    assert Answers(choice="nieuw").access == "nieuw"
    assert Answers(choice="tweedehands").access == "tweedehands"
    # lenen of huren, een alternatief of "alles op een rij": alles mag
    assert Answers(choice="delen").access == "toegang"
    assert Answers(choice="alternatief").access == "toegang"
    assert Answers().access == "toegang"
