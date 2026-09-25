import sqlite3
import json
import os
from datetime import datetime
from typing import Dict, Any, List, Optional

DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "idp_platform.db")

def get_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    
    # Users table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        full_name TEXT NOT NULL,
        role TEXT NOT NULL DEFAULT 'Auditor',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Documents table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS documents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        filename TEXT NOT NULL,
        original_name TEXT NOT NULL,
        file_path TEXT NOT NULL,
        file_size INTEGER NOT NULL,
        mime_type TEXT NOT NULL,
        category TEXT NOT NULL,
        category_confidence REAL NOT NULL,
        processing_status TEXT NOT NULL DEFAULT 'completed',
        validation_status TEXT NOT NULL DEFAULT 'valid',
        page_count INTEGER DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
    ''')
    
    # Document Intelligence Extracted Data
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS document_intelligence (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        document_id INTEGER UNIQUE NOT NULL,
        raw_text TEXT NOT NULL,
        sections_json TEXT NOT NULL,
        fields_json TEXT NOT NULL,
        line_items_json TEXT DEFAULT '[]',
        validation_json TEXT NOT NULL,
        insights_json TEXT NOT NULL,
        entities_json TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE
    )
    ''')
    
    # Chat History
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS chat_messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        document_id INTEGER NOT NULL,
        role TEXT NOT NULL,
        message TEXT NOT NULL,
        citations_json TEXT DEFAULT '[]',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE
    )
    ''')
    
    # Activity Log
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS activity_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        action TEXT NOT NULL,
        details TEXT NOT NULL,
        document_id INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    conn.commit()
    conn.close()

# Helper queries
def save_document(user_id: int, filename: str, original_name: str, file_path: str, 
                  file_size: int, mime_type: str, category: str, category_confidence: float, 
                  validation_status: str, page_count: int = 1) -> int:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
    INSERT INTO documents (user_id, filename, original_name, file_path, file_size, mime_type, 
                           category, category_confidence, processing_status, validation_status, page_count)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'completed', ?, ?)
    ''', (user_id, filename, original_name, file_path, file_size, mime_type, 
          category, category_confidence, validation_status, page_count))
    doc_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return doc_id

def save_document_intelligence(document_id: int, raw_text: str, sections: list, 
                               fields: dict, line_items: list, validation: dict, 
                               insights: list, entities: list):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
    INSERT OR REPLACE INTO document_intelligence 
    (document_id, raw_text, sections_json, fields_json, line_items_json, validation_json, insights_json, entities_json)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        document_id,
        raw_text,
        json.dumps(sections),
        json.dumps(fields),
        json.dumps(line_items),
        json.dumps(validation),
        json.dumps(insights),
        json.dumps(entities)
    ))
    conn.commit()
    conn.close()

def update_document_fields(document_id: int, fields: dict, validation: dict, insights: list):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
    UPDATE document_intelligence 
    SET fields_json = ?, validation_json = ?, insights_json = ?
    WHERE document_id = ?
    ''', (json.dumps(fields), json.dumps(validation), json.dumps(insights), document_id))
    
    val_status = validation.get("status", "valid")
    cursor.execute('''
    UPDATE documents SET validation_status = ?, updated_at = CURRENT_TIMESTAMP
    WHERE id = ?
    ''', (val_status, document_id))
    conn.commit()
    conn.close()

def get_all_documents(user_id: Optional[int] = None) -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    query = '''
    SELECT d.*, di.fields_json, di.validation_json, di.insights_json
    FROM documents d
    LEFT JOIN document_intelligence di ON d.id = di.document_id
    '''
    params = []
    if user_id:
        query += " WHERE d.user_id = ?"
        params.append(user_id)
    query += " ORDER BY d.created_at DESC"
    
    cursor.execute(query, params)
    rows = cursor.fetchall()
    results = []
    for r in rows:
        item = dict(r)
        item["fields"] = json.loads(item["fields_json"]) if item["fields_json"] else {}
        item["validation"] = json.loads(item["validation_json"]) if item["validation_json"] else {}
        item["insights"] = json.loads(item["insights_json"]) if item["insights_json"] else []
        results.append(item)
    conn.close()
    return results

def get_document_by_id(doc_id: int) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
    SELECT d.*, di.raw_text, di.sections_json, di.fields_json, di.line_items_json, 
           di.validation_json, di.insights_json, di.entities_json
    FROM documents d
    LEFT JOIN document_intelligence di ON d.id = di.document_id
    WHERE d.id = ?
    ''', (doc_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return None
    item = dict(row)
    item["sections"] = json.loads(item["sections_json"]) if item["sections_json"] else []
    item["fields"] = json.loads(item["fields_json"]) if item["fields_json"] else {}
    item["line_items"] = json.loads(item["line_items_json"]) if item["line_items_json"] else []
    item["validation"] = json.loads(item["validation_json"]) if item["validation_json"] else {}
    item["insights"] = json.loads(item["insights_json"]) if item["insights_json"] else []
    item["entities"] = json.loads(item["entities_json"]) if item["entities_json"] else []
    conn.close()
    return item

def delete_document(doc_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT file_path FROM documents WHERE id = ?", (doc_id,))
    row = cursor.fetchone()
    if row and row["file_path"] and os.path.exists(row["file_path"]):
        try:
            os.remove(row["file_path"])
        except Exception:
            pass
    cursor.execute("DELETE FROM chat_messages WHERE document_id = ?", (doc_id,))
    cursor.execute("DELETE FROM document_intelligence WHERE document_id = ?", (doc_id,))
    cursor.execute("DELETE FROM documents WHERE id = ?", (doc_id,))
    conn.commit()
    conn.close()

def save_chat_message(doc_id: int, role: str, message: str, citations: list = None):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
    INSERT INTO chat_messages (document_id, role, message, citations_json)
    VALUES (?, ?, ?, ?)
    ''', (doc_id, role, message, json.dumps(citations or [])))
    conn.commit()
    conn.close()

def get_chat_history(doc_id: int) -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
    SELECT * FROM chat_messages WHERE document_id = ? ORDER BY created_at ASC
    ''', (doc_id,))
    rows = cursor.fetchall()
    res = []
    for r in rows:
        d = dict(r)
        d["citations"] = json.loads(d["citations_json"]) if d["citations_json"] else []
        res.append(d)
    conn.close()
    return res

def get_dashboard_metrics() -> Dict[str, Any]:
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM documents")
    total_docs = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM documents WHERE validation_status = 'valid'")
    valid_docs = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM documents WHERE validation_status IN ('warning', 'needs_review')")
    review_docs = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM documents WHERE validation_status = 'error'")
    error_docs = cursor.fetchone()[0]
    
    cursor.execute("SELECT category, COUNT(*) as count FROM documents GROUP BY category")
    categories = [{"category": row[0], "count": row[1]} for row in cursor.fetchall()]
    
    cursor.execute("SELECT AVG(category_confidence) FROM documents")
    avg_conf = cursor.fetchone()[0] or 0.95
    
    conn.close()
    return {
        "total_documents": total_docs,
        "valid_documents": valid_docs,
        "needs_review": review_docs,
        "high_risk_errors": error_docs,
        "average_confidence": round(avg_conf * 100, 1),
        "categories": categories
    }
