from typing import List, Dict, Any, Optional
from sqlmodel import Session

from synda.model.run import Run
from synda.model.step import Step
from synda.pipeline.async_executor import AsyncExecutor
from synda.model.node import Node
from synda.progress_manager import ProgressManager
from synda.pipeline.output.output_saver import OutputSaver


class OutputStep(AsyncExecutor):
    """Step for saving output data to various destinations."""
    
    def __init__(self, session: Session, run: Run, step_model: Step):
        super().__init__(session, run, step_model)
        self.progress = ProgressManager("OUTPUT")
        self.output_type = self.config.parameters.type
        
    async def execute_async(
        self, 
        pending_nodes: List[Node], 
        processed_nodes: List[Node],
        batch_size: Optional[int] = None
    ) -> List[Node]:
        """Execute the output step asynchronously."""
        with self.progress.task("Saving output data...") as advance:
            # Create the appropriate output saver based on the type
            output_saver = self._get_output_saver()
            
            # Save the data
            output_saver.save(pending_nodes)
            
            advance()
            
        return pending_nodes
    
    def _get_output_saver(self) -> OutputSaver:
        """Get the appropriate output saver based on the output type."""
        from synda.pipeline.output.csv_output_saver import CSVOutputSaver
        from synda.pipeline.output.xls_output_saver import XLSOutputSaver
        
        output_type = self.output_type.lower()
        
        if output_type == "csv":
            return CSVOutputSaver(self.config.parameters)
        elif output_type == "xls" or output_type == "xlsx":
            return XLSOutputSaver(self.config.parameters)
        else:
            raise ValueError(f"Unsupported output type: {output_type}")
    
    def execute(self, pending_nodes: List[Node], processed_nodes: List[Node]) -> List[Node]:
        """Synchronous wrapper for backward compatibility."""
        import asyncio
        return asyncio.run(self.execute_async(pending_nodes, processed_nodes))