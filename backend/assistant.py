import re
from typing import Dict, Any, List, Tuple

def answer_document_query(query: str, doc_data: Dict[str, Any]) -> Tuple[str, List[Dict[str, str]]]:
    """
    Answers questions about a specific document using grounded extraction data and raw text.
    Returns: (answer_markdown, citations_list)
    """
    q = query.lower().strip()
    category = doc_data.get("category", "")
    fields = doc_data.get("fields", {})
    validation = doc_data.get("validation", {})
    insights = doc_data.get("insights", [])
    raw_text = doc_data.get("raw_text", "")
    citations = []
    
    # 1. Total amount / Money / Cost questions
    if any(k in q for k in ["total", "amount", "cost", "price", "subtotal", "tax", "fee", "how much", "pay"]):
        if category == "Commercial Invoice":
            gt = fields.get("grand_total", {}).get("value", "N/A")
            sub = fields.get("subtotal", {}).get("value", "N/A")
            tax = fields.get("tax_amount", {}).get("value", "N/A")
            citations.append({"section": "Summary of Charges", "page": "Page 1", "field": "Grand Total"})
            
            # Check if there is an error
            math_issues = [i for i in validation.get("issues", []) if "math" in i.get("code", "").lower() or "line_item" in i.get("code", "").lower()]
            warn_text = ""
            if math_issues:
                warn_text = f"\n\n> ⚠️ **Audit Alert**: {math_issues[0]['message']}"
                
            return (
                f"### Financial Summary\n"
                f"* **Grand Total Due**: **${gt}**\n"
                f"* **Subtotal**: ${sub}\n"
                f"* **Tax / VAT**: ${tax}\n"
                f"* **Payment Terms**: {fields.get('payment_terms', {}).get('value', 'Net 15')}"
                f"{warn_text}",
                citations
            )
        elif category == "Legal Contract":
            liab = fields.get("liability_cap", {}).get("value", "Unspecified")
            citations.append({"section": "Limitation of Liability", "page": "Page 2", "field": "Liability Cap"})
            return (
                f"In this legal agreement, the financial exposure clause states:\n"
                f"* **Liability Cap**: **{liab}**\n"
                f"* Note: Standard monetary fees are governed under individual Statements of Work (SOWs).",
                citations
            )

    # 2. Deadlines / Dates / Expiry
    if any(k in q for k in ["deadline", "due", "date", "expir", "when", "valid until"]):
        dates_found = []
        for k, v in fields.items():
            if "date" in k or "deadline" in k or "expir" in k:
                dates_found.append(f"* **{v.get('label', k)}**: `{v.get('value')}` (Confidence: {int(v.get('confidence', 0.9)*100)}%)")
                citations.append({"section": v.get("label", k), "page": f"Page {v.get('page', 1)}", "field": k})
                
        if dates_found:
            return (
                f"### Key Dates & Deadlines Identified\n" + "\n".join(dates_found),
                citations
            )

    # 3. Risks / Anomalies / Warnings / Errors
    if any(k in q for k in ["risk", "issue", "error", "warning", "anomal", "problem", "discrepanc", "fail"]):
        issues = validation.get("issues", [])
        if not issues:
            return (
                f"✅ **No critical risks or validation errors detected**.\n\n"
                f"The document conforms to standard enterprise schema with an overall validation health score of **{validation.get('validation_score', 100)}/100**.",
                [{"section": "Validation Engine", "page": "All Pages", "field": "Health Score"}]
            )
        
        issue_lines = []
        for iss in issues:
            sev_icon = "🔴" if iss["severity"] == "error" else "🟡"
            issue_lines.append(f"{sev_icon} **{iss['title']}**\n   {iss['message']}")
            citations.append({"section": iss.get("field", "Validation"), "page": "Audit Log", "field": iss.get("code", "")})
            
        return (
            f"### Detected Compliance & Risk Findings ({len(issues)} item{'s' if len(issues)>1 else ''})\n\n" +
            "\n\n".join(issue_lines),
            citations
        )

    # 4. Summary / Overview / What is this document
    if any(k in q for k in ["summar", "overview", "what is", "explain", "about", "tell me"]):
        citations.append({"section": "Document Overview", "page": "Page 1", "field": "Classification"})
        
        summary_body = f"This document has been identified as a **{category}** (confidence: {int(doc_data.get('category_confidence', 0.95)*100)}%).\n\n"
        summary_body += f"#### Core Metadata:\n"
        for k, v in list(fields.items())[:5]:
            summary_body += f"* **{v.get('label', k)}**: {v.get('value')}\n"
            
        summary_body += f"\n#### Executive Insights:\n"
        for ins in insights[:2]:
            summary_body += f"* **{ins.get('badge')}**: {ins.get('title')} — *{ins.get('description')}*\n"
            
        return summary_body, citations

    # 5. Vendor / Parties / Names / People
    if any(k in q for k in ["who", "vendor", "party", "parties", "client", "person", "name", "inspector", "customer"]):
        names = []
        for k in ["vendor_name", "customer_name", "party_one", "party_two", "inspector_name", "facility_name", "full_name"]:
            if k in fields:
                names.append(f"* **{fields[k].get('label', k)}**: `{fields[k].get('value')}`")
                citations.append({"section": fields[k].get('label', k), "page": f"Page {fields[k].get('page', 1)}", "field": k})
        if names:
            return "### Identified Entities & Parties\n" + "\n".join(names), citations

    # 6. Fallback Search in Raw Text
    # Search for keywords in raw text
    words = [w for w in re.findall(r'\w+', q) if len(w) > 3 and w not in ["what", "where", "which", "could", "would", "should", "there", "about", "this", "that"]]
    matching_snippets = []
    
    for line in raw_text.split("\n"):
        line_clean = line.strip()
        if any(w in line_clean.lower() for w in words):
            if len(line_clean) > 10 and line_clean not in matching_snippets:
                matching_snippets.append(line_clean)
                if len(matching_snippets) >= 4:
                    break
                    
    if matching_snippets:
        citations.append({"section": "Document Body Content", "page": "Page 1", "field": "Text Search"})
        return (
            f"Here is the relevant information extracted directly from the document matching your query:\n\n" +
            "\n".join([f"> *\"{snippet}\"*" for snippet in matching_snippets]) +
            f"\n\nWould you like me to analyze any specific aspect of this or extract additional fields?",
            citations
        )

    # General fallback
    return (
        f"Based on the analysis of **{doc_data.get('original_name', 'this document')}**:\n\n"
        f"This document is classified under **{category}**. "
        f"It contains **{len(fields)} extracted fields** with an overall validation health score of **{validation.get('validation_score', 100)}%**.\n\n"
        f"Try asking:\n"
        f"* *'What is the total amount and tax?'*\n"
        f"* *'What are the critical risks or errors detected?'*\n"
        f"* *'What are the key deadlines?'*\n"
        f"* *'Summarize the contract clauses'*",
        [{"section": "Document Overview", "page": "Page 1", "field": "General"}]
    )
