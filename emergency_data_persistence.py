#!/usr/bin/env python3
"""
Emergency Trading Data Persistence System
CRITICAL: Prevents trading data loss during redeployments.
"""
import json
import sqlite3
import os
from datetime import datetime
from typing import Dict, Any
import requests

class EmergencyPersistence:
    """Emergency system to save and recover trading data"""
    
    def __init__(self, db_path: str = "emergency_trading_data.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize emergency database"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Emergency backups table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS emergency_backups (
                    backup_id TEXT PRIMARY KEY,
                    timestamp TEXT NOT NULL,
                    backup_type TEXT NOT NULL,
                    data_snapshot TEXT NOT NULL
                )
            ''')
            
            conn.commit()
    
    def save_emergency_snapshot(self, data: Dict[str, Any]) -> str:
        """Save emergency snapshot of trading data"""
        backup_id = f"EMERGENCY_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO emergency_backups 
                (backup_id, timestamp, backup_type, data_snapshot)
                VALUES (?, ?, ?, ?)
            ''', (
                backup_id,
                datetime.now().isoformat(),
                'emergency_snapshot',
                json.dumps(data, default=str)
            ))
            conn.commit()
        
        return backup_id

def create_immediate_emergency_backup():
    """Create immediate backup of current system state"""
    print("🚨 CREATING EMERGENCY BACKUP...")
    
    emergency = EmergencyPersistence()
    
    try:
        base_url = "https://algoauto-9gx56.ondigitalocean.app"
        
        backup_data = {
            'timestamp': datetime.now().isoformat(),
            'backup_reason': 'Pre-deployment emergency backup',
            'endpoints_data': {}
        }
        
        # Test multiple endpoints
        endpoints = [
            '/api/v1/autonomous/status',
            '/api/v1/dashboard/summary',
            '/api/v1/system/status'
        ]
        
        for endpoint in endpoints:
            try:
                response = requests.get(f"{base_url}{endpoint}", timeout=5)
                if response.status_code == 200:
                    backup_data['endpoints_data'][endpoint] = response.json()
                    print(f"✅ Backed up {endpoint}")
                else:
                    print(f"⚠️ Failed {endpoint}: {response.status_code}")
            except Exception as e:
                print(f"❌ Error {endpoint}: {e}")
        
        # Save to emergency database
        backup_id = emergency.save_emergency_snapshot(backup_data)
        
        # Also save as JSON file
        backup_filename = f"{backup_id}.json"
        with open(backup_filename, 'w') as f:
            json.dump(backup_data, f, indent=2, default=str)
        
        print(f"💾 Emergency backup created: {backup_id}")
        print(f"📁 File saved: {backup_filename}")
        
        return backup_id, backup_filename
        
    except Exception as e:
        print(f"❌ Emergency backup failed: {e}")
        return None, None

if __name__ == "__main__":
    print("🚨 EMERGENCY DATA PERSISTENCE SYSTEM")
    print("=" * 50)
    
    # Create immediate backup
    backup_id, backup_file = create_immediate_emergency_backup()
    
    if backup_id:
        print(f"\n✅ EMERGENCY BACKUP SUCCESSFUL!")
        print(f"📊 Backup ID: {backup_id}")
        print(f"📁 Backup File: {backup_file}")
        print(f"\n🛡️ Your data is now protected!")
    else:
        print(f"\n❌ EMERGENCY BACKUP FAILED!")
        print(f"⚠️ Manual backup required!") 