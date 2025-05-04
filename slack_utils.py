# slack_utils.py
import os
import json
import requests
import logging
from typing import Optional, Dict, Any
from datetime import datetime
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

class SlackNotifier:
    def __init__(self):
        self.webhook_url = os.getenv('SLACK_WEBHOOK_URL')
        self.enabled = bool(self.webhook_url)
        self.session = self._create_session()
        logging.info(f"Slack notifications {'enabled' if self.enabled else 'disabled'}")
        
    def _create_session(self):
        """Create requests session with retry logic"""
        session = requests.Session()
        retries = Retry(
            total=3,
            backoff_factor=0.5,
            status_forcelist=[500, 502, 503, 504]
        )
        session.mount('https://', HTTPAdapter(max_retries=retries))
        return session

    def format_message(self, message: str, level: str, data: Optional[Dict] = None) -> Dict:
        """Enhanced message formatting"""
        color = {
            'info': '#36a64f',
            'warning': '#ffd700',
            'error': '#ff0000'
        }.get(level, '#808080')

        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "🔔 New Notification"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": message
                }
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Time:* {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                    }
                ]
            }
        ]

        if data:
            fields = []
            for k, v in data.items():
                fields.append({
                    "type": "mrkdwn",
                    "text": f"*{k}:* {v}"
                })
            
            blocks.append({
                "type": "section",
                "fields": fields
            })

        return {
            "blocks": blocks,
            "attachments": [{
                "color": color
            }]
        }

    def send_notification(self, 
                         message: str, 
                         level: str = 'info',
                         additional_data: Optional[Dict[str, Any]] = None) -> bool:
        """Enhanced notification sending with retry logic"""
        if not self.enabled:
            logging.warning("Slack notifications disabled - no webhook URL")
            return False
            
        try:
            payload = self.format_message(message, level, additional_data)
            
            response = self.session.post(
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