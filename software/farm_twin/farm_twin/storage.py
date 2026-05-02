import sqlite3
import json

class GraphStorage:
    def __init__(self, db_path=":memory:"):
        self.conn = sqlite3.connect(db_path)
        self._init_db()
        self._migrate_db()

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
                node_id TEXT,
                timestamp TEXT, 
                farm_id TEXT, 
                field_id TEXT, 
                zone_id TEXT, 
                measurement_id TEXT, 
                value REAL,
                layer TEXT,
                payload_json TEXT
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS plant_observations (
                id TEXT PRIMARY KEY,
                farm_id TEXT,
                paddock_id TEXT,
                timestamp TEXT,
                forage_mass REAL,
                cover REAL,
                height REAL,
                recovery_score INTEGER,
                payload_json TEXT
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS cards (
                id TEXT PRIMARY KEY, 
                created_at TEXT, 
                card_type TEXT, 
                status TEXT, 
                action_status TEXT DEFAULT 'pending',
                notes TEXT,
                updated_at TEXT,
                payload_json TEXT
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS grazing_events (
                id TEXT PRIMARY KEY, 
                farm_id TEXT, 
                field_id TEXT,
                paddock_id TEXT, 
                started_at TEXT, 
                ended_at TEXT, 
                animal_count INTEGER,
                notes TEXT,
                payload_json TEXT
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS livestock_observations (
                id TEXT PRIMARY KEY, 
                farm_id TEXT, 
                paddock_id TEXT, 
                timestamp TEXT, 
                bcs REAL, 
                manure_score INTEGER,
                payload_json TEXT
            )
        ''')
        self.conn.commit()

    def _migrate_db(self):
        cursor = self.conn.cursor()
        
        # 1. Check if 'layer' column exists in 'observations'
        cursor.execute("PRAGMA table_info(observations)")
        cols = {row[1] for row in cursor.fetchall()}
        
        if "layer" not in cols:
            cursor.execute("ALTER TABLE observations ADD COLUMN layer TEXT")
            self.conn.commit()
            
        if "node_id" not in cols:
            cursor.execute("ALTER TABLE observations ADD COLUMN node_id TEXT")
            self.conn.commit()

        if "value" not in cols:
            cursor.execute("ALTER TABLE observations ADD COLUMN value REAL")
            self.conn.commit()
            
            # 2. Backfill from payload_json
            cursor.execute("SELECT id, payload_json FROM observations")
            rows = cursor.fetchall()
            for row in rows:
                obs_id = row[0]
                payload = json.loads(row[1]) if row[1] else {}
                layer = payload.get("layer", "Unknown")
                node_id = payload.get("node_id")
                value = payload.get("value")
                cursor.execute("UPDATE observations SET layer = ?, node_id = ?, value = ? WHERE id = ?", 
                             (layer, node_id, value, obs_id))
            self.conn.commit()

        # 3. Check for card action columns
        cursor.execute("PRAGMA table_info(cards)")
        card_cols = {row[1] for row in cursor.fetchall()}
        if "action_status" not in card_cols:
            cursor.execute("ALTER TABLE cards ADD COLUMN action_status TEXT DEFAULT 'pending'")
            cursor.execute("ALTER TABLE cards ADD COLUMN notes TEXT")
            cursor.execute("ALTER TABLE cards ADD COLUMN updated_at TEXT")
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

    def add_observation(self, obs_id: str, node_id: str, timestamp: str, farm_id: str, field_id: str, zone_id: str, measurement_id: str, value: float, layer: str, payload: dict):
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT OR REPLACE INTO observations (id, node_id, timestamp, farm_id, field_id, zone_id, measurement_id, value, layer, payload_json) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (obs_id, node_id, timestamp, farm_id, field_id, zone_id, measurement_id, value, layer, json.dumps(payload))
        )
        self.conn.commit()

    def add_card(self, card_id: str, created_at: str, card_type: str, status: str, payload: dict):
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT OR REPLACE INTO cards (id, created_at, card_type, status, payload_json) VALUES (?, ?, ?, ?, ?)",
            (card_id, created_at, card_type, status, json.dumps(payload))
        )
        self.conn.commit()

    def add_grazing_event(self, event_id: str, farm_id: str, field_id: str, paddock_id: str, started_at: str, ended_at: str, animal_count: int, notes: str, payload: dict):
        cursor = self.conn.cursor()
        cursor.execute(
            """INSERT OR REPLACE INTO grazing_events 
               (id, farm_id, field_id, paddock_id, started_at, ended_at, animal_count, notes, payload_json) 
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (event_id, farm_id, field_id, paddock_id, started_at, ended_at, animal_count, notes, json.dumps(payload))
        )
        self.conn.commit()

    def get_latest_grazing_event(self, paddock_id: str):
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT payload_json FROM grazing_events WHERE paddock_id = ? ORDER BY started_at DESC LIMIT 1",
            (paddock_id,)
        )
        row = cursor.fetchone()
        return json.loads(row[0]) if row else None

    def add_livestock_observation(self, obs_id: str, farm_id: str, paddock_id: str, timestamp: str, bcs: float, manure_score: int, payload: dict):
        cursor = self.conn.cursor()
        cursor.execute(
            """INSERT OR REPLACE INTO livestock_observations 
               (id, farm_id, paddock_id, timestamp, bcs, manure_score, payload_json) 
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (obs_id, farm_id, paddock_id, timestamp, bcs, manure_score, json.dumps(payload))
        )
        self.conn.commit()

    def add_plant_observation(self, obs_id: str, farm_id: str, paddock_id: str, timestamp: str, forage_mass: float, cover: float, height: float, recovery_score: int, payload: dict):
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT OR REPLACE INTO plant_observations (id, farm_id, paddock_id, timestamp, forage_mass, cover, height, recovery_score, payload_json) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (obs_id, farm_id, paddock_id, timestamp, forage_mass, cover, height, recovery_score, json.dumps(payload))
        )
        self.conn.commit()

    def get_livestock_observations(self, paddock_id: str = None, limit: int = 5):
        cursor = self.conn.cursor()
        query = "SELECT payload_json FROM livestock_observations"
        params = []
        if paddock_id:
            query += " WHERE paddock_id = ?"
            params.append(paddock_id)
        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)
        
        cursor.execute(query, params)
        return [json.loads(row[0]) for row in cursor.fetchall()]

    def update_card_action(self, card_id: str, action_status: str, notes: str, updated_at: str):
        cursor = self.conn.cursor()
        cursor.execute(
            "UPDATE cards SET action_status = ?, notes = ?, updated_at = ? WHERE id = ?",
            (action_status, notes, updated_at, card_id)
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
