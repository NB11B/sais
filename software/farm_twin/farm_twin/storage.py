import sqlite3
import json

class GraphStorage:
    def __init__(self, db_path=":memory:"):
        self.conn = sqlite3.connect(db_path)
        self._init_db()

    def _init_db(self):
        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS nodes (
                id TEXT PRIMARY KEY, 
                type TEXT, 
                payload_json TEXT
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS edges (
                id TEXT PRIMARY KEY, 
                source_id TEXT, 
                type TEXT, 
                target_id TEXT, 
                payload_json TEXT
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS observations (
                id TEXT PRIMARY KEY, 
                timestamp TEXT, 
                farm_id TEXT, 
                field_id TEXT, 
                zone_id TEXT, 
                measurement_id TEXT, 
                payload_json TEXT
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS cards (
                id TEXT PRIMARY KEY, 
                created_at TEXT, 
                card_type TEXT, 
                status TEXT, 
                payload_json TEXT
            )
        ''')
        self.conn.commit()

    def add_node(self, node_id: str, node_type: str, payload: dict):
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT OR REPLACE INTO nodes (id, type, payload_json) VALUES (?, ?, ?)",
            (node_id, node_type, json.dumps(payload))
        )
        self.conn.commit()

    def add_edge(self, edge_id: str, source_id: str, edge_type: str, target_id: str, payload: dict = None):
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT OR REPLACE INTO edges (id, source_id, type, target_id, payload_json) VALUES (?, ?, ?, ?, ?)",
            (edge_id, source_id, edge_type, target_id, json.dumps(payload or {}))
        )
        self.conn.commit()

    def add_observation(self, obs_id: str, timestamp: str, farm_id: str, field_id: str, zone_id: str, measurement_id: str, payload: dict):
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT OR REPLACE INTO observations (id, timestamp, farm_id, field_id, zone_id, measurement_id, payload_json) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (obs_id, timestamp, farm_id, field_id, zone_id, measurement_id, json.dumps(payload))
        )
        self.conn.commit()

    def add_card(self, card_id: str, created_at: str, card_type: str, status: str, payload: dict):
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT OR REPLACE INTO cards (id, created_at, card_type, status, payload_json) VALUES (?, ?, ?, ?, ?)",
            (card_id, created_at, card_type, status, json.dumps(payload))
        )
        self.conn.commit()
        
    def get_node(self, node_id: str):
        cursor = self.conn.cursor()
        cursor.execute("SELECT type, payload_json FROM nodes WHERE id = ?", (node_id,))
        row = cursor.fetchone()
        if row:
            return {"type": row[0], "payload": json.loads(row[1])}
        return None

    def get_edges(self, source_id: str = None, target_id: str = None, edge_type: str = None):
        cursor = self.conn.cursor()
        query = "SELECT id, source_id, type, target_id, payload_json FROM edges WHERE 1=1"
        params = []
        if source_id:
            query += " AND source_id = ?"
            params.append(source_id)
        if target_id:
            query += " AND target_id = ?"
            params.append(target_id)
        if edge_type:
            query += " AND type = ?"
            params.append(edge_type)
            
        cursor.execute(query, params)
        return [
            {"id": r[0], "source_id": r[1], "type": r[2], "target_id": r[3], "payload": json.loads(r[4])}
            for r in cursor.fetchall()
        ]
