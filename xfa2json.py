from typing import Any

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
                value: Any  = cls.find_in_dict(needle, value)
                if value is not None:
                    return value

    @classmethod
    def xml_to_dict(cls, xml_string) -> dict:
        """
        Converts XML data to a dictionary.
        """
        root = ET.fromstring(xml_string)
        return cls.element_to_dict(root)

    @classmethod
    def element_to_dict(cls, element) -> dict:
        """
        Converts an XML element to a dictionary.
        """
        # If the element has no children or attributes, just return its text
        children = list(element)
        if not children and not element.attrib:
            return element.text

        # Otherwise, create a dictionary for the element's children and attributes
        d = {}

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
    def _flatten_dict(d: dict, parent_key='', sep='_') -> dict:
        """
        Flattens a nested dictionary to a single level.
        """
        items = []
        for key, value in d.items():
            new_key = f"{parent_key}{sep}{key}" if parent_key else key

            if isinstance(value, dict):
                items.extend(Xfa._flatten_dict(value, new_key, sep=sep).items())
            else:
                items.append((new_key, value))

        return dict(items)

    def get_xml(self) -> str:
        """
        Returns the XML data from the XFA field of a PDF.
        """
        with open(self.filepath, 'rb') as pdf2:
            pdf = pypdf.PdfReader(pdf2)
            objects = self.find_in_dict('/XFA', pdf.resolved_objects)

            for _, obj in enumerate(objects):
                if isinstance(obj, pypdf.generic.IndirectObject):  # Parse objects to find XML data
                    actual_obj = obj.getObject().getData()

                    if actual_obj.startswith(b'\n<xfa'):
                        xml = actual_obj.decode("utf-8")
                        break

        if not xml:
            raise Exception("No XFA data found in PDF.")

        return xml

    def get_json(self) -> dict:
        """
        Returns the JSON data from the XFA field of a PDF.
        """
        xml = self.get_xml()

        json_dict = json.dumps(self.xml_to_dict(xml), indent=4)
        json_dict = copy.deepcopy(loads(json_dict))

        return json_dict

    def get_yaml(self) -> str:
        """
        Returns the YAML data from the XFA field of a PDF.
        """
        json_dict = self.get_json()
        return yaml.dump(json_dict)
    
    def get_csv(self) -> str:
        """
        Returns the CSV data from the XFA field of a PDF.
        """
        json_dict = self.get_json()
        if not json_dict:
            raise Exception("No XFA data found in PDF.")

        flattened_dict = self._flatten_dict(json_dict)
        headers = flattened_dict.keys()
        rows = [flattened_dict]

        csv_output = io.StringIO()
        writer = csv.DictWriter(csv_output, fieldnames=headers)

        writer.writeheader()
        for row in rows:
            writer.writerow(row)

        return csv_output.getvalue()

    def convert(self, output: str = 'json') -> Any:
        """
        Converts the XFA data of a PDF to JSON or XML.
        """
        if output == 'json':
            return self.get_json()
        elif output == 'xml':
            return self.get_xml()
        elif output == 'yaml':
            return self.get_yaml()
        elif output == 'csv':
            return self.get_csv()
        else:
            raise Exception(
                "Invalid output format. Please use 'json', 'xml', 'yaml', or 'csv'.")


if __name__ == '__main__':
    PATH = "C:\\Users\\13439\\Desktop\\CNSC\\Assesment Worksheet\\FINAL-DYNAMIC-eng - filled.PDF"
    xfa = Xfa(PATH)
    print(xfa.convert('csv'))
