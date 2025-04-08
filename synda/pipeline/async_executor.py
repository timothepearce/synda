import asyncio
from abc import abstractmethod
from typing import List, Dict, Any, Optional

from sqlmodel import Session

from synda.model.run import Run
from synda.model.step import Step, StepStatus
from synda.model.node import Node
from synda.utils.cache import StepCache


class AsyncExecutor:
    """Base class for asynchronous step executors."""
    
    def __init__(
        self,
        session: Session,
        run: Run,
        step_model: Step,
        save_on_completion: bool = True,
        use_cache: bool = True,
    ):
        self.session = session
        self.run = run
        self.step_model = step_model
        self.config = step_model.get_step_config()
        self.save_on_completion = save_on_completion
        self.use_cache = use_cache
        self.cache = StepCache()
    
    async def execute_and_update_step_async(
        self,
        pending_nodes: List[Node],
        processed_nodes: List[Node],
        restarted_step: bool = False,
        batch_size: Optional[int] = None,
    ) -> List[Node]:
        """Execute the step asynchronously and update its status."""
        try:
            self.step_model.set_running(
                self.session, pending_nodes, restarted=restarted_step
            )
            
            # Check cache first if enabled
            if self.use_cache and not restarted_step:
                cached_result = self.cache.get(
                    self.step_model.id, 
                    self.config.model_dump(), 
                    pending_nodes
                )
                
                if cached_result:
                    # Convert cached data back to Node objects
                    output_nodes = []
                    for node_data in cached_result:
                        node = Node(
                            parent_node_id=node_data["parent_node_id"],
                            ablated=node_data["ablated"],
                            value=node_data["value"],
                            ancestors=node_data["ancestors"],
                            node_metadata=node_data["node_metadata"]
                        )
                        output_nodes.append(node)
                        
                    if self.save_on_completion:
                        self.step_model.save_at_execution_end(
                            self.session, pending_nodes, output_nodes
                        )
                    else:
                        self.step_model.set_completed(session=self.session)
                        
                    filtered_nodes = [node for node in output_nodes if not node.ablated]
                    return filtered_nodes
            
            # If not in cache or cache disabled, execute the step
            output_nodes = await self.execute_async(
                pending_nodes, processed_nodes, batch_size=batch_size
            )
            
            # Cache the result if caching is enabled
            if self.use_cache:
                self.cache.set(
                    self.step_model.id,
                    self.config.model_dump(),
                    pending_nodes,
                    output_nodes
                )
            
            if self.save_on_completion:
                self.step_model.save_at_execution_end(
                    self.session, pending_nodes, output_nodes
                )
            else:
                self.step_model.set_completed(session=self.session)
            
            filtered_nodes = [node for node in output_nodes if not node.ablated]
            return filtered_nodes
            
        except Exception as e:
            self.step_model.set_status(self.session, StepStatus.ERRORED)
            raise e
    
    @abstractmethod
    async def execute_async(
        self, 
        pending_nodes: List[Node], 
        processed_nodes: List[Node],
        batch_size: Optional[int] = None
    ) -> List[Node]:
        """Abstract method to be implemented by concrete async executors."""
        pass
    
    def execute_and_update_step(
        self,
        pending_nodes: List[Node],
        processed_nodes: List[Node],
        restarted_step: bool = False,
        batch_size: Optional[int] = None,
    ) -> List[Node]:
        """Synchronous wrapper for the async execution method."""
        return asyncio.run(
            self.execute_and_update_step_async(
                pending_nodes, processed_nodes, restarted_step, batch_size
            )
        )
    
    def execute(
        self, 
        pending_nodes: List[Node], 
        processed_nodes: List[Node],
        batch_size: Optional[int] = None
    ) -> List[Node]:
        """Synchronous wrapper for the async execute method."""
        return asyncio.run(
            self.execute_async(pending_nodes, processed_nodes, batch_size)
        )