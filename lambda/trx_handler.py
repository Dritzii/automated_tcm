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
    """Extracts the first integer from a string if it has 5-7 digits, returns None otherwise."""
    match = re.search(r'\d+', name)  # Find the first sequence of digits
    if match:
        number = int(match.group())
        if 10000 <= number <= 9999999:  # Ensure it's between 5 and 7 digits
            return int(number)
    return "not_found"

# Function to parse the .trx file
def parse_trx(file_path):
    rt = RichText()
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
            "pbiID" : extract_integer(result.attrib.get("testName")),
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
            "HasIntegers": extract_integer(name),  # Extract the integer (if any)
            "Storage": definition.attrib.get("storage"),
            "ClassName": definition.find("TestMethod").attrib.get("className") if definition.find(
                "TestMethod") is not None else None
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
        "ResultSummary": result_summary,
        "BackendFunctionalTesting" : {
            "ComponentName": "SS",
            "suiteLink": "N/A",
            "Status": "Conditional",
        },
        "tcsSummary" : {
            "PhaseName" : "System Services Functional Testing",
            "Environment" : "DTS",
            "Notes" : "System Services components. System Services has no external dependencies."
        },
    }

    return trx_data

def trx_to_json(file_path, output_path="none") -> dict:
    # Parse the file and output JSON
    parsed_data = parse_trx(file_path)

    # Convert to JSON string for saving or further use
    json_output = json.dumps(parsed_data, indent=4)

    #Save JSON to a file (optional)
    #with open(output_path, "w") as json_file:
    #    output = json_file.write(json_output)
    #print(json_output)
    return json_output

#context = trx_to_json("/mnt/49bb6cd3-a5bf-468d-b67a-f4dd29190808/SS_FT__DTD__3.1.62.8__2024120608350212.trx", "/mnt/49bb6cd3-a5bf-468d-b67a-f4dd29190808/json.json")
#doc = DocxTemplate("/mnt/49bb6cd3-a5bf-468d-b67a-f4dd29190808/GIT/automated_tcm/lambda/templates/myID_FT&PT_TCM_{Release}_{Year}.docx")
#load_context = json.loads(context)
#doc.render(load_context)
#doc.save("generated_doc1.docx")