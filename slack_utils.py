# slack_utils.py
import os
import json
import requests
import logging
from typing import Optional, Dict, Any
from datetime import datetime

class SlackNotifier:
    def __init__(self):
        self.webhook_url = os.getenv('SLACK_WEBHOOK_URL')
        self.enabled = bool(self.webhook_url)
        
    def send_notification(self, 
                         message: str, 
                         level: str = 'info',
                         additional_data: Optional[Dict[str, Any]] = None) -> bool:
        """
        Send notification to Slack
        Returns: bool indicating success
        """
        if not self.enabled:
            logging.warning("Slack notifications disabled - no webhook URL")
            return False
            
        try:
            color = {
                'info': '#36a64f',
                'warning': '#ff9400',
                'error': '#ff0000'
            }.get(level, '#36a64f')

            payload = {
                "attachments": [{
                    "color": color,
                    "blocks": [
                        {
                            "type": "section",
                            "text": {
                                "type": "mrkdwn",
                                "text": message
                            }
                        }
                    ],
                    "footer": "Hempire Enterprise",
                    "ts": str(int(datetime.now().timestamp()))
                }]
            }

            if additional_data:
                payload["attachments"][0]["fields"] = [
                    {"title": k, "value": str(v), "short": True}
                    for k, v in additional_data.items()
                ]

            response = requests.post(
                self.webhook_url,
                data=json.dumps(payload),
                headers={'Content-Type': 'application/json'},
                timeout=5
            )
            response.raise_for_status()
            return True

        except Exception as e:
            logging.error(f"Slack notification failed: {e}")
            return False