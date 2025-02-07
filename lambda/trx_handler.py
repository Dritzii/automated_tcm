import re
import xml.etree.ElementTree as ET
import json
from docxtpl import DocxTemplate, RichText

# Function to strip namespaces
def strip_namespace(root):
    """Removes the namespace from all elements in the XML tree."""
    for elem in root.iter():
        if '}' in elem.tag:
            elem.tag = elem.tag.split('}', 1)[1]  # Strip namespace
    return root

def extract_integer(name):
    match = re.findall(r'\d+', name)
    return int(max(match))

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
            "testName": result.attrib.get("testName"),
            "testcaseID": extract_integer(result.attrib.get("testName")),
            "Outcome": result.attrib.get("outcome"),
            "Duration": result.attrib.get("duration"),
            "StartTime": result.attrib.get("startTime"),
            "EndTime": result.attrib.get("endTime"),
            "ExecutionID": result.attrib.get("executionId")
        })

    # Extract Test Definitions
    test_definitions = []
    for definition in root.findall(".//UnitTest"):
        name = definition.attrib.get("name")
        test_definitions.append({
            "TestID": definition.attrib.get("id"),
            "testName": name,
            "testcaseID": extract_integer(name),  # Extract the integer (if any)
            "Storage": definition.attrib.get("storage"),
            "ClassName": definition.find("TestMethod").attrib.get("className") if definition.find(
                "TestMethod") is not None else None,
            "TestCategory": [test_value.attrib.get("TestCategory") for test_value in
                             definition.findall(".//TestCategory/TestCategoryItem")]
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
    # Convert the second list into a dictionary for quick lookup
    test_joins = {d["testcaseID"]: d for d in test_definitions}

    # Merge lists based on matching "id"
    test_with_same_id = [
        {**d, **test_joins[d["testcaseID"]]} if d["testcaseID"] in test_joins else d
        for d in test_results
    ]
    # Construct final JSON structure
    trx_data = {
        "TestResults": test_results,
        "TestDefinitions": test_definitions,
        "ResultSummary": result_summary,
        "TestRandD": test_with_same_id,
        "finaltcm" : True,
        "BackendFunctionalTesting": [{
            "ComponentName": "SS",
            "suiteLink": "N/A",
            "Status": "Conditional",
        }],
        "tcsSummary": [{
            "PhaseName": "System Services Functional Testing",
            "Environment": "DTS",
            "Notes": "System Services components. System Services has no external dependencies."
        }],
    }

    return trx_data

def trx_to_json(file_path, output_path="none") -> dict:
    # Parse the file and output JSON
    parsed_data = parse_trx(file_path)

    # Convert to JSON string for saving or further use
    json_output = json.dumps(parsed_data, indent=4)

    print(json_output)
    return json_output
