import pytest

# Zet NiceGUI's `user`-fixture aan: een gesimuleerde gebruiker die klikt zonder echte browser.
# Welke app hij start, staat in pyproject.toml (main_file).
pytest_plugins = ["nicegui.testing.user_plugin"]


@pytest.fixture(autouse=True)
def no_llm(monkeypatch):
    """Tests praten nooit met het echte LLM, ook niet als er een sleutel in .env staat.
    Een omgevingsvariabele wint van .env, dus een lege sleutel = geen LLM = het voorbeeld."""
    monkeypatch.setenv("OPENROUTER_API_KEY", "")
