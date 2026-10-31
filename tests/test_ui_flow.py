import logging

from nicegui.testing import User


async def test_pitch_example_clicks_through_to_lenen(user: User) -> None:
    """start -> 4 vragen -> advies met vb-waarden van de pitch: lenen"""
    await user.open("/")
    user.find("Start →").click()
    await user.should_see("VRAAG 1/4")
    user.find("Het zou handig zijn").click()
    await user.should_see("VRAAG 2/4")
    await user.should_see("= €12,42 per gebruik")
    user.find("Klopt →").click()
    await user.should_see("VRAAG 3/4")
    user.find("Volgende →").click()
    await user.should_see("VRAAG 4/4")
    await user.should_see("62")
    user.find("Toon mijn advies →").click()
    await user.should_see("Lenen is de slimste keuze.")


async def test_impulse_answer_ends_in_laten(user: User) -> None:
    await user.open("/")
    user.find("Start →").click()
    await user.should_see("VRAAG 1/4")
    user.find("Eerlijk? Ik wil het gewoon").click()
    await user.should_see("VRAAG 2/4")
    await user.open("/advies")
    await user.should_see("Laat het even liggen.")


async def test_back_link_returns_to_previous_question(user: User) -> None:
    await user.open("/vraag/2")
    user.find("← Terug").click()
    await user.should_see("VRAAG 1/4")


async def test_opening_advies_directly_uses_example_and_warns(user: User, caplog) -> None:
    """Iemand opent /advies zonder eerst de vragen te doorlopen: geen crash,
    wel een waarschuwing die zegt welke antwoorden ontbraken."""
    with caplog.at_level(logging.WARNING, logger="needful"):
        await user.open("/advies")
        await user.should_see("Lenen is de slimste keuze.")
    assert "antwoorden ontbreken" in caplog.text
    assert "price" in caplog.text
