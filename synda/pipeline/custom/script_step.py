import os
import importlib.util
import inspect
from typing import List, Dict, Any, Optional, Callable
from sqlmodel import Session

from synda.model.run import Run
from synda.model.step import Step
from synda.pipeline.async_executor import AsyncExecutor
from synda.model.node import Node
from synda.progress_manager import ProgressManager


class ScriptStep(AsyncExecutor):
    """Step for executing custom Python scripts on nodes."""
    
    def __init__(self, session: Session, run: Run, step_model: Step):
        super().__init__(session, run, step_model)
        self.progress = ProgressManager("CUSTOM SCRIPT")
        self.script_path = self.config.parameters.script_path
        self.function_name = self.config.parameters.function_name
        self.script_params = getattr(self.config.parameters, "script_params", {})
        
    async def execute_async(
        self, 
        pending_nodes: List[Node], 
        processed_nodes: List[Node],
        batch_size: Optional[int] = None
    ) -> List[Node]:
        """Execute the custom script step asynchronously."""
        # Load the script
        script_function = self._load_script_function()
        
        result = list(processed_nodes)  # Create a copy to avoid modifying the original
        
        with self.progress.task(
            "Executing custom script...",
            len(pending_nodes) + len(processed_nodes),
            completed=len(processed_nodes),
        ) as advance:
            for node in pending_nodes:
                # Execute the script function on the node
                try:
                    # Check if the function is async
                    if inspect.iscoroutinefunction(script_function):
                        output_value = await script_function(
                            node.value, 
                            node_id=node.id,
                            parent_node_id=node.parent_node_id,
                            **self.script_params
                        )
                    else:
                        output_value = script_function(
                            node.value, 
                            node_id=node.id,
                            parent_node_id=node.parent_node_id,
                            **self.script_params
                        )
                    
                    # Create a new node with the output
                    result_node = Node(
                        parent_node_id=node.id,
                        value=output_value,
                        ancestors=node.ancestors
                    )
                    
                    # Save the node
                    self.step_model.save_during_execution(self.session, node, result_node)
                    result.append(result_node)
                    
                except Exception as e:
                    print(f"Error executing script on node {node.id}: {e}")
                    # Create a node with error information
                    error_value = f"ERROR: {str(e)}"
                    result_node = Node(
                        parent_node_id=node.id,
                        value=error_value,
                        ancestors=node.ancestors,
                        ablated=True  # Mark as ablated so it's filtered out
                    )
                    self.step_model.save_during_execution(self.session, node, result_node)
                    result.append(result_node)
                
                advance()
        
        return result
    
    def _load_script_function(self) -> Callable:
        """Load the script function from the specified path."""
        script_path = os.path.abspath(self.script_path)
        
        if not os.path.exists(script_path):
            raise FileNotFoundError(f"Script file not found: {script_path}")
        
        # Load the module
        spec = importlib.util.spec_from_file_location("custom_script", script_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # Get the function
        if not hasattr(module, self.function_name):
            raise AttributeError(f"Function '{self.function_name}' not found in script {script_path}")
        
        return getattr(module, self.function_name)
    
    def execute(self, pending_nodes: List[Node], processed_nodes: List[Node]) -> List[Node]:
        """Synchronous wrapper for backward compatibility."""
        import asyncio
        return asyncio.run(self.execute_async(pending_nodes, processed_nodes))