from __future__ import annotations

def get_ml_config():
    """Return the singleton MLServiceConfig row."""
    from ...models.incidents import MLServiceConfig
    return MLServiceConfig.get_solo()
