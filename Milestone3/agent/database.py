"""
Database management for NovaQA
"""
import sqlite3
import os
from datetime import datetime
import json

class Database:
    def __init__(self, db_path="novaqa.db"):
        self.db_path = db_path
        self.init_db()
    
    def init_db(self):
        """Initialize database tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                email TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Test reports table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                report_id TEXT UNIQUE NOT NULL,
                user_id INTEGER,
                instruction TEXT NOT NULL,
                total_steps INTEGER,
                passed_steps INTEGER,
                failed_steps INTEGER,
                success_rate REAL,
                status TEXT,
                execution_data TEXT,
                generated_code TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        
        conn.commit()
        conn.close()
        print("[Database] Initialized successfully")
    
    def create_user(self, username, password, email=None):
        """Create new user"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO users (username, password, email) VALUES (?, ?, ?)",
                (username, password, email)
            )
            conn.commit()
            user_id = cursor.lastrowid
            print(f"[Database] Created user: {username} (ID: {user_id})")
            return user_id
        except sqlite3.IntegrityError:
            print(f"[Database] User already exists: {username}")
            return None
        finally:
            conn.close()
    
    def verify_user(self, username, password):
        """Verify user credentials"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, username FROM users WHERE username=? AND password=?",
            (username, password)
        )
        user = cursor.fetchone()
        conn.close()
        
        if user:
            print(f"[Database] User verified: {username}")
            return {"id": user[0], "username": user[1]}
        else:
            print(f"[Database] Invalid credentials for: {username}")
            return None
    
    def save_report(self, report_data, user_id=None):
        """Save test report"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        report_id = f"RPT-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        execution = report_data.get("execution", [])
        total = len(execution)
        passed = len([s for s in execution if s.get("status") == "Passed"])
        failed = total - passed
        rate = (passed / total * 100) if total > 0 else 0
        status = "PASSED" if failed == 0 else "FAILED"
        
        cursor.execute('''
            INSERT INTO reports 
            (report_id, user_id, instruction, total_steps, passed_steps, 
             failed_steps, success_rate, status, execution_data, generated_code)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            report_id,
            user_id,
            report_data.get("instruction", ""),
            total,
            passed,
            failed,
            rate,
            status,
            json.dumps(execution),
            report_data.get("generated_code", "")
        ))
        
        conn.commit()
        conn.close()
        
        print(f"[Database] Saved report: {report_id} (User: {user_id or 'Guest'})")
        return report_id
    
    def get_reports(self, user_id=None, limit=50):
        """Get reports (all for guests, user-specific for logged-in)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if user_id:
            cursor.execute('''
                SELECT report_id, instruction, total_steps, passed_steps, 
                       failed_steps, success_rate, status, created_at
                FROM reports 
                WHERE user_id = ?
                ORDER BY created_at DESC
                LIMIT ?
            ''', (user_id, limit))
        else:
            # For guests, show recent public reports
            cursor.execute('''
                SELECT report_id, instruction, total_steps, passed_steps, 
                       failed_steps, success_rate, status, created_at
                FROM reports 
                WHERE user_id IS NULL
                ORDER BY created_at DESC
                LIMIT ?
            ''', (limit,))
        
        reports = []
        for row in cursor.fetchall():
            reports.append({
                "report_id": row[0],
                "instruction": row[1],
                "total_steps": row[2],
                "passed_steps": row[3],
                "failed_steps": row[4],
                "success_rate": row[5],
                "status": row[6],
                "created_at": row[7]
            })
        
        conn.close()
        print(f"[Database] Retrieved {len(reports)} reports (User: {user_id or 'Guest'})")
        return reports
    
    def get_report_detail(self, report_id):
        """Get full report details"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT report_id, instruction, total_steps, passed_steps, 
                   failed_steps, success_rate, status, execution_data, 
                   generated_code, created_at
            FROM reports 
            WHERE report_id = ?
        ''', (report_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            print(f"[Database] Retrieved report details: {report_id}")
            return {
                "report_id": row[0],
                "instruction": row[1],
                "total_steps": row[2],
                "passed_steps": row[3],
                "failed_steps": row[4],
                "success_rate": row[5],
                "status": row[6],
                "execution": json.loads(row[7]) if row[7] else [],
                "generated_code": row[8],
                "created_at": row[9]
            }
        else:
            print(f"[Database] Report not found: {report_id}")
            return None
    
    def delete_report(self, report_id, user_id=None):
        """Delete a report"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            if user_id:
                # For logged-in users, verify ownership
                cursor.execute(
                    "DELETE FROM reports WHERE report_id = ? AND user_id = ?",
                    (report_id, user_id)
                )
            else:
                # For guests, can delete any guest report
                cursor.execute(
                    "DELETE FROM reports WHERE report_id = ? AND user_id IS NULL",
                    (report_id,)
                )
            
            conn.commit()
            deleted = cursor.rowcount > 0
            
            if deleted:
                print(f"[Database] Deleted report: {report_id}")
            else:
                print(f"[Database] Report not found or access denied: {report_id}")
            
            return deleted
        except Exception as e:
            print(f"[ERROR] Delete failed: {e}")
            return False
        finally:
            conn.close()
    
    def clear_guest_reports(self):
        """Clear all guest reports (called when session ends)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("DELETE FROM reports WHERE user_id IS NULL")
            deleted_count = cursor.rowcount
            conn.commit()
            print(f"[Database] Cleared {deleted_count} guest reports")
        except Exception as e:
            print(f"[ERROR] Clear guest reports failed: {e}")
        finally:
            conn.close()