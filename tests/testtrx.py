import json
import re
import xml.etree.ElementTree as ET

from docxtpl import DocxTemplate


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
            "ID": definition.attrib.get("id"),
            "Name": name,
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
        "test_with_same_id": test_with_same_id,
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

# Path to the .trx file
file_path = "/mnt/49bb6cd3-a5bf-468d-b67a-f4dd29190808/SS_FT__DTD__3.1.62.8__2024120608350212.trx"

# Parse the file and output JSON
parsed_data = parse_trx(file_path)

# Convert to JSON string for saving or further use
json_output = json.dumps(parsed_data, indent=4)

# Save JSON to a file (optional)
output_path = "/mnt/49bb6cd3-a5bf-468d-b67a-f4dd29190808/parsed_trx.json"
with open(output_path, "w") as json_file:
    json_file.write(json_output)

print("Parsing completed. JSON data saved to:", output_path)
doc = DocxTemplate("/mnt/49bb6cd3-a5bf-468d-b67a-f4dd29190808/GIT/automated_tcm/lambda/templates/test.docx")

doc.render(json.loads(json_output))
doc.save("/mnt/49bb6cd3-a5bf-468d-b67a-f4dd29190808/GIT/automated_tcm/lambda/doc.docx")