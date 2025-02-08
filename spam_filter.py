# spam_filter.py
import re
from typing import Dict, List, Tuple
import langdetect
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
import logging

# Download required NLTK data
try:
    nltk.download('punkt', quiet=True)
    nltk.download('stopwords', quiet=True)
    nltk.download('averaged_perceptron_tagger', quiet=True)
except Exception as e:
    logging.warning(f"NLTK download failed: {e}")

class SpamFilter:
    def __init__(self):
        self.spam_triggers = [
            'casino', 'viagra', 'crypto', 'bitcoin', 'lottery', 
            'winner', 'investment opportunity', 'forex trading',
            'make money fast', 'work from home', 'earn extra cash',
            'binary options', 'dear sir', 'dear madam', 'dear beneficiary',
            'inheritance', 'bank transfer', 'wire transfer',
            'congratulations you won', 'claim your prize', 'darkweb',
            'million dollar', 'instant cash', 'dating', 'singles',
            'weight loss', 'diet pills', 'enlarge', 'pharmacy',
            'replica watches', 'buy meds', 'online pharmacy'
        ]
        
        self.legitimate_words = [
            'loan', 'business', 'financing', 'equipment', 'funding',
            'capital', 'investment', 'interest rate', 'payment',
            'credit', 'application', 'monthly payment', 'down payment',
            'business plan', 'cash flow', 'invoice', 'revenue',
            'lease', 'purchase', 'machine', 'manufacturing', 'industry',
            'commercial', 'enterprise', 'company', 'corporation'
        ]

        self.inappropriate_words = {
            'adult', 'explicit', 'nsfw', 'xxx', 'porn',
            'sex', 'naked', 'nude', 'drugs', 'pills'
        }

    def analyze_text_structure(self, text: str) -> List[str]:
        """Analyze text structure for spam indicators"""
        issues = []
        
        # Check sentence structure using NLTK
        try:
            tokens = word_tokenize(text)
            if len(tokens) < 3:
                issues.append("Too few words")
            
            # Check for excessive punctuation
            punct_count = sum(1 for c in text if c in '!?.')
            if punct_count / len(text) > 0.1:
                issues.append("Excessive punctuation")
            
            # Check for repeated words
            words = [word.lower() for word in tokens if word.isalnum()]
            word_freq = {word: words.count(word) for word in set(words)}
            if any(count > 3 for count in word_freq.values()):
                issues.append("Word repetition")
                
        except Exception as e:
            logging.error(f"Text analysis error: {e}")
            
        return issues

    def check_message(self, data: Dict) -> Tuple[bool, List[str]]:
        """Returns (is_spam: bool, reasons: List[str])"""
        reasons = []
        message = data.get('message', '').lower()
        
        # Basic validation
        if not message or len(message) < 10:
            return True, ["Message too short"]
        
        try:
            # 1. Language detection
            lang = langdetect.detect(message)
            if lang != 'en':
                reasons.append(f"Non-English content detected ({lang})")

            # 2. Spam trigger words
            spam_words = [word for word in self.spam_triggers 
                         if word in message]
            if spam_words:
                reasons.append(f"Spam triggers: {', '.join(spam_words)}")

            # 3. Business terminology check
            legitimate_count = sum(1 for word in self.legitimate_words 
                                if word in message)
            if legitimate_count == 0:
                reasons.append("No business-related terms")

            # 4. Email validation
            email = data.get('email', '')
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_pattern, email):
                reasons.append("Invalid email format")

            # 5. Phone number validation
            phone = data.get('phone_number', '')
            phone_cleaned = re.sub(r'\D', '', phone)
            if not (9 <= len(phone_cleaned) <= 15):
                reasons.append("Invalid phone number")

            # 6. Text structure analysis
            structure_issues = self.analyze_text_structure(message)
            reasons.extend(structure_issues)

            # 7. Check for inappropriate content
            inappropriate = any(word in message for word in self.inappropriate_words)
            if inappropriate:
                reasons.append("Inappropriate content")

            # 8. URL density check
            urls = re.findall(r'http[s]?://\S+', message)
            if len(urls) > 2:
                reasons.append("Too many URLs")

        except Exception as e:
            logging.error(f"Spam check error: {e}")
            reasons.append("Error in spam detection")

        return bool(reasons), reasons