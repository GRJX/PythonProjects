import os
import requests

# Configuration
JIRA_URL = "https://jira.ictu-sd.nl"
PAT = os.environ["JIRA_PAT"]
headers = {"Authorization": f"Bearer {PAT}"}

# 1. Get all open sub-tasks
jql = "issuetype in subTaskIssueTypes() AND status != Closed"
response = requests.get(f"{JIRA_URL}/rest/api/2/search?jql={jql}", headers=headers)
issues = response.json().get('issues', [])

orphaned_subtasks = []

# 2. Check each parent
for subtask in issues:
    parent_key = subtask['fields']['parent']['key']
    
    # Fetch parent details to see its status
    parent_resp = requests.get(f"{JIRA_URL}/rest/api/2/issue/{parent_key}?fields=status", headers=headers)
    parent_data = parent_resp.json()
    
    parent_status = parent_data['fields']['status']['name']
    
    # If the parent is closed/done, add it to our list
    if parent_status in ["Closed"]:
        orphaned_subtasks.append({
            "subtask": subtask['key'],
            "parent": parent_key,
            "parent_status": parent_status
        })

# Output results
for item in orphaned_subtasks:
    print(f"Warning: Sub-task {item['subtask']} is OPEN but Parent {item['parent']} is {item['parent_status']}")

parent_keys = ', '.join([item['parent'] for item in orphaned_subtasks])
print(f"jql: key in ({parent_keys})")