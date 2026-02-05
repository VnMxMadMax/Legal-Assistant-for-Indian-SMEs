"""
Legal Assistant Configuration
"""
import os
from dotenv import load_dotenv

load_dotenv()

# API Configuration - Users must provide their own key
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# Model Selection Options
MODEL_OPTIONS = {
    "gpt-4o": {
        "name": "GPT-4o (Default – Faster & Cost Efficient)",
        "description": "GPT-4-class model optimized for speed and cost",
        "default": True
    },
    "gpt-4": {
        "name": "GPT-4 (Optional – Higher Cost)",
        "description": "Original GPT-4 model for users who prefer it",
        "default": False
    }
}

LLM_MODEL = "gpt-4o"  # Default model

# Application Settings
APP_NAME = "Legal Assistant for SMEs"
APP_VERSION = "1.0.0"

# File Processing Settings
MAX_FILE_SIZE_MB = 15
SUPPORTED_EXTENSIONS = [".pdf", ".docx", ".doc", ".txt"]

# Average tokens per page (for estimation)
TOKENS_PER_PAGE = 800

# Contract Types
CONTRACT_TYPES = [
    "Employment Agreement",
    "Vendor Contract",
    "Lease Agreement",
    "Partnership Deed",
    "Service Contract",
    "Non-Disclosure Agreement",
    "Unknown"
]

# Risk Levels
RISK_LEVELS = {
    "LOW": {"score_range": (0, 3), "color": "#28a745", "label": "Low Risk"},
    "MEDIUM": {"score_range": (4, 6), "color": "#ffc107", "label": "Medium Risk"},
    "HIGH": {"score_range": (7, 10), "color": "#dc3545", "label": "High Risk"}
}

# Clause Categories for Risk Analysis
RISKY_CLAUSE_TYPES = [
    "penalty_clause",
    "indemnity_clause",
    "unilateral_termination",
    "arbitration_jurisdiction",
    "auto_renewal",
    "lock_in_period",
    "non_compete",
    "ip_transfer",
    "liability_limitation",
    "force_majeure"
]

# Obligation Indicators
OBLIGATION_KEYWORDS = ["shall", "must", "will", "agrees to", "undertakes to", "is required to"]
RIGHT_KEYWORDS = ["may", "is entitled to", "has the right to", "can", "is permitted to"]
PROHIBITION_KEYWORDS = ["shall not", "must not", "may not", "is prohibited from", "cannot"]

# Paths
EXPORTS_DIR = "exports"
LOGS_DIR = "logs"
TEMPLATES_DIR = "templates"
