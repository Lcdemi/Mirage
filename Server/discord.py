from datetime import datetime
import requests
import re
from pytz import timezone
from Server.config_loader import CONFIG

# Necessary variables
COMMAND_RE = re.compile(r'Command:\s*(.+)')
tz = timezone(CONFIG.other.TIMEZONE)

def fwd_discord(target, response):
    # Extract the command from the response
    command = COMMAND_RE.search(response).group(1)
    # print(f"Sending : {formatted_msg}")

    # Setup Post Request
    data = {
        "username": "Mirage",
        "embeds": [
            {
                "title": "✅ Command Executed Successfully",
                "color": 0x00FF00,  # green
                "fields": [
                    {"name": "Target", "value": f"`{target}`", "inline": False},
                    {"name": "Command", "value": f"```bash\n{command}\n```", "inline": False}
                ],
                "footer": {"text": "Mirage"},
                "timestamp": str(datetime.now(tz))
            }
        ]
    }

    # Send and check result
    try:
        result = requests.post(CONFIG.logging.DISCORD_WEBHOOK_URL, json = data, timeout = 5)
        result.raise_for_status()
    except requests.exceptions.HTTPError as err:
        print(err)
    except requests.exceptions.MissingSchema as nourl:
        print("No Discord URL provided : Skipping Webhook")