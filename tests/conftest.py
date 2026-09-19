"""Shared pytest fixtures."""

import pytest

from tests.mock_server import MockWrosbridgeServer


@pytest.fixture(scope="session")
def mock_server():
    server = MockWrosbridgeServer()
    server.start()
    yield server
    server.stop()
