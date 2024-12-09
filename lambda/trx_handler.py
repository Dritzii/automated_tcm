import base64
import json
import os

import boto3

import xml.etree.ElementTree as ET
import json

# Function to strip namespaces
def strip_namespace(root):
    """Removes the namespace from all elements in the XML tree."""
    for elem in root.iter():
        if '}' in elem.tag:
            elem.tag = elem.tag.split('}', 1)[1]  # Strip namespace
    return root

# Function to parse the .trx file
def parse_trx(file_path):
    # Parse the XML content
    tree = ET.parse(file_path)
    root = tree.getroot()

    # Strip namespaces
    root = strip_namespace(root)

    # Extract Test Results
    test_results = []
    for result in root.findall(".//UnitTestResult"):
        test_results.append({
            "TestID": result.attrib.get("testId"),
            "Outcome": result.attrib.get("outcome"),
            "Duration": result.attrib.get("duration"),
            "StartTime": result.attrib.get("startTime"),
            "EndTime": result.attrib.get("endTime"),
            "ExecutionID": result.attrib.get("executionId")
        })

    # Extract Test Definitions
    test_definitions = []
    for definition in root.findall(".//UnitTest"):
        test_definitions.append({
            "ID": definition.attrib.get("id"),
            "Name": definition.attrib.get("name"),
            "Storage": definition.attrib.get("storage"),
            "ClassName": definition.find("TestMethod").attrib.get("className") if definition.find("TestMethod") is not None else None
        })

    # Extract Result Summary
    result_summary_element = root.find(".//ResultSummary")
    if result_summary_element is not None:
        counters_element = result_summary_element.find("Counters")
        result_summary = {
            "Outcome": result_summary_element.attrib.get("outcome"),
            "Counters": {key: int(value) for key, value in counters_element.attrib.items()}
        }
    else:
        result_summary = None

    # Construct final JSON structure
    trx_data = {
        "TestResults": test_results,
        "TestDefinitions": test_definitions,
        "ResultSummary": result_summary
    }

    return trx_data

# Path to the .trx file
file_path = "/mnt/data/SS_FT__DTD__3.1.62.8__2024120608350212.trx"

# Parse the file and output JSON
parsed_data = parse_trx(file_path)

# Convert to JSON string for saving or further use
json_output = json.dumps(parsed_data, indent=4)

# Save JSON to a file (optional)
output_path = "/mnt/data/parsed_trx.json"
with open(output_path, "w") as json_file:
    json_file.write(json_output)

print("Parsing completed. JSON data saved to:", output_path)



def handler(event, context):
    pass