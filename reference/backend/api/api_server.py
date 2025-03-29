#!/usr/bin/env python3
import os
import json
import datetime
from typing import List, Dict, Optional, Union, Any

# FastAPI imports
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Import core components
from backend.core.database import Database
from backend.core.filter import ProcessFilter
from backend.core.categorizer import ProcessCategorizer

# Create FastAPI instance
app = FastAPI(title="PC Time Tracker API", description="API for PC Time Tracking application")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development - restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
db = Database()
process_filter = ProcessFilter()
categorizer = ProcessCategorizer()

# Routes
@app.get("/")
def read_root():
    return {"message": "PC Time Tracker API is running"}

@app.get("/processes")
def get_processes(
    limit: int = 100,
    days: int = 1,
    category: Optional[str] = None,
    include_idle: bool = False
):
    """
    Get processes tracked in the last N days
    """
    try:
        end_date = datetime.datetime.now()
        start_date = end_date - datetime.timedelta(days=days)

        result = db.get_processes(
            start_date=start_date,
            end_date=end_date,
            limit=limit,
            include_idle=include_idle
        )

        # Apply category filter if specified
        if category:
            result = [p for p in result if categorizer.categorize_process(p["name"]) == category]

        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/processes/summary")
def get_process_summary(
    days: int = 1,
    include_idle: bool = False
):
    """
    Get summary of process usage by category
    """
    try:
        end_date = datetime.datetime.now()
        start_date = end_date - datetime.timedelta(days=days)

        # Get summary from categorizer
        summary = categorizer.get_category_summary(
            start_date=start_date,
            end_date=end_date,
            include_idle=include_idle
        )

        return summary
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/resources")
def get_resources(
    days: int = 1,
    interval: str = "hour"  # hour, day, or raw
):
    """
    Get system resource usage for the specified period
    """
    try:
        end_date = datetime.datetime.now()
        start_date = end_date - datetime.timedelta(days=days)

        resources = db.get_resources(
            start_date=start_date,
            end_date=end_date,
            interval=interval
        )

        return resources
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/idle")
def get_idle_time(days: int = 1):
    """
    Get idle time records for the specified period
    """
    try:
        end_date = datetime.datetime.now()
        start_date = end_date - datetime.timedelta(days=days)

        idle_times = db.get_idle_times(
            start_date=start_date,
            end_date=end_date
        )

        return idle_times
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/categories")
def get_categories():
    """
    Get all process categories
    """
    try:
        return categorizer.categories
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/categories/{category}/process/{process}")
def add_process_to_category(category: str, process: str):
    """
    Add a process to a category
    """
    try:
        categorizer.add_process_to_category(category, process)
        categorizer.save_categories()
        return {"message": f"Added {process} to {category} category"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/categories/{category}/process/{process}")
def remove_process_from_category(category: str, process: str):
    """
    Remove a process from a category
    """
    try:
        categorizer.remove_process_from_category(category, process)
        categorizer.save_categories()
        return {"message": f"Removed {process} from {category} category"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/filters")
def get_filters():
    """
    Get all process filters
    """
    try:
        return {
            "excluded": process_filter.excluded_processes,
            "patterns": process_filter.regex_patterns,
            "priorities": process_filter.process_priorities,
            "thresholds": process_filter.resource_thresholds
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/filters/exclude/{process}")
def exclude_process(process: str):
    """
    Add a process to the excluded list
    """
    try:
        process_filter.exclude_process(process)
        process_filter.save_settings()
        return {"message": f"Excluded {process}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/filters/exclude/{process}")
def include_process(process: str):
    """
    Remove a process from the excluded list
    """
    try:
        process_filter.include_process(process)
        process_filter.save_settings()
        return {"message": f"Included {process}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/export")
def export_data(
    days: int = 7,
    format: str = "json"  # json or csv
):
    """
    Export all data for the specified period
    """
    try:
        end_date = datetime.datetime.now()
        start_date = end_date - datetime.timedelta(days=days)

        # Get data
        processes = db.get_processes(start_date=start_date, end_date=end_date, limit=10000)
        resources = db.get_resources(start_date=start_date, end_date=end_date)
        idle_times = db.get_idle_times(start_date=start_date, end_date=end_date)

        data = {
            "processes": processes,
            "resources": resources,
            "idle_times": idle_times,
            "export_date": str(datetime.datetime.now()),
            "period": {
                "start": str(start_date),
                "end": str(end_date),
                "days": days
            }
        }

        if format.lower() == "json":
            return data
        elif format.lower() == "csv":
            # Return error for now - CSV export would be implemented separately
            raise HTTPException(status_code=501, detail="CSV export not implemented yet")
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported format: {format}")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def start_api_server(host: str = "127.0.0.1", port: int = 8000):
    """
    Start the API server
    """
    uvicorn.run(app, host=host, port=port)

if __name__ == "__main__":
    start_api_server()