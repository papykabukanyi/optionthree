# spam_filter.py
import re
from typing import Dict, List, Tuple
import langdetect
import nltk
from nltk.tokenize import word_tokenize
from collections import Counter
import logging
import time

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
            # Existing triggers +
            'casino', 'viagra', 'crypto', 'bitcoin', 'lottery',
            # New financial scam terms
            'investment opportunity', 'forex', 'binary options', 'quick cash',
            'earn from home', 'money back guarantee', 'risk-free investment',
            # Suspicious phrases
            'dear friend', 'dear beneficiary', 'congratulations you',
            'won lottery', 'inheritance claim', 'bank transfer',
            # Medical/pharma spam
            'discount meds', 'online pharmacy', 'cheap pills', 'buy prescription',
            # Crypto/finance 
            'cryptocurrency', 'blockchain', 'ico', 'token sale', 'mining rig',
            # Adult content
            'dating site', 'meet singles', 'adult friend', 'hot singles'
        ]

        # Increased legitimate business terms
        self.legitimate_words = [
            'loan', 'business', 'financing', 'equipment', 'funding',
            'capital', 'investment', 'interest rate', 'payment terms',
            'credit application', 'monthly payment', 'down payment',
            'business plan', 'cash flow', 'invoice', 'revenue projections',
            'lease terms', 'purchase order', 'manufacturing', 'industry',
            'commercial', 'enterprise', 'incorporation', 'tax id',
            'ein number', 'business license', 'vendor', 'supplier'
        ]

        self.spam_patterns = [
            r'\d+%\s*(ROI|return|profit)',  # ROI promises
            r'[A-Z]{5,}',  # EXCESSIVE CAPS
            r'[\$€£]\d+[KkMm]?(?:\s*[-+]\s*[\$€£]\d+[KkMm]?)*', # Money amounts
            r'(?:bit\.ly|tinyurl\.com|goo\.gl)\/\w+',  # Short URLs
            r'(?:password|account|login|bank)\s*details?',  # Suspicious requests
            r'\b(?:viagra|cialis|pharmacy)\b',  # Pharma spam
            r'\b(?:crypto|bitcoin|eth|bnb)\b',  # Crypto terms
            r'(?:urgent|immediate)\s*(?:reply|response|action)',  # Urgency
            r'(?:free|bonus|discount)\s*(?:offer|gift|prize)',  # Promotional
            r'(?:million|billion|trillion)\s*dollars?' # Large amounts
        ]

        self.url_blacklist = [
            'bit.ly', 'tinyurl.com', 'goo.gl', 'ow.ly', 't.co',
            'darkweb', 'crypto', 'btc', 'eth', 'nft'
        ]

        self.rate_limit = {}
        self.rate_window = 3600  # 1 hour
        self.max_attempts = 5

    def check_rate_limit(self, sender: str) -> bool:
        """Check if sender has exceeded rate limit"""
        current_time = time.time()
        if sender in self.rate_limit:
            attempts, first_attempt = self.rate_limit[sender]
            if current_time - first_attempt > self.rate_window:
                self.rate_limit[sender] = (1, current_time)
                return False
            if attempts >= self.max_attempts:
                return True
            self.rate_limit[sender] = (attempts + 1, first_attempt)
        else:
            self.rate_limit[sender] = (1, current_time)
        return False

    def analyze_urls(self, message: str) -> List[str]:
        """Enhanced URL analysis"""
        issues = []
        urls = re.findall(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', message)
        
        if len(urls) > 3:
            issues.append("Excessive URLs detected")
            
        for url in urls:
            if any(blacklisted in url.lower() for blacklisted in self.url_blacklist):
                issues.append(f"Suspicious URL detected: {url}")
            if url.count('.') > 3:
                issues.append(f"Complex URL structure: {url}")
                
        return issues

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
        """Enhanced spam detection"""
        reasons = []
        message = data.get('message', '').lower()
        sender = data.get('email', '')

        if not message or len(message) < 10:
            return True, ["Message too short"]

        # Rate limiting
        if self.check_rate_limit(sender):
            return True, ["Rate limit exceeded"]

        try:
            # Language detection
            if langdetect.detect(message) != 'en':
                reasons.append("Non-English content detected")

            # Pattern matching
            for pattern in self.spam_patterns:
                if re.search(pattern, message, re.I):
                    reasons.append(f"Suspicious pattern detected: {pattern}")

            # Spam trigger words
            spam_words = [word for word in self.spam_triggers if word in message]
            if spam_words:
                reasons.append(f"Spam triggers: {', '.join(spam_words)}")

            # URL analysis
            url_issues = self.analyze_urls(message)
            reasons.extend(url_issues)

            # Content analysis
            words = word_tokenize(message.lower())
            word_freq = Counter(words)

            # Check word repetition
            if any(count > 5 for count in word_freq.values()):
                reasons.append("Excessive word repetition")

            # Check character repetition
            if any(message.count(char) > len(message) * 0.1 for char in '!?.$@'):
                reasons.append("Excessive special characters")

            # Check for legitimate business content
            legitimate_count = sum(1 for word in self.legitimate_words if word in message)
            if legitimate_count == 0:
                reasons.append("No business-related terms")

        except Exception as e:
            logging.error(f"Spam check error: {e}")
            reasons.append("Error in spam detection")

        # Scoring
        spam_score = len(reasons)
        is_spam = spam_score >= 2

        return is_spam, reasons