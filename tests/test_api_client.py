import sys
import pytest
import requests
from pathlib import Path
from unittest.mock import Mock, patch
from dataclasses import dataclass

sys.path.append(str(Path(__file__).resolve().parent.parent))
from reaskapi.api_client import ClientConfig
from reaskapi.deepcyc import DeepCyc
from reaskapi.metryc import Metryc


@dataclass
class MockedResponse:
    status_code: int = 200

    def json(arg):
        return {}


@pytest.mark.parametrize("config", [None, ClientConfig("https://localhost:8001")])
def test_deep_cyc_config(config: ClientConfig):
    with patch("reaskapi.api_client.get_access_token") as token_mock:
        token_mock.return_value = "dummy_token"
        mock_session_send = Mock(return_value=MockedResponse())
        requests.Session.send = mock_session_send
        d = DeepCyc(config=config)
        d.tctrack_events(36.8, -76, "circle", radius_km=50, wind_speed_units="kph")
        mock_session_send.assert_called_once()
        assert (
            mock_session_send.call_args.args[0].url
            == f"{config.base_url if config is not None else 'https://api.reask.earth/v2'}/deepcyc/tctrack/events?radius_km=50&wind_speed_units=kph&lat=36.8&lon=-76&geometry=circle"
        )


@pytest.mark.parametrize("config", [None, ClientConfig("https://localhost:8001")])
def test_metryc_config(config: ClientConfig):
    with patch("reaskapi.api_client.get_access_token") as token_mock:
        token_mock.return_value = "dummy_token"
        mock_session_send = Mock(return_value=MockedResponse())
        requests.Session.send = mock_session_send
        m = Metryc(config=config)
        m.tctrack_events(36.8, -76, "circle", radius_km=50, wind_speed_units="kph")
        mock_session_send.assert_called_once()
        assert (
            mock_session_send.call_args.args[0].url
            == f"{config.base_url if config is not None else 'https://api.reask.earth/v2'}/metryc/tctrack/events?radius_km=50&wind_speed_units=kph&lat=36.8&lon=-76&geometry=circle"
        )

