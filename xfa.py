import re
from typing import Any, Iterable, List, Dict, Tuple

import io
import copy
import json
from json import loads
import xml.etree.ElementTree as ET
import csv
import yaml
import PyPDF2 as pypdf


class Xfa:
    """
    A class for converting XFA data in a PDF to JSON or XML.
    """
    def __init__(self, filepath: str) -> None:
        self.filepath = filepath


    def open(self) -> pypdf.PdfReader:
        """
        Opens a PDF file and decrypts it if necessary.
        """
        pdf = open(self.filepath, 'rb')
        pdf_reader = pypdf.PdfReader(pdf)

        if pdf_reader.is_encrypted:
            password = input('Enter password to decrypt the PDF:')
            pdf_reader.decrypt(password)

        return pdf_reader
    
    @property
    def data(self) -> Any:
        """
        Returns the PdfReader's resolved objects.
        """
        pdf_reader = self.open()
        objects = self.find_in_dict('/XFA', pdf_reader.resolved_objects)

        return objects



    @classmethod
    def find_in_dict(cls, needle: str, haystack: dict) -> Any:
        """
        Recursively searches for a key in a dictionary and returns its value.
        """
        for key in haystack.keys():
            try:
                value = haystack[key]
            except:
                continue

            if key == needle:
                return value

            if isinstance(value, dict):
                item: Any  = cls.find_in_dict(needle, value)

                if item is not None:
                    return item

    @classmethod
    def xml_to_dict(cls, xml_str: str) -> dict:
        """
        Converts XML data to a dictionary.
        """
        root = ET.fromstring(xml_str)
        return cls.element_to_dict(root)

    @classmethod
    def element_to_dict(cls, element: Any) -> dict:
        """
        Converts an XML element to a dictionary.
        """
        # If the element has no children or attributes, just return its text
        children = list(element)
        if not children and not element.attrib:
            return element.text

        # Otherwise, create a dictionary for the element's children and attributes
        d: dict = {}

        for child in children:
            key = child.tag
            value = cls.element_to_dict(child)

            if key in d:
                # If the key already exists, convert it to a list
                if not isinstance(d[key], list):
                    d[key] = [d[key]]
                d[key].append(value)
            else:
                d[key] = value

        # Add attributes as key-value pairs in the dictionary
        d.update(element.attrib)

        return d
    
    @staticmethod
    def _flatten_dict(d: dict, parent_key='', sep='_') -> Iterable[Tuple[str, Any]]:
        """
        Flattens a nested dictionary to a single level.
        """
        items: List[Tuple[str, Any]] = []  # List of flattened key-value pairs

        for key, value in d.items():
            new_key: str = f"{parent_key}{sep}{key}" if parent_key else key

            if isinstance(value, dict):
                items.extend(Xfa._flatten_dict(value, new_key, sep=sep))  # Add the flattened key-value pairs to the list if the value is a dictionary
            else:
                items.append((new_key, value))  # Otherwise, add the key-value pair tuple to the list

        return items

    
    def to_xml(self) -> str:
        """
        Returns the XML data from the XFA field of a PDF.
        """
        pdf_reader = self.open()
        objects = self.find_in_dict('/XFA', pdf_reader.resolved_objects)

        xml = None

        for _, obj in enumerate(objects):
            if isinstance(obj, pypdf.generic.IndirectObject):  # Parse objects to find XML data
                actual_obj = obj.get_object().get_data()

                capture = re.search(b'datasets xmlns', actual_obj) # TODO: Not sure if this capture is true for all XFA forms

                if capture:
                    xml = str(actual_obj.decode("utf-8"))
                    break

        if not xml:
            raise Exception("No XML data found in PDF.")
        
        # We need to prettify the XML data to make it easier to read
        root = ET.fromstring(xml)
        ET.indent(ET.ElementTree(root), space='  ', level=0)

        # add xml declaration
        xml = ET.tostring(root, encoding='utf-8', method='xml').decode('utf-8')
        xml = '<?xml version="1.0" encoding="UTF-8"?>\n' + xml

        return str(xml)

    def to_json(self) -> str:
        """
        Returns the JSON data as a string from the XFA field of a PDF.
        """
        xml = self.to_xml()

        json_dict = json.dumps(self.xml_to_dict(xml), indent=4, sort_keys=True)

        return str(json_dict)

    def to_yaml(self) -> str:
        """
        Returns the YAML data from the XFA field of a PDF.
        """
        json = loads(self.to_json())

        return yaml.dump(json, default_flow_style=False)

    def to_csv(self) -> str:
        """
        Returns the CSV data from the XFA field of a PDF.
        """
        json_dict = loads(self.to_json())

        if not json_dict:
            raise Exception("JSON data failed to load.")

        flattened_dict = dict(self._flatten_dict(json_dict))

        headers = flattened_dict.keys()
        rows = [flattened_dict]

        csv_output = io.StringIO()
        writer = csv.DictWriter(csv_output, fieldnames=headers)

        writer.writeheader()

        for row in rows:
            writer.writerow(row)

        return csv_output.getvalue()
    
    def convert(self, output: str = 'json') -> str:
        if output == 'json':
            return self.to_json()
        elif output == 'xml':
            return self.to_xml()
        elif output == 'yaml':
            return self.to_yaml()
        elif output == 'csv':
            return self.to_csv()
        else:
            raise Exception(
                "Invalid output format. Please use 'json', 'xml', 'yaml', or 'csv'.")


    def save(self, ext: str = 'json') -> None:
        """
        Saves the converted data to a file.
        """    
        with open(f"{self.filepath}.{ext}", "w") as f:
            f.write(self.convert(ext))