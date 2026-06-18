from path_bootstrap import ensure_src_on_path

ensure_src_on_path()

import agents.api  # noqa: F401


def test_import_app_entrypoint_module() -> None:
    import app

    assert callable(app.create_app)


def test_import_api_router_module() -> None:
    from agents.api import agent

    assert agent.system_router is not None
    assert agent.visualizer_router is not None
    assert agent.feature_extractor_router is not None


def test_import_rag_ingest_script_module() -> None:
    from scripts import rag_ingest

    assert callable(rag_ingest.main)


def test_import_rag_api_script_module() -> None:
    from scripts import rag_api

    assert rag_api.app is not None


def test_import_feature_extractor_cli_module() -> None:
    from agents.tasks.feature_extractor import cli

    assert callable(cli.main)


def test_import_price_valuator_cli_module() -> None:
    from agents.tasks.price_valuator import cli

    assert callable(cli.main)
