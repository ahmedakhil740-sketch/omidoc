import os
import shutil
import io
import csv
import json
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from pydantic import BaseModel

from backend.database import (
    init_db, get_connection, save_document, save_document_intelligence,
    get_all_documents, get_document_by_id, delete_document,
    update_document_fields, save_chat_message, get_chat_history,
    get_dashboard_metrics
)
from backend.auth import authenticate_user, create_user, ensure_demo_user
from backend.classifier import classify_document
from backend.extractor import parse_document_file, extract_document_fields, extract_sections, extract_entities
from backend.validator import validate_document
from backend.knowledge import generate_knowledge_and_insights
from backend.assistant import answer_document_query

# Directory setup
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UPLOAD_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uploads")
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(FRONTEND_DIR, exist_ok=True)

# Initialize DB on load
init_db()
ensure_demo_user()

app = FastAPI(
    title="OmniDoc AI - Intelligent Document Processing Platform",
    description="Enterprise-grade AI document understanding, classification, extraction, validation, and discovery platform",
    version="2.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request Models
class LoginRequest(BaseModel):
    username: str
    password: str

class RegisterRequest(BaseModel):
    username: str
    email: str
    password: str
    full_name: str
    role: Optional[str] = "Document Auditor"

class FieldUpdateRequest(BaseModel):
    fields: Dict[str, Any]

class ChatRequest(BaseModel):
    query: str

# ----------------- AUTH ROUTES -----------------
@app.post("/api/auth/login")
def api_login(req: LoginRequest):
    user = authenticate_user(req.username, req.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    return {"status": "success", "user": user, "token": f"token_{user['id']}_{user['username']}"}

@app.post("/api/auth/register")
def api_register(req: RegisterRequest):
    try:
        user = create_user(req.username, req.email, req.password, req.full_name, req.role)
        return {"status": "success", "user": user, "token": f"token_{user['id']}_{user['username']}"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/auth/demo-login")
def api_demo_login():
    user = ensure_demo_user()
    return {"status": "success", "user": user, "token": f"token_{user['id']}_demo"}

# ----------------- DASHBOARD & METRICS -----------------
@app.get("/api/dashboard/metrics")
def api_dashboard_metrics():
    metrics = get_dashboard_metrics()
    docs = get_all_documents()
    
    # Calculate processing times & anomaly count
    total_issues = sum(len(d.get("validation", {}).get("issues", [])) for d in docs)
    recent_activity = []
    for d in docs[:6]:
        recent_activity.append({
            "id": d["id"],
            "title": d["original_name"],
            "category": d["category"],
            "status": d["validation_status"],
            "confidence": int(d["category_confidence"] * 100),
            "timestamp": d["created_at"]
        })
        
    return {
        **metrics,
        "total_anomalies_detected": total_issues,
        "recent_documents": recent_activity
    }

@app.get("/api/dashboard/cross-document-insights")
def api_cross_document_insights():
    """
    Synthesizes portfolio-level insights across all uploaded documents.
    """
    docs = get_all_documents()
    vendors = {}
    high_risks = []
    deadlines = []
    
    for d in docs:
        fields = d.get("fields", {})
        val = d.get("validation", {})
        
        # Vendor spending
        v_name = fields.get("vendor_name", {}).get("value") or fields.get("party_two", {}).get("value")
        if v_name and v_name not in ["N/A", "None"]:
            vendors[v_name] = vendors.get(v_name, 0) + 1
            
        # High risks
        for iss in val.get("issues", []):
            if iss.get("severity") == "error":
                high_risks.append({
                    "doc_id": d["id"],
                    "doc_title": d["original_name"],
                    "issue": iss["title"],
                    "message": iss["message"]
                })
                
        # Deadlines
        for f_key in ["due_date", "expiration_date", "corrective_deadline", "expiry_date"]:
            if f_key in fields:
                deadlines.append({
                    "doc_id": d["id"],
                    "doc_title": d["original_name"],
                    "label": fields[f_key].get("label", f_key),
                    "date": fields[f_key].get("value")
                })
                
    return {
        "active_entities": [{"name": k, "frequency": v} for k, v in sorted(vendors.items(), key=lambda x: x[1], reverse=True)[:6]],
        "urgent_risk_alerts": high_risks[:5],
        "upcoming_deadlines": deadlines[:6]
    }

# ----------------- DOCUMENT MANAGEMENT -----------------
@app.get("/api/documents")
def api_get_documents(category: Optional[str] = None, status: Optional[str] = None, search: Optional[str] = None):
    docs = get_all_documents()
    filtered = []
    for d in docs:
        if category and category.lower() != "all" and d["category"].lower() != category.lower():
            continue
        if status and status.lower() != "all" and d["validation_status"].lower() != status.lower():
            continue
        if search:
            s = search.lower()
            if s not in d["original_name"].lower() and s not in d["category"].lower():
                continue
        filtered.append(d)
    return filtered

@app.get("/api/documents/{doc_id}")
def api_get_document(doc_id: int):
    doc = get_document_by_id(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc

@app.get("/api/documents/{doc_id}/file")
def api_get_document_file(doc_id: int):
    doc = get_document_by_id(doc_id)
    if not doc or not os.path.exists(doc["file_path"]):
        raise HTTPException(status_code=404, detail="Physical document file not found")
    return FileResponse(doc["file_path"], media_type=doc["mime_type"], filename=doc["filename"])

@app.post("/api/documents/upload")
async def api_upload_document(file: UploadFile = File(...)):
    # Validate extension
    allowed_exts = [".pdf", ".txt", ".png", ".jpg", ".jpeg"]
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in allowed_exts:
        raise HTTPException(status_code=400, detail=f"Unsupported format '{ext}'. Please upload PDF, TXT, PNG, or JPG.")
        
    # Save file
    safe_name = f"{os.urandom(6).hex()}_{file.filename.replace(' ', '_')}"
    file_path = os.path.join(UPLOAD_DIR, safe_name)
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    file_size = os.path.getsize(file_path)
    
    # Run full AI Processing Pipeline
    raw_text, pages_data, page_count = parse_document_file(file_path)
    if not raw_text.strip():
        raw_text = f"Scanned/Image document: {file.filename}\nVisual OCR processed."
        
    best_cat, cat_conf, _ = classify_document(raw_text, file.filename)
    fields, line_items = extract_document_fields(best_cat, raw_text, pages_data)
    sections = extract_sections(raw_text)
    entities = extract_entities(raw_text)
    validation = validate_document(best_cat, fields, line_items)
    insights = generate_knowledge_and_insights(best_cat, fields, validation, entities)
    
    doc_id = save_document(
        user_id=1,
        filename=safe_name,
        original_name=file.filename,
        file_path=file_path,
        file_size=file_size,
        mime_type=file.content_type or "application/pdf",
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
    
    return {
        "status": "success",
        "document_id": doc_id,
        "category": best_cat,
        "confidence": cat_conf,
        "validation_status": validation.get("status"),
        "fields_count": len(fields),
        "issues_count": len(validation.get("issues", []))
    }

@app.put("/api/documents/{doc_id}/fields")
def api_update_fields(doc_id: int, req: FieldUpdateRequest):
    doc = get_document_by_id(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
        
    # Re-run validation with updated field values
    category = doc["category"]
    line_items = doc.get("line_items", [])
    entities = doc.get("entities", [])
    
    new_validation = validate_document(category, req.fields, line_items)
    new_insights = generate_knowledge_and_insights(category, req.fields, new_validation, entities)
    
    update_document_fields(doc_id, req.fields, new_validation, new_insights)
    
    return {
        "status": "success",
        "validation": new_validation,
        "insights": new_insights
    }

@app.post("/api/documents/{doc_id}/reprocess")
def api_reprocess_document(doc_id: int):
    doc = get_document_by_id(doc_id)
    if not doc or not os.path.exists(doc["file_path"]):
        raise HTTPException(status_code=404, detail="Document or physical file not found")
        
    raw_text, pages_data, page_count = parse_document_file(doc["file_path"])
    best_cat, cat_conf, _ = classify_document(raw_text, doc["original_name"])
    fields, line_items = extract_document_fields(best_cat, raw_text, pages_data)
    sections = extract_sections(raw_text)
    entities = extract_entities(raw_text)
    validation = validate_document(best_cat, fields, line_items)
    insights = generate_knowledge_and_insights(best_cat, fields, validation, entities)
    
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
    
    return {"status": "success", "message": "Document reprocessed successfully"}

@app.delete("/api/documents/{doc_id}")
def api_delete_document(doc_id: int):
    doc = get_document_by_id(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    delete_document(doc_id)
    return {"status": "success", "message": "Document deleted"}

# ----------------- AI ASSISTANT CHAT -----------------
@app.post("/api/documents/{doc_id}/chat")
def api_document_chat(doc_id: int, req: ChatRequest):
    doc = get_document_by_id(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
        
    answer, citations = answer_document_query(req.query, doc)
    
    # Save conversation
    save_chat_message(doc_id, "user", req.query)
    save_chat_message(doc_id, "assistant", answer, citations)
    
    return {
        "role": "assistant",
        "message": answer,
        "citations": citations
    }

@app.get("/api/documents/{doc_id}/chat")
def api_get_chat_history(doc_id: int):
    return get_chat_history(doc_id)

# ----------------- EXPORT FUNCTIONALITY -----------------
@app.get("/api/documents/{doc_id}/export/json")
def api_export_json(doc_id: int):
    doc = get_document_by_id(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
        
    export_payload = {
        "export_metadata": {
            "platform": "OmniDoc AI Processing Engine v2.0",
            "document_id": doc["id"],
            "filename": doc["original_name"],
            "category": doc["category"],
            "validation_status": doc["validation_status"],
            "processed_at": doc["created_at"]
        },
        "extracted_fields": {k: v.get("value") for k, v in doc.get("fields", {}).items()},
        "line_items": doc.get("line_items", []),
        "validation_issues": doc.get("validation", {}).get("issues", []),
        "knowledge_insights": doc.get("insights", [])
    }
    
    json_bytes = json.dumps(export_payload, indent=2).encode('utf-8')
    return StreamingResponse(
        io.BytesIO(json_bytes),
        media_type="application/json",
        headers={"Content-Disposition": f"attachment; filename={doc['filename']}_extracted.json"}
    )

@app.get("/api/documents/{doc_id}/export/csv")
def api_export_csv(doc_id: int):
    doc = get_document_by_id(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
        
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Field Name", "Extracted Value", "AI Confidence", "Document Page"])
    
    for k, v in doc.get("fields", {}).items():
        writer.writerow([
            v.get("label", k),
            v.get("value", ""),
            f"{int(v.get('confidence', 0.9)*100)}%",
            v.get("page", 1)
        ])
        
    if doc.get("line_items"):
        writer.writerow([])
        writer.writerow(["--- LINE ITEMS ---", "", "", ""])
        writer.writerow(["Description", "Quantity", "Unit Price", "Total"])
        for item in doc["line_items"]:
            writer.writerow([
                item.get("description", ""),
                item.get("quantity", ""),
                item.get("unit_price", ""),
                item.get("total", "")
            ])
            
    csv_bytes = output.getvalue().encode('utf-8')
    return StreamingResponse(
        io.BytesIO(csv_bytes),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={doc['filename']}_audit.csv"}
    )

# Mount frontend
app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

@app.get("/")
def serve_index():
    return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))
