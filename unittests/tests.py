"""
Testing suite for all file type conversions from Xfa.
"""
import pytest
import os
from unittest.mock import patch

from xfa import Xfa



TEST_PDF_DOC = "test_pdf.pdf"


def test_get_xml():
    xfa = Xfa(TEST_PDF_DOC)

    with patch("PyPDF2.PdfReader") as mock_pdf_reader:
        mock_pdf_reader.return_value.isEncrypted = False
        mock_pdf_reader.return_value.decrypt.return_value = None
        mock_pdf_reader.return_value.resolved_objects = {'/XFA': ['Mock XFA Data']}
        assert xfa.get_xml() == "Mock XFA Data"


def test_get_json():
    xfa = Xfa(TEST_PDF_DOC)
    
    with patch.object(xfa, "get_xml", return_value="<root><data>value</data></root>"):
        assert xfa.get_json() == {'root': {'data': 'value'}}


def test_get_yaml():
    xfa = Xfa(TEST_PDF_DOC)

    with patch.object(xfa, "get_json", return_value={"root": {"data": "value"}}):
        assert xfa.get_yaml() == "root:\n  data: value\n"


def test_get_csv():
    xfa = Xfa(TEST_PDF_DOC)

    with patch.object(xfa, "get_json", return_value={"root": {"data": "value"}}):
        assert xfa.get_csv() == "root_data\nvalue\n"


def test_convert():
    xfa = Xfa(TEST_PDF_DOC)

    with patch.object(xfa, "get_json", return_value={"root": {"data": "value"}}):
        assert xfa.convert(output='json') == {"root": {"data": "value"}}


# Ensure that the PDF file exists before running the tests
def pytest_collection_modifyitems(config, items):
    for item in items:
        if 'pdf_test' in item.parent.name and 'test' not in item.parent.name:
            if not os.path.exists(TEST_PDF_DOC):
                pytest.skip("Test PDF file not found.")


if __name__ == "__main__":
    pytest.main()
