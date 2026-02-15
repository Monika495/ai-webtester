"""
Diagnostic Script - Check NovaQA Database
Run this to see what's actually in your database
"""
import sqlite3
import json
from datetime import datetime

def diagnose_database():
    print("="*60)
    print("🔍 NovaQA Database Diagnostic")
    print("="*60)
    
    try:
        conn = sqlite3.connect('novaqa.db')
        cursor = conn.cursor()
        
        # Check users
        print("\n👥 USERS TABLE:")
        cursor.execute("SELECT id, username, created_at FROM users")
        users = cursor.fetchall()
        if users:
            for user in users:
                print(f"   User ID: {user[0]}, Username: {user[1]}, Created: {user[2]}")
        else:
            print("   ❌ No users found!")
        
        # Check reports
        print("\n📊 REPORTS TABLE:")
        cursor.execute("SELECT COUNT(*) FROM reports")
        total_reports = cursor.fetchone()[0]
        print(f"   Total reports in database: {total_reports}")
        
        if total_reports > 0:
            # Show all reports
            cursor.execute("""
                SELECT report_id, user_id, instruction, status, 
                       total_steps, passed_steps, created_at 
                FROM reports 
                ORDER BY created_at DESC 
                LIMIT 10
            """)
            reports = cursor.fetchall()
            
            print(f"\n   Last 10 reports:")
            for i, report in enumerate(reports, 1):
                print(f"\n   Report {i}:")
                print(f"      Report ID: {report[0]}")
                print(f"      User ID: {report[1]}")
                print(f"      Instruction: {report[2][:50]}...")
                print(f"      Status: {report[3]}")
                print(f"      Steps: {report[5]}/{report[4]}")
                print(f"      Created: {report[6]}")
            
            # Check for reports with NULL user_id (guest reports)
            cursor.execute("SELECT COUNT(*) FROM reports WHERE user_id IS NULL")
            guest_reports = cursor.fetchone()[0]
            print(f"\n   Guest reports (user_id IS NULL): {guest_reports}")
            
            # Check for reports with user_id = 1 (typical first user)
            cursor.execute("SELECT COUNT(*) FROM reports WHERE user_id = 1")
            user1_reports = cursor.fetchone()[0]
            print(f"   Reports for user_id=1: {user1_reports}")
            
            # Check for reports with user_id = 2
            cursor.execute("SELECT COUNT(*) FROM reports WHERE user_id = 2")
            user2_reports = cursor.fetchone()[0]
            print(f"   Reports for user_id=2: {user2_reports}")
            
        else:
            print("   ❌ No reports found in database!")
        
        # Check table structure
        print("\n📋 REPORTS TABLE STRUCTURE:")
        cursor.execute("PRAGMA table_info(reports)")
        columns = cursor.fetchall()
        for col in columns:
            print(f"   {col[1]} ({col[2]})")
        
        conn.close()
        
        print("\n" + "="*60)
        print("✅ Diagnostic Complete")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    diagnose_database()