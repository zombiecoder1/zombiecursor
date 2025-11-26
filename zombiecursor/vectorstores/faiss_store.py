"""
FAISS-based vector store for memory management.
"""
import os
import pickle
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import faiss
from sentence_transformers import SentenceTransformer
from core.config import settings
from core.logging_config import log
from core.interfaces import MemoryStore


class FAISSVectorStore(MemoryStore):
    """FAISS-based vector store for semantic memory."""
    
    def __init__(self):
        self.index_path = Path(settings.vector_store_path)
        self.index_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize embedding model
        self.embedding_model = SentenceTransformer(settings.embedding_model)
        self.embedding_dim = self.embedding_model.get_sentence_embedding_dimension()
        
        # Initialize FAISS index
        self.index_file = self.index_path / "faiss.index"
        self.metadata_file = self.index_path / "metadata.pkl"
        
        self.index = None
        self.metadata = []
        
        # Load existing index if available
        self._load_index()
        
        log.info(f"FAISS Vector Store initialized with model: {settings.embedding_model}")
    
    def _load_index(self):
        """Load existing FAISS index and metadata."""
        try:
            if self.index_file.exists() and self.metadata_file.exists():
                self.index = faiss.read_index(str(self.index_file))
                
                with open(self.metadata_file, 'rb') as f:
                    self.metadata = pickle.load(f)
                
                log.info(f"Loaded existing index with {len(self.metadata)} items")
            else:
                # Create new index
                self.index = faiss.IndexFlatL2(self.embedding_dim)
                self.metadata = []
                log.info("Created new FAISS index")
                
        except Exception as e:
            log.error(f"Error loading index: {str(e)}")
            self.index = faiss.IndexFlatL2(self.embedding_dim)
            self.metadata = []
    
    def _save_index(self):
        """Save FAISS index and metadata."""
        try:
            faiss.write_index(self.index, str(self.index_file))
            
            with open(self.metadata_file, 'wb') as f:
                pickle.dump(self.metadata, f)
                
            log.debug(f"Saved index with {len(self.metadata)} items")
            
        except Exception as e:
            log.error(f"Error saving index: {str(e)}")
    
    def _create_embedding(self, text: str) -> np.ndarray:
        """Create embedding for text."""
        try:
            embedding = self.embedding_model.encode(text, convert_to_numpy=True)
            return embedding.reshape(1, -1).astype('float32')
        except Exception as e:
            log.error(f"Error creating embedding: {str(e)}")
            return np.zeros((1, self.embedding_dim), dtype='float32')
    
    async def store(self, key: str, value: Any) -> None:
        """Store a value in vector store."""
        try:
            # Convert value to text for embedding
            if isinstance(value, str):
                text = value
            else:
                text = str(value)
            
            # Create embedding
            embedding = self._create_embedding(text)
            
            # Add to index
            self.index.add(embedding)
            
            # Store metadata
            metadata_item = {
                'key': key,
                'text': text,
                'value': value,
                'timestamp': datetime.now().isoformat(),
                'embedding': embedding.flatten().tolist()
            }
            
            self.metadata.append(metadata_item)
            
            # Save index
            self._save_index()
            
            log.debug(f"Stored item with key: {key}")
            
        except Exception as e:
            log.error(f"Error storing item {key}: {str(e)}")
    
    async def retrieve(self, key: str) -> Optional[Any]:
        """Retrieve a value by key."""
        try:
            for item in self.metadata:
                if item['key'] == key:
                    return item['value']
            return None
            
        except Exception as e:
            log.error(f"Error retrieving item {key}: {str(e)}")
            return None
    
    async def search(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search for similar items."""
        try:
            if not self.metadata or self.index.ntotal == 0:
                return []
            
            # Create query embedding
            query_embedding = self._create_embedding(query)
            
            # Search in index
            k = min(limit, self.index.ntotal)
            distances, indices = self.index.search(query_embedding, k)
            
            # Collect results
            results = []
            for i, (distance, idx) in enumerate(zip(distances[0], indices[0])):
                if idx >= 0 and idx < len(self.metadata):
                    item = self.metadata[idx].copy()
                    item['similarity_score'] = float(1 / (1 + distance))  # Convert distance to similarity
                    item['distance'] = float(distance)
                    results.append(item)
            
            return results
            
        except Exception as e:
            log.error(f"Error searching for query '{query}': {str(e)}")
            return []
    
    async def semantic_search(self, query: str, threshold: float = 0.5, limit: int = 10) -> List[Dict[str, Any]]:
        """Perform semantic search with similarity threshold."""
        results = await self.search(query, limit)
        
        # Filter by threshold
        filtered_results = [
            result for result in results 
            if result['similarity_score'] >= threshold
        ]
        
        return filtered_results
    
    async def hybrid_search(self, query: str, keywords: List[str] = None, 
                          semantic_weight: float = 0.7, limit: int = 10) -> List[Dict[str, Any]]:
        """Perform hybrid search combining semantic and keyword search."""
        try:
            # Get semantic search results
            semantic_results = await self.search(query, limit)
            
            # Get keyword search results
            keyword_results = []
            if keywords:
                for item in self.metadata:
                    text_lower = item['text'].lower()
                    keyword_matches = sum(1 for keyword in keywords if keyword.lower() in text_lower)
                    if keyword_matches > 0:
                        result_item = item.copy()
                        result_item['keyword_score'] = keyword_matches / len(keywords)
                        keyword_results.append(result_item)
            
            # Combine results
            combined_results = {}
            
            # Add semantic results
            for result in semantic_results:
                key = result['key']
                combined_results[key] = result.copy()
                combined_results[key]['semantic_score'] = result['similarity_score']
                combined_results[key]['keyword_score'] = 0.0
            
            # Add keyword results
            for result in keyword_results:
                key = result['key']
                if key in combined_results:
                    combined_results[key]['keyword_score'] = result['keyword_score']
                else:
                    result['semantic_score'] = 0.0
                    result['keyword_score'] = result['keyword_score']
                    combined_results[key] = result
            
            # Calculate hybrid scores
            for result in combined_results.values():
                result['hybrid_score'] = (
                    semantic_weight * result['semantic_score'] + 
                    (1 - semantic_weight) * result['keyword_score']
                )
            
            # Sort by hybrid score
            final_results = sorted(
                combined_results.values(),
                key=lambda x: x['hybrid_score'],
                reverse=True
            )
            
            return final_results[:limit]
            
        except Exception as e:
            log.error(f"Error in hybrid search: {str(e)}")
            return []
    
    async def delete(self, key: str) -> bool:
        """Delete an item by key."""
        try:
            # Find item index
            item_index = None
            for i, item in enumerate(self.metadata):
                if item['key'] == key:
                    item_index = i
                    break
            
            if item_index is None:
                return False
            
            # Remove from metadata
            del self.metadata[item_index]
            
            # Rebuild index (FAISS doesn't support removal)
            self._rebuild_index()
            
            log.debug(f"Deleted item with key: {key}")
            return True
            
        except Exception as e:
            log.error(f"Error deleting item {key}: {str(e)}")
            return False
    
    def _rebuild_index(self):
        """Rebuild the FAISS index from metadata."""
        try:
            # Create new index
            self.index = faiss.IndexFlatL2(self.embedding_dim)
            
            # Add all embeddings
            for item in self.metadata:
                embedding = np.array(item['embedding']).reshape(1, -1).astype('float32')
                self.index.add(embedding)
            
            # Save rebuilt index
            self._save_index()
            
        except Exception as e:
            log.error(f"Error rebuilding index: {str(e)}")
    
    async def update(self, key: str, value: Any) -> bool:
        """Update an existing item."""
        try:
            # Check if item exists
            exists = False
            for item in self.metadata:
                if item['key'] == key:
                    exists = True
                    break
            
            if not exists:
                await self.store(key, value)
                return True
            
            # Delete old item and store new one
            await self.delete(key)
            await self.store(key, value)
            
            log.debug(f"Updated item with key: {key}")
            return True
            
        except Exception as e:
            log.error(f"Error updating item {key}: {str(e)}")
            return False
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get vector store statistics."""
        try:
            total_items = len(self.metadata)
            index_size = self.index.ntotal if self.index else 0
            
            # Calculate index file size
            index_file_size = 0
            if self.index_file.exists():
                index_file_size = self.index_file.stat().st_size
            
            metadata_file_size = 0
            if self.metadata_file.exists():
                metadata_file_size = self.metadata_file.stat().st_size
            
            # Get date range
            timestamps = [item['timestamp'] for item in self.metadata if item.get('timestamp')]
            oldest_item = min(timestamps) if timestamps else None
            newest_item = max(timestamps) if timestamps else None
            
            return {
                'total_items': total_items,
                'index_size': index_size,
                'embedding_dimension': self.embedding_dim,
                'model_name': settings.embedding_model,
                'index_file_size_bytes': index_file_size,
                'metadata_file_size_bytes': metadata_file_size,
                'oldest_item': oldest_item,
                'newest_item': newest_item,
                'storage_path': str(self.index_path)
            }
            
        except Exception as e:
            log.error(f"Error getting stats: {str(e)}")
            return {}
    
    async def clear(self) -> bool:
        """Clear all items from the vector store."""
        try:
            self.index = faiss.IndexFlatL2(self.embedding_dim)
            self.metadata = []
            
            # Delete files
            if self.index_file.exists():
                self.index_file.unlink()
            if self.metadata_file.exists():
                self.metadata_file.unlink()
            
            log.info("Cleared vector store")
            return True
            
        except Exception as e:
            log.error(f"Error clearing vector store: {str(e)}")
            return False
    
    async def backup(self, backup_path: str) -> bool:
        """Create a backup of the vector store."""
        try:
            backup_dir = Path(backup_path)
            backup_dir.mkdir(parents=True, exist_ok=True)
            
            # Copy index file
            if self.index_file.exists():
                import shutil
                shutil.copy2(self.index_file, backup_dir / "faiss.index")
            
            # Copy metadata file
            if self.metadata_file.exists():
                import shutil
                shutil.copy2(self.metadata_file, backup_dir / "metadata.pkl")
            
            log.info(f"Created backup at: {backup_path}")
            return True
            
        except Exception as e:
            log.error(f"Error creating backup: {str(e)}")
            return False
    
    async def restore(self, backup_path: str) -> bool:
        """Restore vector store from backup."""
        try:
            backup_dir = Path(backup_path)
            
            if not backup_dir.exists():
                return False
            
            # Copy index file
            index_backup = backup_dir / "faiss.index"
            if index_backup.exists():
                import shutil
                shutil.copy2(index_backup, self.index_file)
            
            # Copy metadata file
            metadata_backup = backup_dir / "metadata.pkl"
            if metadata_backup.exists():
                import shutil
                shutil.copy2(metadata_backup, self.metadata_file)
            
            # Reload index
            self._load_index()
            
            log.info(f"Restored from backup: {backup_path}")
            return True
            
        except Exception as e:
            log.error(f"Error restoring from backup: {str(e)}")
            return False


# Global vector store instance
vector_store = FAISSVectorStore()