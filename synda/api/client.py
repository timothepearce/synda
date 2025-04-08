import requests
from typing import Dict, Any, Optional, List
import yaml
import json


class SyndaClient:
    """Client for interacting with the Synda API."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        """Initialize the client with the API base URL."""
        self.base_url = base_url.rstrip("/")
    
    def run_pipeline(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run a pipeline with the provided configuration.
        
        Args:
            config: The pipeline configuration as a dictionary
            
        Returns:
            A dictionary with the run ID and status
        """
        # Convert the config to YAML
        config_yaml = yaml.dump(config)
        
        # Make the request
        response = requests.post(
            f"{self.base_url}/pipeline/run",
            json={"config_yaml": config_yaml}
        )
        
        # Check for errors
        response.raise_for_status()
        
        return response.json()
    
    def run_pipeline_from_file(self, config_file: str) -> Dict[str, Any]:
        """
        Run a pipeline with the configuration from a file.
        
        Args:
            config_file: Path to the configuration file
            
        Returns:
            A dictionary with the run ID and status
        """
        # Load the config from file
        with open(config_file, "r") as f:
            config_yaml = f.read()
        
        # Make the request
        response = requests.post(
            f"{self.base_url}/pipeline/run",
            json={"config_yaml": config_yaml}
        )
        
        # Check for errors
        response.raise_for_status()
        
        return response.json()
    
    def resume_pipeline(self, run_id: int) -> Dict[str, Any]:
        """
        Resume a pipeline run.
        
        Args:
            run_id: The ID of the run to resume
            
        Returns:
            A dictionary with the run ID and status
        """
        # Make the request
        response = requests.post(f"{self.base_url}/pipeline/resume/{run_id}")
        
        # Check for errors
        response.raise_for_status()
        
        return response.json()
    
    def get_pipeline_status(self, run_id: int) -> Dict[str, Any]:
        """
        Get the status of a pipeline run.
        
        Args:
            run_id: The ID of the run to check
            
        Returns:
            A dictionary with the run ID, status, and steps
        """
        # Make the request
        response = requests.get(f"{self.base_url}/pipeline/status/{run_id}")
        
        # Check for errors
        response.raise_for_status()
        
        return response.json()
    
    def cancel_pipeline(self, run_id: int) -> Dict[str, Any]:
        """
        Cancel a running pipeline.
        
        Args:
            run_id: The ID of the run to cancel
            
        Returns:
            A dictionary with the run ID and status
        """
        # Make the request
        response = requests.delete(f"{self.base_url}/pipeline/cancel/{run_id}")
        
        # Check for errors
        response.raise_for_status()
        
        return response.json()
    
    def wait_for_completion(self, run_id: int, poll_interval: int = 5) -> Dict[str, Any]:
        """
        Wait for a pipeline run to complete.
        
        Args:
            run_id: The ID of the run to wait for
            poll_interval: The interval in seconds between status checks
            
        Returns:
            The final status of the run
        """
        import time
        
        while True:
            # Get the status
            status = self.get_pipeline_status(run_id)
            
            # Check if the run is finished
            if status["status"] in ["finished", "errored", "stopped"]:
                return status
            
            # Wait before checking again
            time.sleep(poll_interval)