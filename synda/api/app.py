import os
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel

from synda.config import Config
from synda.pipeline.async_pipeline import AsyncPipeline
from synda.model.run import Run, RunStatus
from synda.model.step import Step
from synda.database import init_db


# Initialize the database
init_db()

# Create FastAPI app
app = FastAPI(
    title="Synda API",
    description="API for Synda synthetic data generation",
    version="0.1.0",
)


# Models for API requests and responses
class ConfigRequest(BaseModel):
    config_yaml: str


class RunResponse(BaseModel):
    run_id: int
    status: str


class RunStatusResponse(BaseModel):
    run_id: int
    status: str
    steps: List[Dict[str, Any]]


# Background task for running pipelines
async def run_pipeline_task(config_yaml: str, run_id: Optional[int] = None):
    try:
        if run_id:
            # Resume a run
            pipeline = AsyncPipeline()
            await pipeline.resume(run_id=run_id)
        else:
            # Create a new run
            config = Config.load_config_from_string(config_yaml)
            pipeline = AsyncPipeline(config)
            await pipeline.execute()
    except Exception as e:
        print(f"Error running pipeline: {e}")


@app.post("/pipeline/run", response_model=RunResponse)
async def run_pipeline(config: ConfigRequest, background_tasks: BackgroundTasks):
    """Run a pipeline with the provided configuration."""
    try:
        # Parse the config
        config_obj = Config.load_config_from_string(config.config_yaml)
        
        # Create a pipeline
        pipeline = AsyncPipeline(config_obj)
        
        # Get the run ID
        run_id = pipeline.run.id
        
        # Run the pipeline in the background
        background_tasks.add_task(run_pipeline_task, config.config_yaml)
        
        return {"run_id": run_id, "status": RunStatus.RUNNING.value}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/pipeline/resume/{run_id}", response_model=RunResponse)
async def resume_pipeline(run_id: int, background_tasks: BackgroundTasks):
    """Resume a pipeline run."""
    try:
        # Check if the run exists
        run = Run.get_by_id(run_id)
        if not run:
            raise HTTPException(status_code=404, detail=f"Run with ID {run_id} not found")
        
        # Run the pipeline in the background
        background_tasks.add_task(run_pipeline_task, None, run_id)
        
        return {"run_id": run_id, "status": RunStatus.RUNNING.value}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/pipeline/status/{run_id}", response_model=RunStatusResponse)
async def get_pipeline_status(run_id: int):
    """Get the status of a pipeline run."""
    try:
        # Get the run
        run = Run.get_by_id(run_id)
        if not run:
            raise HTTPException(status_code=404, detail=f"Run with ID {run_id} not found")
        
        # Get the steps
        steps = Step.get_by_run_id(run_id)
        
        # Format the steps
        step_data = []
        for step in steps:
            step_data.append({
                "id": step.id,
                "name": step.name,
                "type": step.type,
                "method": step.method,
                "status": step.status.value,
                "created_at": step.created_at.isoformat() if step.created_at else None,
                "updated_at": step.updated_at.isoformat() if step.updated_at else None,
            })
        
        return {
            "run_id": run_id,
            "status": run.status.value,
            "steps": step_data
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.delete("/pipeline/cancel/{run_id}", response_model=RunResponse)
async def cancel_pipeline(run_id: int):
    """Cancel a running pipeline."""
    try:
        # Get the run
        run = Run.get_by_id(run_id)
        if not run:
            raise HTTPException(status_code=404, detail=f"Run with ID {run_id} not found")
        
        # Update the status
        run.update(None, RunStatus.STOPPED)
        
        return {"run_id": run_id, "status": RunStatus.STOPPED.value}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


def start_api(host: str = "0.0.0.0", port: int = 8000):
    """Start the API server."""
    import uvicorn
    uvicorn.run(app, host=host, port=port)