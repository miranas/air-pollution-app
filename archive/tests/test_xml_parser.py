import pytest
from backend.utils.xml_parser import fetch_arso_xml



def test_fetch_arso_xm():

    #Call the function
    success, xml_content, error = fetch_arso_xml()

    #Basic assertions:
    assert success is True, f"Failed to fetch ARSO XML data :{error}"
    assert xml_content is not None, "XML content is None"
    assert len(xml_content) > 100, "XML content too short"
    assert "postaja" in xml_content, "Missing 'postaja' element in XML content"
    assert error is None, f"Unexpected error message: {error}"
    assert "<?xml" in xml_content, "XML does not start with <? "


    print(f"Successfully fetched ARSO XML data length: {len(xml_content)} caharacters")
    print(f"Contains stations data in {'postaja' in xml_content}")


