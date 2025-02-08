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
        logging.info(f"Slack notifications {'enabled' if self.enabled else 'disabled'}")
        
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
            logging.debug(f"Sending Slack notification to {self.webhook_url[:20]}...")
            
            payload = {
                "blocks": [
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": message
                        }
                    }
                ]
            }

            if additional_data:
                fields = []
                for k, v in additional_data.items():
                    fields.append({
                        "type": "mrkdwn",
                        "text": f"*{k}:* {v}"
                    })
                
                payload["blocks"].append({
                    "type": "section",
                    "fields": fields
                })

            response = requests.post(
                self.webhook_url,
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            if response.status_code == 200:
                logging.info("Slack notification sent successfully")
                return True
            else:
                logging.error(f"Slack API error: {response.status_code} - {response.text}")
                return False

        except Exception as e:
            logging.error(f"Slack notification failed: {e}")
            return False