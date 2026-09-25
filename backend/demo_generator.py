import os
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

from backend.database import save_document, save_document_intelligence, get_all_documents
from backend.classifier import classify_document
from backend.extractor import parse_document_file, extract_document_fields, extract_sections, extract_entities
from backend.validator import validate_document
from backend.knowledge import generate_knowledge_and_insights

DEMO_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "demo_files")
os.makedirs(DEMO_DIR, exist_ok=True)

def generate_pdf_invoice_valid(file_path: str):
    doc = SimpleDocTemplate(file_path, pagesize=letter, leftMargin=36, rightMargin=36, topMargin=36, bottomMargin=36)
    styles = getSampleStyleSheet()
    story = []
    
    title_style = ParagraphStyle('TitleStyle', parent=styles['Heading1'], fontSize=20, leading=24, textColor=colors.HexColor('#1E293B'))
    bold_style = ParagraphStyle('BoldStyle', parent=styles['Normal'], fontSize=10, leading=14, fontName='Helvetica-Bold')
    normal_style = ParagraphStyle('NormalStyle', parent=styles['Normal'], fontSize=10, leading=14, textColor=colors.HexColor('#334155'))
    
    # Header Table
    header_data = [
        [
            Paragraph("<b>ACME CLOUD LOGISTICS INC.</b><br/>450 Mission Bay Boulevard<br/>San Francisco, CA 94158<br/>contact@acmecloudlogistics.com", normal_style),
            Paragraph("<b>TAX INVOICE</b><br/><b>Invoice #:</b> INV-84920<br/><b>Invoice Date:</b> 2026-09-15<br/><b>Payment Due:</b> 2026-10-15<br/><b>Tax / EIN:</b> US-EIN-98421094", normal_style)
        ]
    ]
    t_header = Table(header_data, colWidths=[3.5*inch, 3.5*inch])
    t_header.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 12),
    ]))
    story.append(t_header)
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#6366F1'), spaceBefore=8, spaceAfter=12))
    
    # Bill To
    bill_data = [
        [
            Paragraph("<b>BILL TO:</b><br/>Nexus Global Enterprises Ltd.<br/>780 Third Avenue, Suite 2400<br/>New York, NY 10017<br/>Attn: Accounts Payable", normal_style),
            Paragraph("<b>PAYMENT DETAILS:</b><br/><b>Payment Terms:</b> Net 30 Days<br/><b>Payment Method:</b> Wire Transfer<br/><b>Bank:</b> JPMorgan Chase N.A.<br/><b>Routing:</b> 021000021", normal_style)
        ]
    ]
    t_bill = Table(bill_data, colWidths=[3.5*inch, 3.5*inch])
    t_bill.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 16),
    ]))
    story.append(t_bill)
    
    # Line items
    story.append(Paragraph("<b>SUMMARY OF CHARGES & SERVICES</b>", bold_style))
    story.append(Spacer(1, 8))
    
    items_data = [
        ["Description", "Qty", "Unit Price", "Total Amount"],
        ["Enterprise High-Performance Kubernetes Node Pool (Monthly)", "2", "$3,400.00", "$6,800.00"],
        ["Dedicated Managed Cloud Gateway & SOC 2 Security Shield", "1", "$4,150.00", "$4,150.00"],
        ["Automated Multi-Region Disaster Recovery Cold Storage (100TB)", "1", "$1,500.00", "$1,500.00"],
    ]
    t_items = Table(items_data, colWidths=[4.0*inch, 0.8*inch, 1.1*inch, 1.1*inch])
    t_items.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#F1F5F9')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.HexColor('#0F172A')),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 9),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ('TOPPADDING', (0,0), (-1,-1), 8),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')),
        ('ALIGN', (1,0), (-1,-1), 'RIGHT'),
    ]))
    story.append(t_items)
    story.append(Spacer(1, 14))
    
    # Totals
    totals_data = [
        ["", "Subtotal:", "$12,450.00"],
        ["", "Standard Applicable Tax (10%):", "$1,245.00"],
        ["", "Total Amount Due:", "$13,695.00"]
    ]
    t_totals = Table(totals_data, colWidths=[4.0*inch, 1.9*inch, 1.1*inch])
    t_totals.setStyle(TableStyle([
        ('FONTNAME', (1,2), (2,2), 'Helvetica-Bold'),
        ('FONTSIZE', (1,2), (2,2), 11),
        ('TEXTCOLOR', (1,2), (2,2), colors.HexColor('#1E1B4B')),
        ('ALIGN', (1,0), (-1,-1), 'RIGHT'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LINEABOVE', (1,2), (2,2), 1, colors.HexColor('#6366F1')),
    ]))
    story.append(t_totals)
    story.append(Spacer(1, 20))
    story.append(Paragraph("<b>Notice:</b> Thank you for your business. Remittances after due date subject to standard late interest charges.", normal_style))
    
    doc.build(story)

def generate_pdf_contract_risk(file_path: str):
    doc = SimpleDocTemplate(file_path, pagesize=letter, leftMargin=40, rightMargin=40, topMargin=40, bottomMargin=40)
    styles = getSampleStyleSheet()
    story = []
    
    title_style = ParagraphStyle('ContractTitle', parent=styles['Heading1'], fontSize=16, leading=20, alignment=1, textColor=colors.HexColor('#0F172A'))
    normal = ParagraphStyle('CBody', parent=styles['Normal'], fontSize=9.5, leading=14, textColor=colors.HexColor('#334155'))
    h2 = ParagraphStyle('CH2', parent=styles['Heading2'], fontSize=11, leading=15, textColor=colors.HexColor('#1E293B'))
    
    story.append(Paragraph("<b>MASTER CLOUD SERVICES &amp; SLA AGREEMENT</b>", title_style))
    story.append(Spacer(1, 10))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#94A3B8'), spaceBefore=4, spaceAfter=14))
    
    story.append(Paragraph("This Master Services Agreement is entered into on <b>Effective Date: 2024-06-01</b>, by and between:", normal))
    story.append(Spacer(1, 6))
    story.append(Paragraph("<b>Client:</b> NovaTech Solutions Corp, a Delaware corporation ('Client'), and<br/><b>Contractor:</b> AlphaStream Data Systems LLC ('Service Provider').", normal))
    story.append(Spacer(1, 10))
    
    story.append(Paragraph("<b>SECTION 1. TERM AND TERMINATION</b>", h2))
    story.append(Paragraph("This Agreement shall commence on the Effective Date and shall continue until <b>Expiration Date: 2025-05-31</b> ('Initial Term'). Either party may terminate with 30 days written notice.", normal))
    story.append(Spacer(1, 10))
    
    story.append(Paragraph("<b>SECTION 2. INDEMNIFICATION AND LIMITATION OF LIABILITY</b>", h2))
    story.append(Paragraph("Contractor shall defend and hold harmless Client against any claims, losses, or liabilities. Both parties agree that Contractor liability under this Agreement shall be subject to <b>Limitation of Liability: Uncapped / Unlimited Indemnification</b> without aggregate monetary cap or exclusions for indirect or consequential damages.", normal))
    story.append(Spacer(1, 10))
    
    story.append(Paragraph("<b>SECTION 3. CONFIDENTIALITY</b>", h2))
    story.append(Paragraph("Each party shall protect confidential information with reasonable care for a period of <b>Confidentiality Period: 3 Years Post-Termination</b>.", normal))
    story.append(Spacer(1, 10))
    
    story.append(Paragraph("<b>SECTION 4. DISPUTE RESOLUTION AND LAW</b>", h2))
    story.append(Paragraph("<b>Governing Law: Not Specified (High Risk)</b>. In the event of dispute, parties shall attempt informal negotiation before initiating proceedings.", normal))
    story.append(Spacer(1, 20))
    
    story.append(Paragraph("<b>IN WITNESS WHEREOF</b>, the authorized representatives have executed this Agreement.", normal))
    story.append(Spacer(1, 15))
    sig_data = [
        ["_______________________________________", "_______________________________________"],
        ["NovaTech Solutions Corp (Client)", "AlphaStream Data Systems LLC (Provider)"],
        ["Date: 2024-06-01", "Date: 2024-06-01"]
    ]
    t_sig = Table(sig_data, colWidths=[3.2*inch, 3.2*inch])
    story.append(t_sig)
    
    doc.build(story)

def generate_pdf_invoice_error(file_path: str):
    # Invoice with intentional Math Discrepancy & Overdue Date
    doc = SimpleDocTemplate(file_path, pagesize=letter, leftMargin=36, rightMargin=36, topMargin=36, bottomMargin=36)
    styles = getSampleStyleSheet()
    story = []
    
    bold_style = ParagraphStyle('BoldStyle', parent=styles['Normal'], fontSize=10, leading=14, fontName='Helvetica-Bold')
    normal_style = ParagraphStyle('NormalStyle', parent=styles['Normal'], fontSize=10, leading=14, textColor=colors.HexColor('#334155'))
    
    header_data = [
        [
            Paragraph("<b>APEX GLOBAL SUPPLIERS LTD.</b><br/>Industrial Zone Sector 9<br/>Chicago, IL 60607<br/>billing@apexsuppliers.com", normal_style),
            Paragraph("<b>COMMERCIAL INVOICE</b><br/><b>Invoice #:</b> INV-20411<br/><b>Invoice Date:</b> 2026-08-01<br/><b>Payment Due:</b> 2026-08-20<br/><b>Tax ID:</b> US-EIN-7729104", normal_style)
        ]
    ]
    t_header = Table(header_data, colWidths=[3.5*inch, 3.5*inch])
    story.append(t_header)
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#EF4444'), spaceBefore=8, spaceAfter=12))
    
    bill_data = [
        [
            Paragraph("<b>BILL TO:</b><br/>Horizon Global Manufacturing Inc.<br/>Industrial Highway 4<br/>Detroit, MI 48201", normal_style),
            Paragraph("<b>PAYMENT TERMS:</b><br/>Terms: Net 15 Days<br/>Bank: Citibank NA<br/>Account #: 8839-4412-9901", normal_style)
        ]
    ]
    story.append(Table(bill_data, colWidths=[3.5*inch, 3.5*inch]))
    story.append(Spacer(1, 10))
    
    items_data = [
        ["Item Description", "Qty", "Rate", "Total"],
        ["Precision Industrial Pneumatic Valves (Model PX-90)", "10", "$500.00", "$5,000.00"],
        ["Heavy-Duty Hydraulic Seal Replacement Kits", "7", "$500.00", "$3,500.00"],
    ]
    t_items = Table(items_data, colWidths=[3.8*inch, 0.8*inch, 1.2*inch, 1.2*inch])
    t_items.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#FEE2E2')),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#F87171')),
        ('ALIGN', (1,0), (-1,-1), 'RIGHT'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(t_items)
    story.append(Spacer(1, 12))
    
    # Deliberate Discrepancy: Subtotal 8500, Tax 850 = 9350, but stated Grand Total is 10,250.00
    totals_data = [
        ["", "Subtotal:", "$8,500.00"],
        ["", "Sales Tax (10%):", "$850.00"],
        ["", "Grand Total Due:", "$10,250.00"]  # Intentionally Mismatched for demo!
    ]
    t_totals = Table(totals_data, colWidths=[4.0*inch, 1.8*inch, 1.2*inch])
    t_totals.setStyle(TableStyle([
        ('FONTNAME', (1,2), (2,2), 'Helvetica-Bold'),
        ('TEXTCOLOR', (1,2), (2,2), colors.HexColor('#991B1B')),
        ('ALIGN', (1,0), (-1,-1), 'RIGHT'),
        ('LINEABOVE', (1,2), (2,2), 1, colors.HexColor('#EF4444')),
    ]))
    story.append(t_totals)
    story.append(Spacer(1, 20))
    story.append(Paragraph("<b>Notice:</b> Payment overdue. Immediate settlement required.", normal_style))
    
    doc.build(story)

def generate_pdf_safety_audit(file_path: str):
    doc = SimpleDocTemplate(file_path, pagesize=letter, leftMargin=36, rightMargin=36, topMargin=36, bottomMargin=36)
    styles = getSampleStyleSheet()
    story = []
    
    title_style = ParagraphStyle('AuditTitle', parent=styles['Heading1'], fontSize=16, leading=20, alignment=1, textColor=colors.HexColor('#0F172A'))
    normal = ParagraphStyle('ABody', parent=styles['Normal'], fontSize=9.5, leading=14, textColor=colors.HexColor('#334155'))
    
    story.append(Paragraph("<b>COMPLIANCE &amp; SAFETY AUDIT REPORT</b>", title_style))
    story.append(Paragraph("Regulatory Environmental &amp; OSHA Facility Standards", ParagraphStyle('Sub', parent=styles['Normal'], fontSize=10, alignment=1, textColor=colors.HexColor('#64748B'))))
    story.append(Spacer(1, 8))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#D97706'), spaceBefore=4, spaceAfter=12))
    
    meta_data = [
        [
            Paragraph("<b>Audit ID:</b> AUD-2026-9812<br/><b>Facility:</b> Apex BioMed Production Lab 4<br/><b>Lead Inspector:</b> Marcus Vance, CSP, Lead Auditor", normal),
            Paragraph("<b>Audit Date:</b> 2026-09-18<br/><b>Compliance Score:</b> 74.5%<br/><b>Status:</b> ACTION REQUIRED<br/><b>Remediation Deadline:</b> 2026-10-05", normal)
        ]
    ]
    story.append(Table(meta_data, colWidths=[3.5*inch, 3.5*inch]))
    story.append(Spacer(1, 14))
    
    findings_data = [
        ["Audit Category", "Inspection Standard", "Result", "Severity"],
        ["HVAC HEPA Filtration & Air Flow", "ISO 14644-1 Cleanroom Cl. 7", "FAILED - Differential Pressure Out of Spec", "CRITICAL"],
        ["Emergency Eye Wash & Shower Units", "OSHA 1910.151(c) Safety Station", "PASSED - Inspected & Tagged", "NONE"],
        ["Hazardous Chemical Secondary Containment", "EPA 40 CFR 264.175 Standard", "ACTION REQUIRED - Berm Seal Deterioration", "MODERATE"],
        ["Electrical Arc Flash Signage", "NFPA 70E Electrical Workplace", "PASSED - All Panels Verified", "NONE"]
    ]
    t_find = Table(findings_data, colWidths=[2.2*inch, 2.3*inch, 1.8*inch, 0.7*inch])
    t_find.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#FEF3C7')),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 8.5),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#F59E0B')),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('TOPPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(t_find)
    story.append(Spacer(1, 15))
    
    story.append(Paragraph("<b>MANDATORY CORRECTIVE ACTION NOTICE:</b><br/>Facility failed cleanroom environmental containment threshold. Facility management must complete recalibration of primary HVAC differential sensors and repair hazardous chemical containment berms by 2026-10-05.", normal))
    
    doc.build(story)

def generate_pdf_identity_kyc(file_path: str):
    doc = SimpleDocTemplate(file_path, pagesize=letter, leftMargin=40, rightMargin=40, topMargin=40, bottomMargin=40)
    styles = getSampleStyleSheet()
    story = []
    
    title_style = ParagraphStyle('IDTitle', parent=styles['Heading1'], fontSize=16, leading=20, alignment=1, textColor=colors.HexColor('#0F172A'))
    normal = ParagraphStyle('IDBody', parent=styles['Normal'], fontSize=10, leading=15, textColor=colors.HexColor('#334155'))
    
    story.append(Paragraph("<b>GLOBAL IDENTITY &amp; KYC VERIFICATION CERTIFICATE</b>", title_style))
    story.append(Spacer(1, 6))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#8B5CF6'), spaceBefore=4, spaceAfter=14))
    
    id_data = [
        [
            Paragraph("<b>OFFICIAL IDENTITY RECORD</b><br/><br/><b>Full Name:</b> Elena Rostova<br/><b>Document Type:</b> International Passport<br/><b>Passport No:</b> P9842109X<br/><b>Nationality:</b> United States of America", normal),
            Paragraph("<b>RECORD VALIDATION DETAILS</b><br/><br/><b>Date of Birth:</b> 1991-04-18<br/><b>Sex / Gender:</b> Female<br/><b>Issue Date:</b> 2016-10-10<br/><b>Expiry Date:</b> 2026-10-10", normal)
        ]
    ]
    t_id = Table(id_data, colWidths=[3.4*inch, 3.4*inch])
    t_id.setStyle(TableStyle([
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#DDD6FE')),
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F5F3FF')),
        ('PADDING', (0,0), (-1,-1), 12),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
    ]))
    story.append(t_id)
    story.append(Spacer(1, 16))
    
    story.append(Paragraph("<b>MACHINE READABLE ZONE (MRZ) VERIFICATION:</b>", ParagraphStyle('MBold', fontName='Helvetica-Bold', fontSize=9)))
    story.append(Spacer(1, 4))
    story.append(Paragraph("<font face='Courier' size=9>P&lt;USAROSTOVA&lt;&lt;ELENA&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;<br/>P9842109X8USA9104184F2610103&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;8</font>", normal))
    story.append(Spacer(1, 14))
    story.append(Paragraph("<b>Compliance Note:</b> ICAO Doc 9303 checksum confirmed valid. Alert: Passport expiration occurs within 30 days of audit.", normal))
    
    doc.build(story)

def seed_demo_data():
    """
    Creates the 5 realistic PDF files and processes them directly into the database.
    """
    existing_docs = get_all_documents()
    if len(existing_docs) >= 5:
        return
        
    demo_files_config = [
        {
            "filename": "Acme_Logistics_Invoice_INV-84920.pdf",
            "func": generate_pdf_invoice_valid,
            "category": "Commercial Invoice",
            "name": "Acme Logistics - Standard Valid Cloud Invoice"
        },
        {
            "filename": "NovaTech_Master_Services_Contract.pdf",
            "func": generate_pdf_contract_risk,
            "category": "Legal Contract",
            "name": "NovaTech MSA - High Risk Uncapped Liability Contract"
        },
        {
            "filename": "Apex_Global_Supplier_Invoice_INV-20411.pdf",
            "func": generate_pdf_invoice_error,
            "category": "Commercial Invoice",
            "name": "Apex Global - Invoice with Math Error & Overdue Date"
        },
        {
            "filename": "Apex_BioMed_Facility_Safety_Audit.pdf",
            "func": generate_pdf_safety_audit,
            "category": "Compliance Audit",
            "name": "Apex BioMed - Facility Safety Audit (Action Required)"
        },
        {
            "filename": "Global_Executive_Identity_KYC_Verification.pdf",
            "func": generate_pdf_identity_kyc,
            "category": "Identity Verification",
            "name": "Elena Rostova - Passport KYC (Expiring Soon Alert)"
        }
    ]
    
    for cfg in demo_files_config:
        f_path = os.path.join(DEMO_DIR, cfg["filename"])
        # Generate the PDF
        cfg["func"](f_path)
        
        # Parse file text and layout
        raw_text, pages_data, page_count = parse_document_file(f_path)
        f_size = os.path.getsize(f_path)
        
        # Run Classification
        best_cat, cat_conf, _ = classify_document(raw_text, cfg["filename"])
        
        # Extract Fields & Line Items
        fields, line_items = extract_document_fields(best_cat, raw_text, pages_data)
        
        # Extract Sections & Entities
        sections = extract_sections(raw_text)
        entities = extract_entities(raw_text)
        
        # Run Validation
        validation = validate_document(best_cat, fields, line_items)
        
        # Run Knowledge Discovery & Insights
        insights = generate_knowledge_and_insights(best_cat, fields, validation, entities)
        
        # Save to DB
        doc_id = save_document(
            user_id=1,
            filename=cfg["filename"],
            original_name=cfg["name"],
            file_path=f_path,
            file_size=f_size,
            mime_type="application/pdf",
            category=best_cat,
            category_confidence=cat_conf,
            validation_status=validation.get("status", "valid"),
            page_count=page_count
        )
        
        save_document_intelligence(
            document_id=doc_id,
            raw_text=raw_text,
            sections=sections,
            fields=fields,
            line_items=line_items,
            validation=validation,
            insights=insights,
            entities=entities
        )
        print(f"Seeded demo document #{doc_id}: {cfg['name']} ({validation.get('status')})")

if __name__ == "__main__":
    from backend.database import init_db
    from backend.auth import ensure_demo_user
    init_db()
    ensure_demo_user()
    seed_demo_data()
    print("Demo data generation complete!")
