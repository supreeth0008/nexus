from nexus.config.settings import Settings, validate_settings


def test_default_settings_valid():
    s = Settings()
    validate_settings(s)
