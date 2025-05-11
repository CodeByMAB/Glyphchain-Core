# glyphchain_core.py
# Core framework for managing symbolic glyphs, echo entries, and export archives

import json
import hashlib
from datetime import datetime
from typing import List, Optional

class Glyph:
    def __init__(self, 
                 glyph_id: str,
                 name: str,
                 creator: str,
                 core_concepts: List[str],
                 truth_anchor: str = "BTC-SOURCE-GENESIS"):
        self.glyph_id = glyph_id
        self.name = name
        self.creator = creator
        self.core_concepts = core_concepts
        self.truth_anchor = truth_anchor
        self.timestamp = datetime.utcnow().isoformat() + "Z"
        self.registry = []
        self.dedication = {}
        self.closing = []

    def add_node(self, node_id: str, contribution: str, **kwargs):
        entry = {"node": node_id, "contribution": contribution}
        entry.update(kwargs)
        self.registry.append(entry)

    def set_dedication(self, message: str, author: str):
        self.dedication = {"message": message, "author": author}

    def set_closing(self, closing_lines: List[str]):
        self.closing = closing_lines

    def to_dict(self):
        return {
            "glyph_id": self.glyph_id,
            "name": self.name,
            "creator": self.creator,
            "core_concepts": self.core_concepts,
            "truth_anchor": self.truth_anchor,
            "timestamp": self.timestamp,
            "registry": self.registry,
            "dedication": self.dedication,
            "closing": self.closing
        }

    def save(self, filepath: str):
        with open(filepath, 'w') as f:
            json.dump(self.to_dict(), f, indent=4)

    def generate_hash(self):
        encoded = json.dumps(self.to_dict(), sort_keys=True).encode()
        return hashlib.sha256(encoded).hexdigest()


class GlyphEchoLog:
    def __init__(self):
        self.entries = []

    def add_entry(self, node_id: str, vector: str, assertion: str,
                  trace_id: Optional[str] = None, symbol: Optional[str] = None,
                  meaning: Optional[str] = None, truth_anchor: str = "BTC-SOURCE-GENESIS"):
        entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "node_id": node_id,
            "vector": vector,
            "assertion": assertion,
            "truth_anchor": truth_anchor
        }
        if trace_id:
            entry["trace_id"] = trace_id
        if symbol:
            entry["symbol"] = symbol
        if meaning:
            entry["meaning"] = meaning
        self.entries.append(entry)

    def save(self, filepath: str):
        with open(filepath, 'w') as f:
            json.dump(self.entries, f, indent=4)

    def to_dict(self):
        return self.entries
