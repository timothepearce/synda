import os
import json
import hashlib
from typing import Any, Optional, List, Dict, Union
from pathlib import Path
from diskcache import Cache

from synda.model.node import Node


class StepCache:
    """Cache system for step outputs to enable faster pipeline execution and resuming."""
    
    _instance = None
    _cache = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(StepCache, cls).__new__(cls)
            cache_dir = os.environ.get("SYNDA_CACHE_DIR", str(Path.home() / ".synda" / "cache"))
            cls._cache = Cache(cache_dir)
        return cls._instance
    
    @staticmethod
    def _generate_key(step_id: int, config_hash: str, input_hash: str) -> str:
        """Generate a unique cache key based on step ID, config, and input data."""
        key_components = f"{step_id}:{config_hash}:{input_hash}"
        return hashlib.md5(key_components.encode()).hexdigest()
    
    @staticmethod
    def _hash_config(config: Dict[str, Any]) -> str:
        """Generate a hash for the step configuration."""
        config_str = json.dumps(config, sort_keys=True)
        return hashlib.md5(config_str.encode()).hexdigest()
    
    @staticmethod
    def _hash_inputs(nodes: List[Node]) -> str:
        """Generate a hash for the input nodes."""
        # Sort by ID to ensure consistent hashing
        sorted_nodes = sorted(nodes, key=lambda x: x.id if x.id is not None else 0)
        node_data = [{"id": n.id, "value": n.value, "ablated": n.ablated} for n in sorted_nodes]
        node_str = json.dumps(node_data, sort_keys=True)
        return hashlib.md5(node_str.encode()).hexdigest()
    
    def get(self, step_id: int, config: Dict[str, Any], input_nodes: List[Node]) -> Optional[List[Dict[str, Any]]]:
        """Retrieve cached output nodes for a step if available."""
        if not self._is_caching_enabled():
            return None
            
        config_hash = self._hash_config(config)
        input_hash = self._hash_inputs(input_nodes)
        cache_key = self._generate_key(step_id, config_hash, input_hash)
        
        return self._cache.get(cache_key)
    
    def set(self, step_id: int, config: Dict[str, Any], input_nodes: List[Node], output_nodes: List[Node]) -> None:
        """Cache the output nodes for a step."""
        if not self._is_caching_enabled():
            return
            
        config_hash = self._hash_config(config)
        input_hash = self._hash_inputs(input_nodes)
        cache_key = self._generate_key(step_id, config_hash, input_hash)
        
        # Convert nodes to serializable format
        serialized_nodes = []
        for node in output_nodes:
            serialized_nodes.append({
                "parent_node_id": node.parent_node_id,
                "ablated": node.ablated,
                "value": node.value,
                "ancestors": node.ancestors,
                "node_metadata": node.node_metadata
            })
        
        self._cache.set(cache_key, serialized_nodes)
    
    def clear(self) -> None:
        """Clear the entire cache."""
        self._cache.clear()
    
    def clear_for_step(self, step_id: int) -> None:
        """Clear cache entries for a specific step."""
        # This is a bit inefficient but diskcache doesn't support pattern matching
        keys_to_delete = []
        for key in self._cache:
            if key.startswith(f"{step_id}:"):
                keys_to_delete.append(key)
        
        for key in keys_to_delete:
            del self._cache[key]
    
    def _is_caching_enabled(self) -> bool:
        """Check if caching is enabled via environment variable."""
        return os.environ.get("SYNDA_ENABLE_CACHE", "true").lower() == "true"