import re
from typing import Tuple, Dict, Any

CATEGORIES = {
    "Commercial Invoice": {
        "keywords": ["invoice", "bill to", "sold to", "remit to", "tax invoice", "subtotal", "gstin", "vat", "due date", "amount due", "payment terms", "line item", "po number", "unit price"],
        "patterns": [r"inv[-\s]?[0-9a-z]{3,}", r"total\s+amount", r"balance\s+due", r"qty\s+unit\s+price"],
        "weight": 1.2
    },
    "Legal Contract": {
        "keywords": ["agreement", "master services agreement", "terms and conditions", "indemnification", "confidentiality", "governing law", "jurisdiction", "breach", "force majeure", "parties hereto", "severability", "arbitration"],
        "patterns": [r"this\s+agreement\s+is\s+entered", r"whereas", r"in\s+witness\s+whereof", r"section\s+\d+"],
        "weight": 1.1
    },
    "Compliance Audit": {
        "keywords": ["audit report", "safety inspection", "compliance assessment", "non-conformance", "corrective action", "inspector", "hazard", "osha", "iso 9001", "remediation", "inspection checklist", "passed", "failed"],
        "patterns": [r"audit\s+id", r"findings\s+and\s+observations", r"corrective\s+action\s+request", r"inspection\s+score"],
        "weight": 1.15
    },
    "Identity Verification": {
        "keywords": ["passport", "driver license", "national identity", "date of birth", "identification", "nationality", "issuing authority", "expiry date", "sex", "citizenship", "id number", "full legal name"],
        "patterns": [r"dob:\s*\d{2}", r"passport\s+no", r"national\s+id", r"issuing\s+country"],
        "weight": 1.2
    },
    "Medical Claim": {
        "keywords": ["patient name", "claim form", "diagnosis code", "icd-10", "provider", "healthcare", "treatment date", "insurance policy", "copay", "prescription", "hospital"],
        "patterns": [r"patient\s+id", r"policy\s+number", r"diagnostic\s+code", r"claim\s+amount"],
        "weight": 1.1
    }
}

def classify_document(text: str, filename: str = "") -> Tuple[str, float, Dict[str, float]]:
    text_lower = (text + " " + filename).lower()
    scores: Dict[str, float] = {}
    
    for category, config in CATEGORIES.items():
        score = 0.0
        # Keyword matches
        for kw in config["keywords"]:
            count = text_lower.count(kw)
            if count > 0:
                score += min(count * 8.0, 32.0)
                
        # Regex patterns
        for pattern in config["patterns"]:
            matches = len(re.findall(pattern, text_lower))
            if matches > 0:
                score += min(matches * 15.0, 45.0)
                
        # Apply category specific weighting
        score *= config.get("weight", 1.0)
        scores[category] = round(score, 2)
        
    # Check if empty or no strong match
    best_cat = max(scores, key=scores.get)
    max_score = scores[best_cat]
    
    if max_score < 10.0:
        # Fallback to general report or check filename
        if "invoice" in filename.lower() or "bill" in filename.lower():
            return "Commercial Invoice", 0.85, scores
        elif "contract" in filename.lower() or "agreement" in filename.lower() or "nda" in filename.lower():
            return "Legal Contract", 0.85, scores
        elif "audit" in filename.lower() or "inspection" in filename.lower():
            return "Compliance Audit", 0.85, scores
        elif "id" in filename.lower() or "passport" in filename.lower() or "kyc" in filename.lower():
            return "Identity Verification", 0.85, scores
        else:
            return "Business Report", 0.72, scores
            
    # Normalize confidence to 0.82 - 0.99
    confidence = min(0.99, max(0.82, 0.75 + (max_score / (max_score + 40.0)) * 0.24))
    return best_cat, round(confidence, 2), scores
