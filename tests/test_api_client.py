import sys
import pytest
import requests

from pathlib import Path
from unittest.mock import Mock, patch
from dataclasses import dataclass, field
from typing import Dict

sys.path.append(str(Path(__file__).resolve().parent.parent))
from reaskapi.api_client import ClientConfig
from reaskapi.deepcyc import DeepCyc
from reaskapi.metryc import Metryc


@dataclass
class MockedResponse:
    status_code: int = 200
    headers: Dict[str, str] = field(default_factory=lambda: {"Content-Type": "application/json"})
    content: str = ""

    def json(arg):
        return {}


@pytest.mark.parametrize("config", [None, ClientConfig("https://localhost:8001")])
@pytest.mark.parametrize("product", ["metryc", "deepcyc"])
def test_config(config: ClientConfig, product):
    with patch("reaskapi.api_client.get_access_token") as token_mock, patch(
        "requests.Session.send"
    ) as mock_session_send:
        token_mock.return_value = "dummy_token"
        mock_session_send.return_value = MockedResponse()
        if product == 'metryc':
            obj = Metryc(config=config)
        else:
            obj = DeepCyc(config=config)
        obj.tctrack_events(36.8, -76, "circle", radius_km=50, wind_speed_units="kph")
        mock_session_send.assert_called_once()
        name, args, kwargs = mock_session_send.mock_calls[0]
        print(args)
        assert (
            args[0].url
            == f"{config.base_url if config is not None else 'https://api.reask.earth/v2'}/{product}/tctrack/events?radius_km=50&wind_speed_units=kph&lat=36.8&lon=-76&geometry=circle"
        )
