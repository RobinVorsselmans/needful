# Zet NiceGUI's `user`-fixture aan: een gesimuleerde gebruiker die klikt zonder echte browser.
# Welke app hij start, staat in pyproject.toml (main_file).
pytest_plugins = ["nicegui.testing.user_plugin"]
