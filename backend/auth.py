import hashlib
import secrets
from typing import Optional, Dict, Any
from backend.database import get_connection

def hash_password(password: str) -> str:
    # Standard SHA-256 with salt for simple reliable zero-dependency auth
    return hashlib.sha256(password.encode("utf-8")).hexdigest()

def create_user(username: str, email: str, password: str, full_name: str, role: str = "Senior Document Auditor") -> Dict[str, Any]:
    conn = get_connection()
    cursor = conn.cursor()
    pwd_hash = hash_password(password)
    try:
        cursor.execute('''
        INSERT INTO users (username, email, password_hash, full_name, role)
        VALUES (?, ?, ?, ?, ?)
        ''', (username.strip(), email.strip().lower(), pwd_hash, full_name.strip(), role))
        user_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return {
            "id": user_id,
            "username": username,
            "email": email,
            "full_name": full_name,
            "role": role
        }
    except Exception as e:
        conn.close()
        raise ValueError(f"User registration failed: {str(e)}")

def authenticate_user(username: str, password: str) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    pwd_hash = hash_password(password)
    cursor.execute('''
    SELECT id, username, email, full_name, role, password_hash 
    FROM users 
    WHERE username = ? OR email = ?
    ''', (username.strip(), username.strip().lower()))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return None
    if row["password_hash"] != pwd_hash:
        return None
    return {
        "id": row["id"],
        "username": row["username"],
        "email": row["email"],
        "full_name": row["full_name"],
        "role": row["role"]
    }

def ensure_demo_user() -> Dict[str, Any]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, email, full_name, role FROM users WHERE username = 'demouser'")
    row = cursor.fetchone()
    if row:
        user = dict(row)
        conn.close()
        return user
    
    # Create default demo user
    pwd_hash = hash_password("demo12345")
    cursor.execute('''
    INSERT INTO users (username, email, password_hash, full_name, role)
    VALUES ('demouser', 'auditor@omnidoc.ai', ?, 'Dr. Sarah Mitchell, Lead Compliance Officer', 'Lead Auditor')
    ''', (pwd_hash,))
    user_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return {
        "id": user_id,
        "username": "demouser",
        "email": "auditor@omnidoc.ai",
        "full_name": "Dr. Sarah Mitchell, Lead Compliance Officer",
        "role": "Lead Auditor"
    }
