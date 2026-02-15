"""Database management for NovaQA - ENHANCED VERSION with Result Page Analysis"""
import sqlite3
import os
import json
import time
import traceback
from datetime import datetime

class Database:
    def __init__(self, db_path="novaqa.db"):
        self.db_path = db_path
        self.init_db()
    
    def init_db(self):
        """Initialize database with correct schema"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                email TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create reports table - CORRECTED VERSION with result_page_analysis
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS reports (
                report_id TEXT PRIMARY KEY,
                user_id INTEGER,
                instruction TEXT NOT NULL,
                total_steps INTEGER DEFAULT 0,
                passed_steps INTEGER DEFAULT 0,
                failed_steps INTEGER DEFAULT 0,
                warning_steps INTEGER DEFAULT 0,
                info_steps INTEGER DEFAULT 0,
                success_rate REAL DEFAULT 0,
                status TEXT DEFAULT 'PENDING',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                metadata TEXT,
                execution_data TEXT,
                generated_code TEXT,
                data_usage TEXT,
                result_page_analysis TEXT,
                final_screenshot_data TEXT,
                used_random_data INTEGER DEFAULT 0,
                was_random_data_used INTEGER DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        ''')
        
        # Create indexes - CORRECTED without session_id index
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_reports_user_id ON reports(user_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_reports_created_at ON reports(created_at)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_reports_status ON reports(status)')
        
        conn.commit()
        conn.close()
        print(f"[Database] Initialized at {self.db_path}")
    
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
        """Save test report - ENHANCED VERSION with result page analysis"""
        
        # DEBUG: Add print statements to trace what's happening
        print(f"\n[DEBUG DATABASE] 1. Entering save_report function")
        print(f"[DEBUG DATABASE] 2. Received user_id: {user_id}")
        print(f"[DEBUG DATABASE] 3. Received report_data keys: {list(report_data.keys())}")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get or generate report_id
        report_id = report_data.get('report_id', f"RPT-{datetime.now().strftime('%Y%m%d%H%M%S')}")
        
        print(f"[DEBUG DATABASE] 4. Using report_id: {report_id}")
        
        # Extract execution data
        execution = report_data.get("execution", [])
        total = report_data.get("total_steps", len(execution))
        passed = report_data.get("passed_steps", len([s for s in execution if s.get("status", "").lower() == "passed"]))
        failed = report_data.get("failed_steps", len([s for s in execution if s.get("status", "").lower() == "failed"]))
        warning = report_data.get("warning_steps", len([s for s in execution if s.get("status", "").lower() == "warning"]))
        info = report_data.get("info_steps", len([s for s in execution if s.get("status", "").lower() == "info"]))
        
        rate = report_data.get("success_rate", 0)
        status = report_data.get("status", "PASSED" if failed == 0 else "FAILED")
        
        print(f"[DEBUG DATABASE] 5. Report stats - Total: {total}, Passed: {passed}, Failed: {failed}, Status: {status}")
        
        # Get random data usage
        used_random_data = report_data.get("used_random_data", False)
        was_random_data_used = report_data.get("was_random_data_used", False)
        
        # Prepare data for storage
        metadata = json.dumps(report_data.get("metadata", {}), ensure_ascii=False)
        data_usage = json.dumps(report_data.get("data_usage", {}), ensure_ascii=False)
        
        # Enhanced result page analysis with content
        result_page_analysis = report_data.get("result_page_analysis", {})
        
        # If result_page_analysis is not present, try to extract from execution steps
        if not result_page_analysis and execution:
            # Look for result_page_capture step
            for step in execution:
                if step.get("action") == "result_page_capture":
                    if step.get("page_analysis"):
                        result_page_analysis = step.get("page_analysis")
                    elif step.get("result_content"):
                        result_page_analysis = {
                            "content": step.get("result_content"),
                            "summary": step.get("result_summary", "Result page captured")
                        }
                    elif step.get("result_summary"):
                        result_page_analysis = {
                            "summary": step.get("result_summary")
                        }
                    break
                
                # Also check validate_page steps with result_content
                if step.get("action") == "validate_page" and step.get("result_content"):
                    result_page_analysis = {
                        "content": step.get("result_content"),
                        "summary": step.get("details", "Validation completed")
                    }
                    break
        
        # Also check metadata for result_summary
        if not result_page_analysis and report_data.get("metadata", {}).get("result_summary"):
            result_page_analysis = {
                "summary": report_data.get("metadata", {}).get("result_summary")
            }
        
        # If we still don't have result_page_analysis, create a basic one
        if not result_page_analysis:
            # Try to extract from the last step
            if execution and len(execution) > 0:
                last_step = execution[-1]
                if last_step.get("details"):
                    result_page_analysis = {
                        "summary": last_step.get("details", "Execution completed"),
                        "content": last_step.get("result_content") if last_step.get("result_content") else last_step.get("details")
                    }
                else:
                    result_page_analysis = {"summary": "Test execution completed"}
            else:
                result_page_analysis = {"summary": "No execution data available"}
        
        if result_page_analysis:
            print(f"[DEBUG DATABASE] Found result_page_analysis with keys: {list(result_page_analysis.keys()) if isinstance(result_page_analysis, dict) else 'not a dict'}")
        
        result_page_analysis_json = json.dumps(result_page_analysis, ensure_ascii=False)
        
        final_screenshot_data = json.dumps(report_data.get("final_screenshot_data", {}), ensure_ascii=False)
        
        print(f"[DEBUG DATABASE] 6. Preparing to save to database...")
        
        try:
            cursor.execute('''
                INSERT OR REPLACE INTO reports 
                (report_id, user_id, instruction, total_steps, passed_steps, 
                 failed_steps, warning_steps, info_steps, success_rate, status, 
                 execution_data, metadata, generated_code, data_usage,
                 result_page_analysis, final_screenshot_data, used_random_data, was_random_data_used)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                report_id,
                user_id,
                report_data.get("instruction", ""),
                total,
                passed,
                failed,
                warning,
                info,
                rate,
                status,
                json.dumps(execution, ensure_ascii=False),
                metadata,
                report_data.get("generated_code", ""),
                data_usage,
                result_page_analysis_json,
                final_screenshot_data,
                1 if used_random_data else 0,
                1 if was_random_data_used else 0
            ))
            
            conn.commit()
            print(f"✅ [Database] Saved report: {report_id} (User: {user_id or 'Guest'})")
            print(f"[DEBUG DATABASE] 7. Database save successful for report_id: {report_id}")
            
            # Verify the save by retrieving
            cursor.execute("SELECT result_page_analysis FROM reports WHERE report_id = ?", (report_id,))
            saved = cursor.fetchone()
            if saved and saved[0]:
                print(f"[DEBUG DATABASE] Verified: result_page_analysis saved with length {len(saved[0])}")
                # Print preview of saved content
                try:
                    preview = json.loads(saved[0])
                    if isinstance(preview, dict):
                        if preview.get("summary"):
                            print(f"[DEBUG DATABASE] Summary preview: {preview['summary'][:100]}...")
                        elif preview.get("content"):
                            print(f"[DEBUG DATABASE] Content preview: {preview['content'][:100]}...")
                except:
                    pass
            
            return report_id
            
        except Exception as e:
            print(f"❌ [Database] Error saving report: {e}")
            print(f"[DEBUG DATABASE] 8. Database save FAILED with error: {str(e)}")
            traceback.print_exc()
            return None
        finally:
            conn.close()
            print(f"[DEBUG DATABASE] 9. Database connection closed")
    
    def get_reports(self, user_id=None, limit=100):
        """Get reports - FIXED to show ALL reports with proper JSON parsing"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row  # This allows column access by name
            cursor = conn.cursor()
            
            if user_id:
                # Get reports for specific user
                cursor.execute('''
                    SELECT report_id, instruction, total_steps, passed_steps, 
                           failed_steps, warning_steps, info_steps, success_rate, 
                           status, metadata, data_usage, result_page_analysis,
                           final_screenshot_data, created_at, execution_data,
                           generated_code, used_random_data, was_random_data_used
                    FROM reports 
                    WHERE user_id = ?
                    ORDER BY created_at DESC
                    LIMIT ?
                ''', (user_id, limit))
            else:
                # For guests, show recent reports (including those without user_id)
                cursor.execute('''
                    SELECT report_id, instruction, total_steps, passed_steps, 
                           failed_steps, warning_steps, info_steps, success_rate, 
                           status, metadata, data_usage, result_page_analysis,
                           final_screenshot_data, created_at, execution_data,
                           generated_code, used_random_data, was_random_data_used
                    FROM reports 
                    WHERE user_id IS NULL OR user_id = ''
                    ORDER BY created_at DESC
                    LIMIT ?
                ''', (limit,))
            
            reports = []
            rows = cursor.fetchall()
            
            for row in rows:
                report = dict(row)
                
                # Ensure all required fields exist
                if 'report_id' not in report or not report['report_id']:
                    report['report_id'] = f"UNKNOWN_{int(time.time())}"
                
                if 'instruction' not in report:
                    report['instruction'] = "No instruction provided"
                
                if 'status' not in report:
                    report['status'] = 'UNKNOWN'
                
                if 'total_steps' not in report:
                    report['total_steps'] = 0
                
                if 'passed_steps' not in report:
                    report['passed_steps'] = 0
                
                if 'failed_steps' not in report:
                    report['failed_steps'] = 0
                
                if 'warning_steps' not in report:
                    report['warning_steps'] = 0
                
                if 'info_steps' not in report:
                    report['info_steps'] = 0
                
                # Calculate success rate if not present
                if 'success_rate' not in report or report['success_rate'] is None:
                    if report['total_steps'] > 0:
                        report['success_rate'] = round(
                            (report['passed_steps'] / report['total_steps']) * 100, 
                            2
                        )
                    else:
                        report['success_rate'] = 0
                
                # Parse JSON fields safely
                json_fields = {
                    'metadata': {},
                    'data_usage': {},
                    'result_page_analysis': {},
                    'final_screenshot_data': {},
                    'execution_data': []
                }
                
                for field, default_value in json_fields.items():
                    if field in report and report[field]:
                        try:
                            if isinstance(report[field], str):
                                parsed = json.loads(report[field])
                                report[field] = parsed
                            elif isinstance(report[field], dict):
                                # Already a dict, keep as is
                                pass
                            else:
                                report[field] = default_value
                        except (json.JSONDecodeError, TypeError) as e:
                            print(f"[Database] Failed to parse {field} for report {report['report_id']}: {e}")
                            report[field] = default_value
                    else:
                        report[field] = default_value
                
                # Ensure execution field exists (for compatibility)
                if 'execution' not in report:
                    if 'execution_data' in report and report['execution_data']:
                        report['execution'] = report['execution_data']
                    else:
                        report['execution'] = []
                
                # Format created_at if missing or not in correct format
                if 'created_at' not in report or not report['created_at']:
                    report['created_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                elif isinstance(report['created_at'], str):
                    # Ensure it's in a readable format
                    try:
                        # If it's already a formatted string, keep it
                        datetime.strptime(report['created_at'], "%Y-%m-%d %H:%M:%S")
                    except ValueError:
                        # Try to parse and reformat
                        try:
                            dt = datetime.fromisoformat(report['created_at'].replace('Z', '+00:00'))
                            report['created_at'] = dt.strftime("%Y-%m-%d %H:%M:%S")
                        except:
                            report['created_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                # Convert boolean fields from SQLite integer to Python boolean
                if 'used_random_data' in report:
                    report['used_random_data'] = bool(report['used_random_data'])
                if 'was_random_data_used' in report:
                    report['was_random_data_used'] = bool(report['was_random_data_used'])
                
                reports.append(report)
            
            conn.close()
            print(f"[Database] Retrieved {len(reports)} reports for user_id: {user_id}")
            return reports
            
        except Exception as e:
            print(f"[Database] Error in get_reports: {e}")
            traceback.print_exc()
            return []
    
    def get_report_detail(self, report_id):
        """Get full report details with complete data"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM reports WHERE report_id = ?
            ''', (report_id,))
            
            row = cursor.fetchone()
            conn.close()
            
            if not row:
                print(f"[Database] Report not found: {report_id}")
                return None
            
            report = dict(row)
            
            # Ensure all required fields exist
            required_fields = [
                'report_id', 'instruction', 'total_steps', 'passed_steps',
                'failed_steps', 'warning_steps', 'info_steps', 'success_rate',
                'status', 'created_at'
            ]
            
            for field in required_fields:
                if field not in report:
                    if field == 'report_id':
                        report[field] = report_id
                    elif field == 'instruction':
                        report[field] = "No instruction provided"
                    elif field in ['total_steps', 'passed_steps', 'failed_steps', 
                                  'warning_steps', 'info_steps']:
                        report[field] = 0
                    elif field == 'success_rate':
                        report[field] = 0
                    elif field == 'status':
                        report[field] = 'UNKNOWN'
                    elif field == 'created_at':
                        report['created_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Parse all JSON fields with proper error handling
            json_fields = {
                'execution_data': [],
                'metadata': {},
                'data_usage': {},
                'result_page_analysis': {},
                'final_screenshot_data': {}
            }
            
            for field, default_value in json_fields.items():
                if field in report and report[field]:
                    try:
                        if isinstance(report[field], str):
                            parsed = json.loads(report[field])
                            report[field] = parsed
                        elif isinstance(report[field], (dict, list)):
                            # Already parsed, keep as is
                            pass
                        else:
                            report[field] = default_value
                    except (json.JSONDecodeError, TypeError) as e:
                        print(f"[Database] Failed to parse {field} for report {report_id}: {e}")
                        report[field] = default_value
                else:
                    report[field] = default_value
            
            # Ensure execution field exists (for frontend compatibility)
            if 'execution' not in report or not report['execution']:
                if 'execution_data' in report and report['execution_data']:
                    report['execution'] = report['execution_data']
                else:
                    report['execution'] = []
            
            # Ensure metadata has required structure
            if 'metadata' not in report or not report['metadata']:
                report['metadata'] = {}
            
            # Add screenshots if they exist in metadata
            if 'metadata' in report and isinstance(report['metadata'], dict):
                if 'screenshots' not in report['metadata']:
                    report['metadata']['screenshots'] = []
                if 'final_screenshot' not in report['metadata']:
                    report['metadata']['final_screenshot'] = None
            
            # Format result_page_analysis for display
            if 'result_page_analysis' in report and report['result_page_analysis']:
                # Ensure it has a summary field for display
                if isinstance(report['result_page_analysis'], dict):
                    if 'summary' not in report['result_page_analysis']:
                        if 'content' in report['result_page_analysis']:
                            content = report['result_page_analysis']['content']
                            if content:
                                report['result_page_analysis']['summary'] = content[:300] + "..." if len(content) > 300 else content
                        else:
                            report['result_page_analysis']['summary'] = "Result page captured"
                elif isinstance(report['result_page_analysis'], str):
                    # Convert string to dict
                    report['result_page_analysis'] = {
                        'summary': report['result_page_analysis'][:300] + "..." if len(report['result_page_analysis']) > 300 else report['result_page_analysis'],
                        'content': report['result_page_analysis']
                    }
            
            # Format created_at to readable format
            if 'created_at' in report and report['created_at']:
                try:
                    if isinstance(report['created_at'], str):
                        # Try to parse and format
                        try:
                            dt = datetime.fromisoformat(report['created_at'].replace('Z', '+00:00'))
                            report['created_at'] = dt.strftime("%Y-%m-%d %H:%M:%S")
                        except:
                            # If already formatted, keep it
                            pass
                except:
                    report['created_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Convert boolean fields
            if 'used_random_data' in report:
                report['used_random_data'] = bool(report['used_random_data'])
            if 'was_random_data_used' in report:
                report['was_random_data_used'] = bool(report['was_random_data_used'])
            
            print(f"[Database] Retrieved detailed report: {report_id}")
            
            # Print preview of result_page_analysis if available
            if report.get('result_page_analysis'):
                analysis = report['result_page_analysis']
                if isinstance(analysis, dict):
                    if analysis.get('summary'):
                        print(f"[Database] Result summary: {analysis['summary'][:100]}...")
                    elif analysis.get('content'):
                        print(f"[Database] Result content: {analysis['content'][:100]}...")
            
            return report
            
        except Exception as e:
            print(f"[Database] Error in get_report_detail for {report_id}: {e}")
            traceback.print_exc()
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
            print(f"[Database] Delete failed: {e}")
            return False
        finally:
            conn.close()
    
    def clear_user_reports(self, user_id):
        """Clear all reports for a specific user"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("DELETE FROM reports WHERE user_id = ?", (user_id,))
            deleted_count = cursor.rowcount
            conn.commit()
            print(f"[Database] Cleared {deleted_count} reports for user {user_id}")
            return deleted_count
        except Exception as e:
            print(f"[Database] Clear user reports failed: {e}")
            return 0
        finally:
            conn.close()
    
    def clear_guest_reports(self):
        """Clear all guest reports"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("DELETE FROM reports WHERE user_id IS NULL")
            deleted_count = cursor.rowcount
            conn.commit()
            print(f"[Database] Cleared {deleted_count} guest reports")
            return deleted_count
        except Exception as e:
            print(f"[Database] Clear guest reports failed: {e}")
            return 0
        finally:
            conn.close()
    
    def commit(self):
        """Commit any pending transactions"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"[Database] Commit failed: {e}")
            return False