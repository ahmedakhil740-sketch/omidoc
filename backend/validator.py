import re
from datetime import datetime
from typing import Dict, Any, List

def parse_num(val_str: Any) -> float:
    if isinstance(val_str, (int, float)):
        return float(val_str)
    if not val_str or not isinstance(val_str, str):
        return 0.0
    clean = re.sub(r'[^\d.]', '', val_str.replace(',', ''))
    try:
        return float(clean)
    except Exception:
        return 0.0

def parse_date(date_str: str) -> datetime:
    if not date_str:
        return None
    date_str = date_str.strip()
    formats = [
        "%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%d-%m-%Y",
        "%B %d, %Y", "%b %d, %Y", "%B %d %Y", "%b %d %Y"
    ]
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    return None

def validate_document(category: str, fields: Dict[str, Any], line_items: List[Dict[str, Any]]) -> Dict[str, Any]:
    issues: List[Dict[str, Any]] = []
    status = "valid"  # 'valid' | 'warning' | 'error' | 'needs_review'
    score = 100
    
    # 1. General Check: Low confidence fields
    for key, f_data in fields.items():
        if isinstance(f_data, dict):
            conf = f_data.get("confidence", 1.0)
            val = f_data.get("value", "")
            lbl = f_data.get("label", key)
            if conf < 0.85:
                issues.append({
                    "severity": "warning",
                    "field": key,
                    "title": f"Low AI Confidence on {lbl}",
                    "message": f"AI model confidence for '{lbl}' is {int(conf*100)}%. Requires human verification.",
                    "code": "LOW_CONFIDENCE"
                })
                score -= 10
            if str(val).strip() in ["", "N/A", "Unknown", "None"]:
                issues.append({
                    "severity": "error",
                    "field": key,
                    "title": f"Missing Mandatory Field: {lbl}",
                    "message": f"Required field '{lbl}' could not be located in the document.",
                    "code": "MISSING_FIELD"
                })
                score -= 25

    # 2. Category-Specific Validations
    if category == "Commercial Invoice":
        inv_date_str = fields.get("invoice_date", {}).get("value", "")
        due_date_str = fields.get("due_date", {}).get("value", "")
        subtotal_val = parse_num(fields.get("subtotal", {}).get("value", 0))
        tax_val = parse_num(fields.get("tax_amount", {}).get("value", 0))
        total_val = parse_num(fields.get("grand_total", {}).get("value", 0))
        
        # A. Date order consistency
        d_inv = parse_date(inv_date_str)
        d_due = parse_date(due_date_str)
        if d_inv and d_due and d_due < d_inv:
            issues.append({
                "severity": "error",
                "field": "due_date",
                "title": "Date Inconsistency: Due Date Precedes Invoice Date",
                "message": f"Payment due date ({due_date_str}) occurs before the issue date ({inv_date_str}).",
                "code": "DATE_INCONSISTENCY"
            })
            score -= 30
            
        # B. Overdue check against current date (2026 local context)
        now = datetime(2026, 9, 25)
        if d_due and d_due < now:
            days_overdue = (now - d_due).days
            issues.append({
                "severity": "warning",
                "field": "due_date",
                "title": f"Invoice Payment Overdue ({days_overdue} Days)",
                "message": f"The scheduled due date ({due_date_str}) has lapsed by {days_overdue} days.",
                "code": "INVOICE_OVERDUE"
            })
            score -= 15
            
        # C. Math Discrepancy: Subtotal + Tax vs Grand Total
        expected_total = round(subtotal_val + tax_val, 2)
        if total_val > 0 and subtotal_val > 0:
            diff = abs(total_val - expected_total)
            if diff > 0.05:
                issues.append({
                    "severity": "error",
                    "field": "grand_total",
                    "title": "Arithmetic Discrepancy in Invoice Totals",
                    "message": f"Stated Grand Total (${total_val:,.2f}) does not match Subtotal + Tax (${subtotal_val:,.2f} + ${tax_val:,.2f} = ${expected_total:,.2f}). Delta: ${diff:,.2f}.",
                    "code": "MATH_MISMATCH"
                })
                score -= 35
                
        # D. Line items check
        if line_items:
            line_sum = 0.0
            for item in line_items:
                line_sum += parse_num(item.get("total", 0))
            if subtotal_val > 0 and abs(line_sum - subtotal_val) > 1.0:
                issues.append({
                    "severity": "warning",
                    "field": "subtotal",
                    "title": "Line Items Sum Mismatch",
                    "message": f"Sum of extracted itemized rows (${line_sum:,.2f}) deviates from reported subtotal (${subtotal_val:,.2f}).",
                    "code": "LINE_ITEM_MISMATCH"
                })
                score -= 15

    elif category == "Legal Contract":
        eff_date_str = fields.get("effective_date", {}).get("value", "")
        exp_date_str = fields.get("expiration_date", {}).get("value", "")
        gov_law = fields.get("governing_law", {}).get("value", "")
        liability = fields.get("liability_cap", {}).get("value", "")
        
        d_eff = parse_date(eff_date_str)
        d_exp = parse_date(exp_date_str)
        
        # Expiration check
        now = datetime(2026, 9, 25)
        if d_exp and d_exp < now:
            issues.append({
                "severity": "error",
                "field": "expiration_date",
                "title": "Contract Expired",
                "message": f"The term for this legal agreement concluded on {exp_date_str}. Active execution poses compliance risk.",
                "code": "CONTRACT_EXPIRED"
            })
            score -= 35
            
        # High Risk: Governing Law Missing
        if "not specified" in gov_law.lower() or "n/a" in gov_law.lower():
            issues.append({
                "severity": "error",
                "field": "governing_law",
                "title": "High Risk: Missing Governing Law & Jurisdiction",
                "message": "Agreement does not specify state or federal legal jurisdiction. Creates substantial legal exposure.",
                "code": "HIGH_LEGAL_EXPOSURE"
            })
            score -= 30
            
        # High Risk: Uncapped Liability
        if "uncapped" in liability.lower() or "unlimited" in liability.lower():
            issues.append({
                "severity": "warning",
                "field": "liability_cap",
                "title": "Critical Clause: Uncapped / Unlimited Indemnification",
                "message": "Contract contains open-ended liability without standard limitation caps (e.g. 1x or 2x annual contract value).",
                "code": "UNCAPPED_LIABILITY"
            })
            score -= 20

    elif category == "Compliance Audit":
        status_val = fields.get("status", {}).get("value", "")
        score_val = parse_num(fields.get("compliance_score", {}).get("value", 100))
        deadline_str = fields.get("corrective_deadline", {}).get("value", "")
        
        if "action required" in status_val.lower() or "failed" in status_val.lower():
            issues.append({
                "severity": "error",
                "field": "status",
                "title": "Audit Flagged: Immediate Corrective Action Required",
                "message": f"Facility failed compliance threshold with score {score_val}%. Critical environmental / safety non-conformances identified.",
                "code": "AUDIT_FAILURE"
            })
            score -= 40
            
        d_dead = parse_date(deadline_str)
        now = datetime(2026, 9, 25)
        if d_dead and (d_dead - now).days <= 10:
            issues.append({
                "severity": "warning",
                "field": "corrective_deadline",
                "title": "Urgent Remediation Window (Under 10 Days)",
                "message": f"Formal corrective response required before {deadline_str}. Failure to submit results in regulatory halt.",
                "code": "TIGHT_DEADLINE"
            })
            score -= 15

    elif category == "Identity Verification":
        exp_str = fields.get("expiry_date", {}).get("value", "")
        d_exp = parse_date(exp_str)
        now = datetime(2026, 9, 25)
        if d_exp:
            if d_exp < now:
                issues.append({
                    "severity": "error",
                    "field": "expiry_date",
                    "title": "Identification Document Expired",
                    "message": f"Document expired on {exp_str}. Cannot be used for KYC / employment authorization.",
                    "code": "ID_EXPIRED"
                })
                score -= 50
            elif (d_exp - now).days < 30:
                issues.append({
                    "severity": "warning",
                    "field": "expiry_date",
                    "title": "Document Expiring Within 30 Days",
                    "message": f"Document will expire on {exp_str}. Flag for secondary verification.",
                    "code": "ID_EXPIRING_SOON"
                })
                score -= 15

    # Determine final status
    severities = [i["severity"] for i in issues]
    if "error" in severities:
        status = "error"
    elif "warning" in severities:
        status = "warning"
    elif any(i.get("code") == "LOW_CONFIDENCE" for i in issues):
        status = "needs_review"
    else:
        status = "valid"

    return {
        "status": status,
        "validation_score": max(0, score),
        "issues_count": len(issues),
        "issues": issues,
        "is_approved": status == "valid"
    }
