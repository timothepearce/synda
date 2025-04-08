import os
import ray
from typing import List, Dict, Any, Optional, Callable, TypeVar, Generic

from synda.model.node import Node

T = TypeVar('T')


class RayExecutor:
    """Utility class for distributed execution using Ray."""
    
    _initialized = False
    
    @classmethod
    def initialize(cls, num_cpus: Optional[int] = None, num_gpus: Optional[int] = None):
        """Initialize Ray if not already initialized."""
        if not cls._initialized:
            ray.init(
                num_cpus=num_cpus,
                num_gpus=num_gpus,
                ignore_reinit_error=True
            )
            cls._initialized = True
    
    @classmethod
    def shutdown(cls):
        """Shutdown Ray."""
        if cls._initialized:
            ray.shutdown()
            cls._initialized = False
    
    @staticmethod
    def is_ray_enabled() -> bool:
        """Check if Ray is enabled via environment variable."""
        return os.environ.get("SYNDA_ENABLE_RAY", "false").lower() == "true"
    
    @staticmethod
    def get_num_cpus() -> int:
        """Get the number of CPUs to use for Ray."""
        try:
            return int(os.environ.get("SYNDA_RAY_NUM_CPUS", "0"))
        except ValueError:
            return 0
    
    @staticmethod
    def get_num_gpus() -> int:
        """Get the number of GPUs to use for Ray."""
        try:
            return int(os.environ.get("SYNDA_RAY_NUM_GPUS", "0"))
        except ValueError:
            return 0
    
    @classmethod
    def map(cls, func: Callable[[T], Any], items: List[T], batch_size: int = 10) -> List[Any]:
        """
        Apply a function to each item in parallel using Ray.
        
        Args:
            func: The function to apply to each item
            items: The list of items to process
            batch_size: The number of items to process in each batch
            
        Returns:
            A list of results from applying the function to each item
        """
        if not cls.is_ray_enabled() or len(items) == 0:
            # Fall back to regular map if Ray is not enabled
            return list(map(func, items))
        
        # Initialize Ray if needed
        cls.initialize(
            num_cpus=cls.get_num_cpus() or None,
            num_gpus=cls.get_num_gpus() or None
        )
        
        # Define a remote function
        @ray.remote
        def remote_func(item):
            return func(item)
        
        # Process in batches to avoid overwhelming the scheduler
        results = []
        for i in range(0, len(items), batch_size):
            batch = items[i:i+batch_size]
            # Submit tasks
            refs = [remote_func.remote(item) for item in batch]
            # Get results
            batch_results = ray.get(refs)
            results.extend(batch_results)
        
        return results
    
    @classmethod
    def process_nodes(
        cls, 
        process_func: Callable[[Node], Node], 
        nodes: List[Node], 
        batch_size: int = 10
    ) -> List[Node]:
        """
        Process a list of nodes in parallel using Ray.
        
        Args:
            process_func: The function to apply to each node
            nodes: The list of nodes to process
            batch_size: The number of nodes to process in each batch
            
        Returns:
            A list of processed nodes
        """
        if not cls.is_ray_enabled() or len(nodes) == 0:
            # Fall back to regular processing if Ray is not enabled
            return [process_func(node) for node in nodes]
        
        # Initialize Ray if needed
        cls.initialize(
            num_cpus=cls.get_num_cpus() or None,
            num_gpus=cls.get_num_gpus() or None
        )
        
        # Define a remote function for processing nodes
        @ray.remote
        def remote_process(node_dict):
            # Convert dict to Node
            node = Node(**node_dict)
            # Process the node
            result_node = process_func(node)
            # Convert back to dict for serialization
            return {
                "id": result_node.id,
                "parent_node_id": result_node.parent_node_id,
                "ablated": result_node.ablated,
                "value": result_node.value,
                "ancestors": result_node.ancestors,
                "status": result_node.status.value if hasattr(result_node.status, 'value') else result_node.status,
                "node_metadata": result_node.node_metadata
            }
        
        # Process in batches
        results = []
        for i in range(0, len(nodes), batch_size):
            batch = nodes[i:i+batch_size]
            # Convert nodes to dicts for serialization
            node_dicts = [
                {
                    "id": node.id,
                    "parent_node_id": node.parent_node_id,
                    "ablated": node.ablated,
                    "value": node.value,
                    "ancestors": node.ancestors,
                    "status": node.status.value if hasattr(node.status, 'value') else node.status,
                    "node_metadata": node.node_metadata
                }
                for node in batch
            ]
            # Submit tasks
            refs = [remote_process.remote(node_dict) for node_dict in node_dicts]
            # Get results
            batch_results = ray.get(refs)
            # Convert dicts back to Nodes
            result_nodes = [Node(**result_dict) for result_dict in batch_results]
            results.extend(result_nodes)
        
        return results