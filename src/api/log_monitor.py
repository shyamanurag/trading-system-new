"""
Log Monitor API - Access DigitalOcean logs via API endpoints
"""

import logging
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, HTTPException, Query

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/logs", tags=["logs"])


@router.get("/health")
async def get_log_health():
    """
    Get system health report from logs.
    
    Returns analyzed log data with identified issues.
    """
    try:
        from monitoring.digitalocean_log_monitor import get_log_monitor
        
        monitor = get_log_monitor()
        
        if not monitor.is_configured:
            return {
                "success": False,
                "error": "Log monitor not configured",
                "help": "Set DO_API_TOKEN and DO_APP_ID environment variables",
                "timestamp": datetime.now().isoformat()
            }
        
        report = await monitor.get_health_report()
        
        return {
            "success": True,
            "data": report,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting log health: {e}")
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


@router.get("/recent")
async def get_recent_logs(
    minutes: int = Query(default=30, ge=1, le=120, description="Minutes of logs to fetch"),
    lines: int = Query(default=100, ge=10, le=500, description="Number of lines to return")
):
    """
    Fetch recent logs from DigitalOcean.
    
    Args:
        minutes: How many minutes of logs to fetch (1-120)
        lines: Number of lines to return (10-500)
    """
    try:
        from monitoring.digitalocean_log_monitor import get_log_monitor
        
        monitor = get_log_monitor()
        
        if not monitor.is_configured:
            return {
                "success": False,
                "error": "Log monitor not configured",
                "help": "Set DO_API_TOKEN and DO_APP_ID environment variables"
            }
        
        logs = await monitor.fetch_recent_logs(minutes=minutes)
        
        # Return last N lines
        recent_logs = logs[-lines:] if len(logs) > lines else logs
        
        return {
            "success": True,
            "data": {
                "total_lines": len(logs),
                "returned_lines": len(recent_logs),
                "logs": recent_logs
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error fetching recent logs: {e}")
        return {
            "success": False,
            "error": str(e)
        }


@router.get("/analyze")
async def analyze_logs(
    minutes: int = Query(default=30, ge=1, le=120, description="Minutes of logs to analyze")
):
    """
    Fetch and analyze logs for issues.
    
    Returns identified issues with suggested fixes.
    """
    try:
        from monitoring.digitalocean_log_monitor import get_log_monitor
        
        monitor = get_log_monitor()
        
        if not monitor.is_configured:
            return {
                "success": False,
                "error": "Log monitor not configured",
                "help": "Set DO_API_TOKEN and DO_APP_ID environment variables"
            }
        
        logs = await monitor.fetch_recent_logs(minutes=minutes)
        analysis = monitor.analyze_logs(logs)
        
        return {
            "success": True,
            "data": analysis,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error analyzing logs: {e}")
        return {
            "success": False,
            "error": str(e)
        }


@router.get("/search")
async def search_logs(
    pattern: str = Query(..., description="Search pattern (regex supported)"),
    minutes: int = Query(default=30, ge=1, le=120, description="Minutes of logs to search")
):
    """
    Search logs for a specific pattern.
    """
    try:
        import re
        from monitoring.digitalocean_log_monitor import get_log_monitor
        
        monitor = get_log_monitor()
        
        if not monitor.is_configured:
            return {
                "success": False,
                "error": "Log monitor not configured"
            }
        
        logs = await monitor.fetch_recent_logs(minutes=minutes)
        
        # Search for pattern
        matching_logs = []
        for line in logs:
            if re.search(pattern, line, re.IGNORECASE):
                matching_logs.append(line)
        
        return {
            "success": True,
            "data": {
                "pattern": pattern,
                "total_searched": len(logs),
                "matches_found": len(matching_logs),
                "matching_logs": matching_logs[:100]  # Limit to 100 matches
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error searching logs: {e}")
        return {
            "success": False,
            "error": str(e)
        }


@router.get("/errors")
async def get_error_logs(
    minutes: int = Query(default=60, ge=1, le=120, description="Minutes of logs to search")
):
    """
    Get only error logs from recent history.
    """
    try:
        from monitoring.digitalocean_log_monitor import get_log_monitor
        
        monitor = get_log_monitor()
        
        if not monitor.is_configured:
            return {
                "success": False,
                "error": "Log monitor not configured"
            }
        
        logs = await monitor.fetch_recent_logs(minutes=minutes)
        
        # Filter for errors
        error_patterns = [
            r"error",
            r"exception",
            r"failed",
            r"❌",
            r"🚨",
            r"traceback",
            r"critical"
        ]
        
        error_logs = []
        for line in logs:
            line_lower = line.lower()
            for pattern in error_patterns:
                if pattern in line_lower or pattern in line:
                    error_logs.append(line)
                    break
        
        return {
            "success": True,
            "data": {
                "total_searched": len(logs),
                "errors_found": len(error_logs),
                "error_logs": error_logs
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error fetching error logs: {e}")
        return {
            "success": False,
            "error": str(e)
        }


@router.post("/analyze-text")
async def analyze_pasted_logs(logs_text: str):
    """
    Analyze pasted log text (for when API token is not configured).
    
    Just POST your logs as text and get analysis.
    """
    try:
        from monitoring.digitalocean_log_monitor import DOLogMonitor
        
        monitor = DOLogMonitor()  # Don't need config for local analysis
        
        # Split text into lines
        logs = logs_text.strip().split("\n")
        
        analysis = monitor.analyze_logs(logs)
        
        return {
            "success": True,
            "data": analysis,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error analyzing pasted logs: {e}")
        return {
            "success": False,
            "error": str(e)
        }
