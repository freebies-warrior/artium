def test_import_app_entrypoint_module() -> None:
    import app

    assert callable(app.create_app)


def test_import_api_router_module() -> None:
    from agents.api import agent

    assert agent.system_router is not None
    assert agent.visualizer_router is not None
    assert agent.feature_extractor_router is not None
