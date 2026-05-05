from typing import List, Optional
from dataclasses import asdict
from .storage import GraphStorage
from .models import GraphEntity

class FarmGraph:
    def __init__(self, db_path=":memory:"):
        self.storage = GraphStorage(db_path)

    def add_node(self, node: GraphEntity, commit: bool = True):
        payload = asdict(node)
        node_type = type(node).__name__
        self.storage.add_node(node.id, node_type, payload, commit=commit)

    def add_edge(self, source_id: str, edge_type: str, target_id: str, payload: dict = None, commit: bool = True):
        edge_id = f"{source_id}-{edge_type}-{target_id}"
        self.storage.add_edge(edge_id, source_id, edge_type, target_id, payload, commit=commit)
        
    def get_node(self, node_id: str) -> Optional[dict]:
        return self.storage.get_node(node_id)
        
    def get_edges(self, source_id: str = None, target_id: str = None, edge_type: str = None) -> List[dict]:
        return self.storage.get_edges(source_id, target_id, edge_type)
