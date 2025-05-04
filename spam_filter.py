# spam_filter.py
import re
from typing import Dict, List, Tuple
import logging
import time
from datetime import datetime
from collections import Counter

# Try importing optional ML dependencies
try:
    import numpy as np
    import joblib
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.ensemble import IsolationForest
    ML_ENABLED = True
except ImportError:
    ML_ENABLED = False
    logging.warning("ML dependencies not found. Running with basic spam detection only.")

# Try importing NLTK
try:
    import nltk
    from nltk.tokenize import word_tokenize
    nltk.download('punkt', quiet=True)
    nltk.download('stopwords', quiet=True)
    nltk.download('averaged_perceptron_tagger', quiet=True)
    NLTK_ENABLED = True
except ImportError:
    NLTK_ENABLED = False
    logging.warning("NLTK not found. Running with basic text analysis only.")

try:
    import langdetect
    LANGDETECT_ENABLED = True
except ImportError:
    LANGDETECT_ENABLED = False
    logging.warning("langdetect not found. Language detection disabled.")

class SpamFilter:
    def __init__(self):
        self.spam_triggers = [
            # Common spam patterns
            'casino', 'viagra', 'crypto', 'bitcoin', 'lottery',
            # AI/Tech scams
            'ai investment', 'trading bot', 'auto trading', 'mining profits',
            # Sophisticated financial scams
            'private equity', 'hedge fund opportunity', 'guaranteed returns',
            'exclusive investment', 'pre-ipo', 'seed round', 'venture capital',
            # Modern phishing attempts
            'account security', 'verify identity', 'unusual activity',
            'login attempt', 'password reset', 'account compromise',
            # Emerging crypto scams
            'defi', 'yield farming', 'smart contract', 'web3', 'nft mint',
            'metaverse land', 'token presale', 'airdrop', 'blockchain gaming',
            # Business email compromise
            'urgent wire', 'invoice due', 'payment pending', 'account update',
            'tax refund', 'payroll update', 'direct deposit change'
        ]

        # Initialize ML components if available
        if ML_ENABLED:
            self.vectorizer = TfidfVectorizer(max_features=1000)
            self.detector = IsolationForest(contamination=0.1, random_state=42)
            try:
                self.detector = joblib.load('spam_model.joblib')
                self.vectorizer = joblib.load('vectorizer.joblib')
            except:
                logging.info("No existing ML model found. Will train on new data.")
        
        # Enhanced rate limiting
        self.rate_limit = {}
        self.rate_window = 3600  # 1 hour
        self.max_attempts = 5
        self.suspicious_ips = set()

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

    def analyze_metadata(self, data: Dict) -> List[str]:
        """Analyze submission metadata for suspicious patterns"""
        issues = []
        
        # Time-based analysis
        hour = datetime.now().hour
        if hour < 6 or hour > 22:  # Outside business hours
            issues.append("Suspicious submission time")
            
        # IP analysis
        ip = data.get('ip_address', '')
        if ip in self.suspicious_ips:
            issues.append("Previously flagged IP")
            
        return issues

    def analyze_text_structure(self, text: str) -> List[str]:
        """Analyze text structure for spam indicators"""
        issues = []
        
        # Check sentence structure using NLTK
        if NLTK_ENABLED:
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
        else:
            logging.warning("NLTK not enabled. Skipping text structure analysis.")
            
        return issues

    def analyze_content(self, message: str) -> List[str]:
        """Analyze content for spam indicators"""
        issues = []
        try:
            # URL analysis
            url_issues = self.analyze_urls(message)
            issues.extend(url_issues)

            # Content analysis
            words = word_tokenize(message.lower()) if NLTK_ENABLED else message.lower().split()
            word_freq = Counter(words)

            # Check word repetition
            if any(count > 5 for count in word_freq.values()):
                issues.append("Excessive word repetition")

            # Check character repetition
            if any(message.count(char) > len(message) * 0.1 for char in '!?.$@'):
                issues.append("Excessive special characters")

        except Exception as e:
            logging.error(f"Content analysis error: {e}")
            issues.append("Error in content analysis")
            
        return issues

    def check_message(self, data: Dict) -> Tuple[bool, List[str]]:
        """Enhanced spam detection with graceful fallback"""
        reasons = []
        message = data.get('message', '').lower()
        sender = data.get('email', '')
        ip_address = data.get('ip_address', '')

        if not message or len(message) < 10:
            return True, ["Message too short"]

        try:
            # Basic pattern matching
            for pattern in self.spam_triggers:
                if pattern in message:
                    reasons.append(f"Suspicious pattern: {pattern}")

            # Rate limiting
            if self.check_rate_limit(sender):
                self.suspicious_ips.add(ip_address)
                reasons.append("Rate limit exceeded")

            # ML-based detection if available
            if ML_ENABLED and hasattr(self, 'vectorizer') and hasattr(self, 'detector'):
                features = self.vectorizer.transform([message])
                if self.detector.predict(features.toarray())[0] == -1:
                    reasons.append("ML model flagged as suspicious")

            # NLTK analysis if available
            if NLTK_ENABLED:
                text_issues = self.analyze_text_structure(message)
                reasons.extend(text_issues)

            # Content analysis
            content_issues = self.analyze_content(message)
            reasons.extend(content_issues)

        except Exception as e:
            logging.error(f"Spam check error: {e}")
            reasons.append("Error in spam detection")

        spam_score = self.calculate_spam_score(reasons)
        is_spam = spam_score >= 0.7

        return is_spam, reasons

    def calculate_spam_score(self, reasons: List[str]) -> float:
        """Calculate weighted spam score"""
        weights = {
            "ML model flagged": 0.8,
            "Rate limit": 0.9,
            "Suspicious pattern": 0.6,
            "Metadata issue": 0.5,
            "Content issue": 0.4
        }
        
        score = 0
        for reason in reasons:
            for key, weight in weights.items():
                if key in reason:
                    score += weight
                    break
                    
        return min(score / len(weights), 1.0)