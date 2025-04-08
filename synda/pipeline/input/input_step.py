from typing import List, Dict, Any, Optional
from sqlmodel import Session

from synda.model.run import Run
from synda.model.step import Step
from synda.pipeline.async_executor import AsyncExecutor
from synda.model.node import Node
from synda.progress_manager import ProgressManager
from synda.pipeline.input.input_loader import InputLoader


class InputStep(AsyncExecutor):
    """Step for loading input data from various sources."""
    
    def __init__(self, session: Session, run: Run, step_model: Step):
        super().__init__(session, run, step_model)
        self.progress = ProgressManager("INPUT")
        self.input_type = self.config.parameters.type
        
    async def execute_async(
        self, 
        pending_nodes: List[Node], 
        processed_nodes: List[Node],
        batch_size: Optional[int] = None
    ) -> List[Node]:
        """Execute the input step asynchronously."""
        with self.progress.task("Loading input data...") as advance:
            # Create the appropriate input loader based on the type
            input_loader = self._get_input_loader()
            
            # Load the data
            nodes = input_loader.load(self.session)
            
            advance()
            
        return nodes
    
    def _get_input_loader(self) -> InputLoader:
        """Get the appropriate input loader based on the input type."""
        from synda.pipeline.input.csv_input_loader import CSVInputLoader
        from synda.pipeline.input.xls_input_loader import XLSInputLoader
        
        input_type = self.input_type.lower()
        
        if input_type == "csv":
            return CSVInputLoader(self.config.parameters)
        elif input_type == "xls" or input_type == "xlsx":
            return XLSInputLoader(self.config.parameters)
        else:
            raise ValueError(f"Unsupported input type: {input_type}")
    
    def execute(self, pending_nodes: List[Node], processed_nodes: List[Node]) -> List[Node]:
        """Synchronous wrapper for backward compatibility."""
        import asyncio
        return asyncio.run(self.execute_async(pending_nodes, processed_nodes))