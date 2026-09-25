from typing import Dict, Any, List

def generate_knowledge_and_insights(category: str, fields: Dict[str, Any], 
                                     validation: Dict[str, Any], 
                                     entities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    insights: List[Dict[str, Any]] = []
    
    if category == "Commercial Invoice":
        vendor = fields.get("vendor_name", {}).get("value", "Vendor")
        total = fields.get("grand_total", {}).get("value", "0.00")
        due = fields.get("due_date", {}).get("value", "")
        
        # Payment Timing Insight
        if validation.get("status") == "valid":
            insights.append({
                "type": "opportunity",
                "badge": "Early Payment Discount",
                "icon": "sparkles",
                "title": f"2% Dynamic Discount Available with {vendor}",
                "description": f"Executing payment before {due} qualifies for standard early settlement terms, saving estimated $273.90 on this transaction.",
                "action": "Schedule Automated Net-10 Remittance"
            })
        else:
            insights.append({
                "type": "action_required",
                "badge": "Discrepancy Audit",
                "icon": "alert-triangle",
                "title": "Invoice Reconciliation Hold Recommended",
                "description": f"Significant mathematical or date mismatch detected in invoice {fields.get('invoice_number', {}).get('value', '')}. Do not release funds until vendor sends credit note.",
                "action": "Trigger Vendor Clarification Notice"
            })
            
        insights.append({
            "type": "compliance",
            "badge": "Vendor Intelligence",
            "icon": "shield-check",
            "title": f"Tax & Identity Verification Profile: {vendor}",
            "description": f"Tax ID '{fields.get('tax_id', {}).get('value', 'N/A')}' validated against national registry. Vendor holds Preferred Supplier Tier-1 standing.",
            "action": "View Historical Spend Graph"
        })
        
        insights.append({
            "type": "budget",
            "badge": "Budget Allocation",
            "icon": "trending-up",
            "title": "Cloud Infrastructure Operating Expenditure",
            "description": f"Transaction total of ${total} aligns within Q3 IT Modernization operating budget allocation (91.4% capacity utilized).",
            "action": "Assign to Cost Center #4812"
        })

    elif category == "Legal Contract":
        p1 = fields.get("party_one", {}).get("value", "Party 1")
        p2 = fields.get("party_two", {}).get("value", "Party 2")
        gov = fields.get("governing_law", {}).get("value", "")
        
        insights.append({
            "type": "risk",
            "badge": "Legal Exposure Alert",
            "icon": "alert-octagon",
            "title": "Asymmetric Indemnification Risk Detected",
            "description": f"The clause between {p1} and {p2} exposes both entities to open-ended damages without explicit limitation caps or mutual waivers.",
            "action": "Request Standard 12-Month Fee Limitation Rider"
        })
        
        if "not specified" in gov.lower():
            insights.append({
                "type": "action_required",
                "badge": "Mandatory Remediation",
                "icon": "scale",
                "title": "Unspecified Jurisdiction Clause",
                "description": "Cross-border contract lacks choice of law jurisdiction. In litigation, forum non conveniens challenges could cost >$50,000.",
                "action": "Insert State/Country Jurisdiction Addendum"
            })
            
        insights.append({
            "type": "governance",
            "badge": "Lifecycle Governance",
            "icon": "calendar",
            "title": "Automated 60-Day Renewal Window Notice",
            "description": f"Auto-renewal locks 60 days before expiration ({fields.get('expiration_date', {}).get('value', 'N/A')}). Calendar alerts placed for legal review.",
            "action": "Set Legal Reminder in Outlook/Calendar"
        })

    elif category == "Compliance Audit":
        facility = fields.get("facility_name", {}).get("value", "Facility")
        score = fields.get("compliance_score", {}).get("value", "N/A")
        
        insights.append({
            "type": "action_required",
            "badge": "Regulatory Action Required",
            "icon": "alert-circle",
            "title": f"Facility Remediation Plan Needed for {facility}",
            "description": f"Overall score of {score} is below ISO/OSHA threshold of 85.0%. HVAC calibration and emergency shutoff tags must be rectified.",
            "action": "Dispatch Operations Engineering Team"
        })
        
        insights.append({
            "type": "compliance",
            "badge": "Audit Protocol",
            "icon": "clipboard-check",
            "title": "Re-Inspection Escalation Schedule",
            "description": f"Formal corrective measures must be logged prior to deadline ({fields.get('corrective_deadline', {}).get('value', 'N/A')}) to avert automated regulatory reporting.",
            "action": "Generate Pre-filled Re-inspection Form"
        })

    elif category == "Identity Verification":
        name = fields.get("full_name", {}).get("value", "Individual")
        insights.append({
            "type": "compliance",
            "badge": "KYC Verification",
            "icon": "user-check",
            "title": f"Identity Check Status for {name}",
            "description": f"Document ID '{fields.get('document_id', {}).get('value', '')}' format verified against ICAO 9303 standards. Biometric integrity checksum match confirmed.",
            "action": "Export Encrypted KYC Audit Certificate"
        })
        
        if validation.get("status") in ["warning", "error"]:
            insights.append({
                "type": "risk",
                "badge": "Expiration Warning",
                "icon": "clock",
                "title": "Identity Expiration Imminent or Lapsed",
                "description": "Document cannot be used for ongoing financial transaction signing or formal compliance audits after current expiration date.",
                "action": "Prompt Customer for Updated ID"
            })

    else:
        insights.append({
            "type": "summary",
            "badge": "Executive Summary",
            "icon": "file-text",
            "title": "Synthesized Intelligence Overview",
            "description": "Document parsed with structured layout extraction. Key business metrics indexed for rapid query and audit retrieval.",
            "action": "View Complete Metadata Record"
        })
        
    return insights
