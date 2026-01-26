import json
import requests
import urllib3
from Server.config_loader import CONFIG

# Disable HTTPS Warnings for Pwnboard
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def fwd_pwnboard(target, result):
    from Server.callbacks import privileged_results
    
    # Set up JSON Request
    data = {}
    data["ip"] = target
    data["application"] = "Mirage"
    data["access_type"] = "IIS Backdoor"

    payload = json.dumps(data)
    # print(payload)

    headers = {'Content-Type': 'application/json', 'Authorization': CONFIG.logging.PWNBOARD_AUTH_TOKEN}

    # Send and check result
    try:
        response = requests.post(CONFIG.logging.PWNBOARD_URL, headers=headers, data=payload, verify=False)
        #print(f"✅ Payload delivered successfully, code {response.status_code}.") testing
        privileged_results.append({
            "target": target,
            "status": "PRIVILEGED - Sent to Pwnboard",
            "pwnboard_status": f"HTTP {response.status_code}"
        })
    except requests.exceptions.HTTPError as err:
        #print(f"❌ HTTP Error: {err}") testing
        privileged_results.append({
            "target": target, 
            "status": "PRIVILEGED - Pwnboard Error",
            "pwnboard_status": f"Error: {err}"
        })
    except requests.exceptions.MissingSchema as nourl:
        #print(f"❌ PWNBoard Error: {nourl}") testing
        privileged_results.append({
            "target": target,
            "status": "PRIVILEGED - Pwnboard Error", 
            "pwnboard_status": f"Error: {nourl}"
        })