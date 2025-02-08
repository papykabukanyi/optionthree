# New spam_filter.py file
import re
from typing import Dict, List, Tuple
import langdetect
from profanity_check import predict_prob

class SpamFilter:
    def __init__(self):
        # Common spam trigger words/phrases
        self.spam_triggers = [
            'casino', 'viagra', 'crypto', 'bitcoin', 'lottery', 
            'winner', 'investment opportunity', 'forex trading',
            'make money fast', 'work from home', 'earn extra cash',
            'binary options', 'dear sir', 'dear madam', 'dear beneficiary',
            'inheritance', 'bank transfer', 'wire transfer',
            'congratulations you won', 'claim your prize'
        ]
        
        # Business financing related legitimate words
        self.legitimate_words = [
            'loan', 'business', 'financing', 'equipment', 'funding',
            'capital', 'investment', 'interest rate', 'payment',
            'credit', 'application', 'monthly payment', 'down payment',
            'business plan', 'cash flow', 'invoice', 'revenue'
        ]

    def check_message(self, data: Dict) -> Tuple[bool, List[str]]:
        """
        Returns (is_spam: bool, reasons: List[str])
        """
        reasons = []
        
        # 1. Check message length
        if len(data['message']) < 10:
            reasons.append("Message too short")
        
        # 2. Check language
        try:
            lang = langdetect.detect(data['message'])
            if lang != 'en':
                reasons.append(f"Non-English content detected ({lang})")
        except:
            reasons.append("Unable to determine language")

        # 3. Check for spam trigger words
        message_lower = data['message'].lower()
        spam_words = [word for word in self.spam_triggers 
                     if word in message_lower]
        if spam_words:
            reasons.append(f"Spam trigger words found: {', '.join(spam_words)}")

        # 4. Check for legitimate business terms
        legitimate_count = sum(1 for word in self.legitimate_words 
                             if word in message_lower)
        if legitimate_count == 0:
            reasons.append("No business-related terms found")

        # 5. Check email format
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, data['email']):
            reasons.append("Invalid email format")

        # 6. Check phone number format
        phone_pattern = r'^\+?1?\d{9,15}$'
        if not re.match(phone_pattern, data['phone_number']):
            reasons.append("Invalid phone number format")

        # 7. Check profanity/toxicity
        profanity_score = predict_prob([data['message']])[0]
        if profanity_score > 0.5:
            reasons.append(f"High profanity score: {profanity_score:.2f}")

        # 8. Check for excessive capitals
        caps_ratio = sum(1 for c in data['message'] if c.isupper()) / len(data['message'])
        if caps_ratio > 0.5:
            reasons.append("Excessive use of capital letters")

        # Message is considered spam if it has any reasons
        return bool(reasons), reasons