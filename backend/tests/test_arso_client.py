import pytest # testing framework
from unittest.mock import patch, MagicMock # used to mock network calls
from backend.network.arso_client import fetch_arso_xml


"""
Test successful fetching of ARSO XML data.
"With patch" block replaces the real request.get
function with mock object for the duration of the with
object. When fetch_arso_xml() calls request.get, 
it actually calls mock_get which returns mock_response
"""
def test_fetch_arso_xml_success():
    fake_xml = "<xml>test</xml>"
    with patch("requests.get") as mock_get:
        mock_response = MagicMock()
        mock_response.text = fake_xml
        mock_response.encoding = "utf-8"
        # returns no value, simulates successfull response, no Exception needed
        mock_response.raise_for_status.return_value = None 
        # makes request.get return mock response
        mock_get.return_value = mock_response

        # Short way:assert fetch_arso_xml() == (True, fake_xml, None)
        success,xml_data, error = fetch_arso_xml()
        assert success is True
        assert xml_data == fake_xml
        assert error is None


def test_fetch_arso_html_http_error():
    with patch("requests.get") as mock_get:
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = Exception("Http Error")
        mock_get.return_value = mock_response

        success, xml_data, error = fetch_arso_xml()
        assert success is False
        assert xml_data is None
        assert error is not None








