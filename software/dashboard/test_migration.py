import sqlite3
import os
import json
import pytest
from farm_twin.storage import GraphStorage

def test_sqlite_migration():
    db_path = "test_migration_legacy.sqlite"
    if os.path.exists(db_path):
        os.remove(db_path)
        
    # 1. Create a legacy database without 'layer' column
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE observations (
            id TEXT PRIMARY KEY, 
            timestamp TEXT, 
            farm_id TEXT, 
            field_id TEXT, 
            zone_id TEXT, 
            measurement_id TEXT, 
            payload_json TEXT
        )
    ''')
    
    # 2. Seed with old observations
    obs1 = {
        "id": "old-1",
        "timestamp": "2026-05-01T12:00:00Z",
        "farm_id": "farm-1",
        "layer": "Weather",
        "value": 10
    }
    cursor.execute(
        "INSERT INTO observations (id, timestamp, farm_id, measurement_id, payload_json) VALUES (?, ?, ?, ?, ?)",
        ("old-1", obs1["timestamp"], "farm-1", "temp", json.dumps(obs1))
    )
    conn.commit()
    conn.close()
    
    # 3. Load with GraphStorage (should trigger migration)
    storage = GraphStorage(db_path)
    
    # 4. Verify column exists
    cursor = storage.conn.cursor()
    cursor.execute("PRAGMA table_info(observations)")
    cols = {row[1] for row in cursor.fetchall()}
    assert "layer" in cols
    
    # 5. Verify backfill
    cursor.execute("SELECT id, layer FROM observations WHERE id = 'old-1'")
    row = cursor.fetchone()
    assert row is not None
    assert row[1] == "Weather"
    
    storage.conn.close()
    os.remove(db_path)
