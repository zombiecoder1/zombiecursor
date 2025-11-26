"""
Memory management for ZombieCursor agents.
"""
import json
import hashlib
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from pathlib import Path
from core.interfaces import MemoryStore
from core.config import settings
from core.logging_config import log


class SimpleMemoryStore(MemoryStore):
    """Simple file-based memory store."""
    
    def __init__(self):
        self.memory_dir = Path(settings.vector_store_path)
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        self.memory_file = self.memory_dir / "memory.json"
        self.memory_data = self._load_memory()
    
    def _load_memory(self) -> Dict[str, Any]:
        """Load memory from file."""
        try:
            if self.memory_file.exists():
                with open(self.memory_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            log.error(f"Failed to load memory: {str(e)}")
        return {}
    
    def _save_memory(self) -> None:
        """Save memory to file."""
        try:
            with open(self.memory_file, 'w', encoding='utf-8') as f:
                json.dump(self.memory_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            log.error(f"Failed to save memory: {str(e)}")
    
    def _generate_key(self, content: str) -> str:
        """Generate a key for content."""
        return hashlib.md5(content.encode()).hexdigest()[:16]
    
    async def store(self, key: str, value: Any) -> None:
        """Store a value in memory."""
        try:
            self.memory_data[key] = {
                'value': value,
                'timestamp': datetime.now().isoformat(),
                'accessed': datetime.now().isoformat()
            }
            self._save_memory()
            log.debug(f"Stored memory entry: {key}")
        except Exception as e:
            log.error(f"Failed to store memory entry {key}: {str(e)}")
    
    async def retrieve(self, key: str) -> Optional[Any]:
        """Retrieve a value from memory."""
        try:
            if key in self.memory_data:
                entry = self.memory_data[key]
                entry['accessed'] = datetime.now().isoformat()
                self._save_memory()
                return entry['value']
        except Exception as e:
            log.error(f"Failed to retrieve memory entry {key}: {str(e)}")
        return None
    
    async def search(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search memory for relevant items."""
        try:
            results = []
            query_lower = query.lower()
            
            for key, entry in self.memory_data.items():
                value_str = str(entry['value']).lower()
                if query_lower in value_str:
                    results.append({
                        'key': key,
                        'value': entry['value'],
                        'timestamp': entry['timestamp'],
                        'accessed': entry['accessed'],
                        'relevance': self._calculate_relevance(query_lower, value_str)
                    })
            
            # Sort by relevance and limit results
            results.sort(key=lambda x: x['relevance'], reverse=True)
            return results[:limit]
            
        except Exception as e:
            log.error(f"Failed to search memory: {str(e)}")
            return []
    
    def _calculate_relevance(self, query: str, content: str) -> float:
        """Calculate relevance score for search."""
        if not query or not content:
            return 0.0
        
        query_words = query.split()
        content_words = content.split()
        
        matches = sum(1 for word in query_words if word in content_words)
        return matches / len(query_words) if query_words else 0.0
    
    async def cleanup(self, days: int = 30) -> None:
        """Clean up old memory entries."""
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            cutoff_str = cutoff_date.isoformat()
            
            keys_to_remove = []
            for key, entry in self.memory_data.items():
                if entry['timestamp'] < cutoff_str:
                    keys_to_remove.append(key)
            
            for key in keys_to_remove:
                del self.memory_data[key]
            
            if keys_to_remove:
                self._save_memory()
                log.info(f"Cleaned up {len(keys_to_remove)} old memory entries")
                
        except Exception as e:
            log.error(f"Failed to cleanup memory: {str(e)}")
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get memory statistics."""
        try:
            total_entries = len(self.memory_data)
            total_size = self.memory_file.stat().st_size if self.memory_file.exists() else 0
            
            # Calculate age statistics
            now = datetime.now()
            ages = []
            for entry in self.memory_data.values():
                timestamp = datetime.fromisoformat(entry['timestamp'])
                age = (now - timestamp).days
                ages.append(age)
            
            return {
                'total_entries': total_entries,
                'total_size_bytes': total_size,
                'average_age_days': sum(ages) / len(ages) if ages else 0,
                'oldest_entry_days': max(ages) if ages else 0,
                'newest_entry_days': min(ages) if ages else 0
            }
        except Exception as e:
            log.error(f"Failed to get memory stats: {str(e)}")
            return {}


# Global memory store instance
memory_store = SimpleMemoryStore()