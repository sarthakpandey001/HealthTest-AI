import json
import requests
from dotenv import load_dotenv,find_dotenv
import os

load_dotenv(dotenv_path=find_dotenv())

JIRA_BASE_URL = os.getenv("JIRA_BASE_URL")
PROJECT_KEY = os.getenv("PROJECT_KEY")
JIRA_API_TOKEN = os.getenv("JIRA_API_TOKEN")
JIRA_EMAIL = os.getenv("JIRA_EMAIL")

def create_jira_issue_logic(test_cases):
    """
    Core function to iterate through test cases and create Jira issues.
    Returns a list of results (success or failure) for each test case.
    """
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    results = []

    for test_case in test_cases:
        test_case_id = test_case.get('id', 'N/A')
        test_case_title = test_case.get('title', 'No Title')

        # 1. Build the description text
        description_text = (
            f"Test Case ID: {test_case_id}\n"
            f"Title: {test_case_title}\n"
            f"Description: {test_case.get('description', '')}\n"
            f"Type: {test_case.get('type', '')}\n"
            f"Priority: {test_case.get('priority', '')}\n"
            f"Status: {test_case.get('status', '')}\n"
            f"Preconditions: {', '.join(test_case.get('preconditions', []))}\n"
            f"Steps: {', '.join(test_case.get('steps', []))}\n"
            f"Expected Results: {', '.join(test_case.get('expectedResults', []))}\n"
            f"Traceability: {', '.join(test_case.get('traceability', []))}"
        )

        # 2. Build the Jira **A**tlassian **D**ocument **F**ormat (ADF) for the description
        description_adf = {
            "type": "doc",
            "version": 1,
            "content": [
                {
                    "type": "paragraph",
                    "content": [
                        {"type": "text", "text": description_text}
                    ]
                }
            ]
        }

        # 3. Build the final request payload
        payload = {
            "fields": {
                "project": {"key": PROJECT_KEY},
                "summary": f"{test_case_id} - {test_case_title}",
                "description": description_adf,
                # Note: You were using "Task" - change this if you need "Bug", "Story", etc.
                "issuetype": {"name": "Task"}
            }
        }

        # 4. Make the Jira API call
        try:
            response = requests.post(
                f"{JIRA_BASE_URL}/rest/api/3/issue",
                headers=headers,
                auth=(JIRA_EMAIL, JIRA_API_TOKEN),
                data=json.dumps(payload)
            )

            if response.status_code == 201:
                issue_key = response.json()["key"]
                results.append({
                    "test_case_id": test_case_id,
                    "status": "SUCCESS",
                    "issue_key": issue_key
                })
            else:
                # Log or capture the full error response for debugging
                results.append({
                    "test_case_id": test_case_id,
                    "status": "FAILURE",
                    "error": response.text,
                    "http_status": response.status_code
                })
        except requests.exceptions.RequestException as e:
            results.append({
                "test_case_id": test_case_id,
                "status": "FAILURE",
                "error": f"Network or request error: {str(e)}"
            })
    
    return results


