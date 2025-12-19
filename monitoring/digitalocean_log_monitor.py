"""
DigitalOcean Log Monitor - Fetch and analyze runtime logs automatically
No more copy-pasting logs! This fetches directly from DigitalOcean API.

Usage:
    # As a standalone script:
    python monitoring/digitalocean_log_monitor.py

    # Or import and use:
    from monitoring.digitalocean_log_monitor import DOLogMonitor
    monitor = DOLogMonitor()
    logs = await monitor.fetch_recent_logs()
    issues = monitor.analyze_logs(logs)
"""

import os
import re
import asyncio
import logging
import httpx
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class LogLevel(Enum):
    ERROR = "ERROR"
    WARNING = "WARNING"
    INFO = "INFO"
    DEBUG = "DEBUG"

@dataclass
class LogIssue:
    """Represents an identified issue in logs"""
    severity: str  # CRITICAL, HIGH, MEDIUM, LOW
    category: str  # e.g., "API_TIMEOUT", "AUTH_FAILURE", "CRASH"
    message: str
    count: int
    first_seen: str
    last_seen: str
    sample_logs: List[str]
    suggested_fix: str

class DOLogMonitor:
    """
    DigitalOcean Log Monitor
    
    Fetches logs from DigitalOcean App Platform and analyzes them for issues.
    """
    
    # Known issue patterns to detect
    ISSUE_PATTERNS = {
        "504_TIMEOUT": {
            "pattern": r"504|Gateway Timeout|timeout",
            "severity": "CRITICAL",
            "category": "API_TIMEOUT",
            "fix": "Event loop is blocked. Check strategy execution time and add yield points."
        },
        "401_AUTH": {
            "pattern": r"401|Unauthorized|Token.*invalid|authentication.*fail",
            "severity": "HIGH",
            "category": "AUTH_FAILURE",
            "fix": "Zerodha token expired. Re-authenticate via /api/v1/zerodha/daily-auth"
        },
        "ZERODHA_DISCONNECT": {
            "pattern": r"ZERODHA DISCONNECTED|Token.*expired|Incorrect.*api_key",
            "severity": "HIGH",
            "category": "BROKER_DISCONNECT",
            "fix": "Refresh Zerodha token via daily authentication flow."
        },
        "TRUEDATA_ERROR": {
            "pattern": r"User Already Connected|TrueData.*error|WebSocket.*closed",
            "severity": "MEDIUM",
            "category": "DATA_FEED",
            "fix": "Multiple instances running or connection issues. Check deployment count."
        },
        "TRADING_LOOP_DIED": {
            "pattern": r"TRADING TASK DIED|Trading loop died|WATCHDOG ALERT",
            "severity": "CRITICAL",
            "category": "CRASH",
            "fix": "Trading loop crashed. Check exception logs for root cause."
        },
        "RATE_LIMIT": {
            "pattern": r"Too many requests|Rate limit|429",
            "severity": "MEDIUM",
            "category": "RATE_LIMIT",
            "fix": "Too many API calls. Historical data cache should help."
        },
        "ORDER_FAILED": {
            "pattern": r"Order.*failed|instrument.*expired|does not exist",
            "severity": "HIGH",
            "category": "ORDER_FAILURE",
            "fix": "Check symbol mapping and exchange detection logic."
        },
        "MEMORY_ERROR": {
            "pattern": r"MemoryError|Out of memory|killed",
            "severity": "CRITICAL",
            "category": "RESOURCE",
            "fix": "App running out of memory. Consider upgrading instance or optimizing."
        },
        "DATABASE_ERROR": {
            "pattern": r"database.*error|connection.*refused|psycopg2|sqlalchemy.*error",
            "severity": "HIGH",
            "category": "DATABASE",
            "fix": "Database connection issue. Check PostgreSQL connection string."
        },
        "REDIS_ERROR": {
            "pattern": r"Redis.*error|redis.*connection|REDIS.*fail",
            "severity": "MEDIUM",
            "category": "CACHE",
            "fix": "Redis connection issue. Check Redis URL and availability."
        }
    }
    
    def __init__(
        self,
        api_token: Optional[str] = None,
        app_id: Optional[str] = None
    ):
        """
        Initialize the log monitor.
        
        Args:
            api_token: DigitalOcean API token (or set DO_API_TOKEN env var)
            app_id: DigitalOcean App ID (or set DO_APP_ID env var)
        """
        self.api_token = api_token or os.getenv("DO_API_TOKEN")
        self.app_id = app_id or os.getenv("DO_APP_ID")
        self.base_url = "https://api.digitalocean.com/v2"
        
        # Extract app ID from URL if full URL provided
        if self.app_id and "ondigitalocean.app" in self.app_id:
            # Extract from URL like algoauto-9gx56.ondigitalocean.app
            match = re.search(r'([a-z0-9-]+)\.ondigitalocean\.app', self.app_id)
            if match:
                self.app_name = match.group(1)
                logger.info(f"Extracted app name: {self.app_name}")
        
        self._client: Optional[httpx.AsyncClient] = None
        self._last_fetch_time: Optional[datetime] = None
        self._log_cache: List[str] = []
    
    @property
    def is_configured(self) -> bool:
        """Check if monitor is properly configured"""
        return bool(self.api_token and self.app_id)
    
    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client"""
        if self._client is None:
            self._client = httpx.AsyncClient(
                headers={
                    "Authorization": f"Bearer {self.api_token}",
                    "Content-Type": "application/json"
                },
                timeout=30.0
            )
        return self._client
    
    async def fetch_app_info(self) -> Dict[str, Any]:
        """Fetch app information to get app ID from name"""
        try:
            client = await self._get_client()
            response = await client.get(f"{self.base_url}/apps")
            
            if response.status_code == 200:
                data = response.json()
                apps = data.get("apps", [])
                
                # Find our app
                for app in apps:
                    app_url = app.get("live_url", "")
                    if self.app_name and self.app_name in app_url:
                        self.app_id = app.get("id")
                        logger.info(f"Found app ID: {self.app_id}")
                        return app
                
                return {"apps": apps}
            else:
                logger.error(f"Failed to fetch apps: {response.status_code} - {response.text}")
                return {"error": response.text}
                
        except Exception as e:
            logger.error(f"Error fetching app info: {e}")
            return {"error": str(e)}
    
    async def fetch_recent_logs(
        self,
        minutes: int = 30,
        component: str = "ALL",
        log_type: str = "RUN"
    ) -> List[str]:
        """
        Fetch recent logs from DigitalOcean.
        
        Args:
            minutes: How many minutes of logs to fetch (default 30)
            component: Component to filter (default ALL)
            log_type: BUILD, DEPLOY, or RUN (default RUN)
            
        Returns:
            List of log lines
        """
        if not self.is_configured:
            logger.warning("⚠️ Log monitor not configured. Set DO_API_TOKEN and DO_APP_ID")
            return ["ERROR: Log monitor not configured. Set DO_API_TOKEN and DO_APP_ID environment variables."]
        
        try:
            client = await self._get_client()
            
            # DigitalOcean logs endpoint
            # GET /v2/apps/{app_id}/logs
            url = f"{self.base_url}/apps/{self.app_id}/logs"
            params = {
                "type": log_type,
                "follow": False,
                "tail_lines": 500  # Fetch last 500 lines
            }
            
            if component != "ALL":
                params["component_name"] = component
            
            response = await client.get(url, params=params)
            
            if response.status_code == 200:
                data = response.json()
                
                # DigitalOcean returns logs in different formats
                if "live_url" in data:
                    # Streaming URL provided - need to fetch from there
                    live_url = data.get("live_url")
                    if live_url:
                        log_response = await client.get(live_url)
                        if log_response.status_code == 200:
                            logs = log_response.text.split("\n")
                            self._log_cache = logs
                            self._last_fetch_time = datetime.now()
                            return logs
                
                # Direct log content
                logs = data.get("logs", [])
                if isinstance(logs, str):
                    logs = logs.split("\n")
                
                self._log_cache = logs
                self._last_fetch_time = datetime.now()
                return logs
                
            elif response.status_code == 401:
                return ["ERROR: Invalid DO_API_TOKEN. Please check your DigitalOcean API token."]
            elif response.status_code == 404:
                return ["ERROR: App not found. Please check your DO_APP_ID."]
            else:
                logger.error(f"Failed to fetch logs: {response.status_code} - {response.text}")
                return [f"ERROR: Failed to fetch logs - {response.status_code}: {response.text}"]
                
        except Exception as e:
            logger.error(f"Error fetching logs: {e}")
            return [f"ERROR: {str(e)}"]
    
    async def fetch_deployment_logs(self, deployment_id: Optional[str] = None) -> List[str]:
        """Fetch logs for a specific deployment"""
        if not self.is_configured:
            return ["ERROR: Log monitor not configured"]
        
        try:
            client = await self._get_client()
            
            # If no deployment ID, get the latest
            if not deployment_id:
                deployments_url = f"{self.base_url}/apps/{self.app_id}/deployments"
                response = await client.get(deployments_url)
                if response.status_code == 200:
                    deployments = response.json().get("deployments", [])
                    if deployments:
                        deployment_id = deployments[0].get("id")
            
            if not deployment_id:
                return ["ERROR: No deployments found"]
            
            # Fetch deployment logs
            url = f"{self.base_url}/apps/{self.app_id}/deployments/{deployment_id}/logs"
            response = await client.get(url, params={"type": "RUN"})
            
            if response.status_code == 200:
                data = response.json()
                logs = data.get("logs", [])
                if isinstance(logs, str):
                    logs = logs.split("\n")
                return logs
            else:
                return [f"ERROR: {response.status_code} - {response.text}"]
                
        except Exception as e:
            return [f"ERROR: {str(e)}"]
    
    def analyze_logs(self, logs: List[str]) -> Dict[str, Any]:
        """
        Analyze logs for common issues.
        
        Args:
            logs: List of log lines to analyze
            
        Returns:
            Analysis report with identified issues
        """
        issues: List[LogIssue] = []
        issue_counts: Dict[str, Dict] = {}
        
        log_text = "\n".join(logs)
        
        # Check each pattern
        for issue_name, issue_config in self.ISSUE_PATTERNS.items():
            pattern = issue_config["pattern"]
            matches = re.findall(pattern, log_text, re.IGNORECASE)
            
            if matches:
                # Find sample log lines containing the pattern
                sample_logs = []
                for log_line in logs:
                    if re.search(pattern, log_line, re.IGNORECASE):
                        sample_logs.append(log_line[:200])  # Truncate long lines
                        if len(sample_logs) >= 3:
                            break
                
                issue = LogIssue(
                    severity=issue_config["severity"],
                    category=issue_config["category"],
                    message=f"{issue_name}: Found {len(matches)} occurrences",
                    count=len(matches),
                    first_seen="In fetched logs",
                    last_seen="In fetched logs",
                    sample_logs=sample_logs,
                    suggested_fix=issue_config["fix"]
                )
                issues.append(issue)
        
        # Sort by severity
        severity_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
        issues.sort(key=lambda x: severity_order.get(x.severity, 99))
        
        # Extract key metrics from logs
        metrics = self._extract_metrics(logs)
        
        return {
            "timestamp": datetime.now().isoformat(),
            "total_lines": len(logs),
            "issues_found": len(issues),
            "issues": [
                {
                    "severity": i.severity,
                    "category": i.category,
                    "message": i.message,
                    "count": i.count,
                    "sample_logs": i.sample_logs,
                    "suggested_fix": i.suggested_fix
                }
                for i in issues
            ],
            "metrics": metrics,
            "health_score": self._calculate_health_score(issues),
            "summary": self._generate_summary(issues, metrics)
        }
    
    def _extract_metrics(self, logs: List[str]) -> Dict[str, Any]:
        """Extract key metrics from logs"""
        metrics = {
            "heartbeats": 0,
            "strategies_processed": 0,
            "orders_placed": 0,
            "orders_failed": 0,
            "signals_generated": 0,
            "api_calls": 0,
            "cache_hits": 0,
            "errors": 0,
            "warnings": 0
        }
        
        for line in logs:
            line_lower = line.lower()
            
            if "heartbeat" in line_lower:
                metrics["heartbeats"] += 1
            if "processing strategy" in line_lower:
                metrics["strategies_processed"] += 1
            if "order placed" in line_lower or "placing order" in line_lower:
                metrics["orders_placed"] += 1
            if "order failed" in line_lower or "order rejected" in line_lower:
                metrics["orders_failed"] += 1
            if "signal" in line_lower and ("generated" in line_lower or "buy" in line_lower or "sell" in line_lower):
                metrics["signals_generated"] += 1
            if "api" in line_lower and ("call" in line_lower or "request" in line_lower):
                metrics["api_calls"] += 1
            if "cache hit" in line_lower or "using cached" in line_lower:
                metrics["cache_hits"] += 1
            if "error" in line_lower:
                metrics["errors"] += 1
            if "warning" in line_lower or "⚠️" in line:
                metrics["warnings"] += 1
        
        return metrics
    
    def _calculate_health_score(self, issues: List[LogIssue]) -> int:
        """Calculate health score (0-100) based on issues"""
        score = 100
        
        for issue in issues:
            if issue.severity == "CRITICAL":
                score -= 30
            elif issue.severity == "HIGH":
                score -= 15
            elif issue.severity == "MEDIUM":
                score -= 5
            elif issue.severity == "LOW":
                score -= 2
        
        return max(0, score)
    
    def _generate_summary(self, issues: List[LogIssue], metrics: Dict) -> str:
        """Generate human-readable summary"""
        if not issues:
            return "✅ No issues detected. System appears healthy."
        
        critical = sum(1 for i in issues if i.severity == "CRITICAL")
        high = sum(1 for i in issues if i.severity == "HIGH")
        
        if critical > 0:
            return f"🚨 CRITICAL: {critical} critical issue(s) detected! Immediate attention required."
        elif high > 0:
            return f"⚠️ WARNING: {high} high-severity issue(s) detected. Please investigate."
        else:
            return f"📊 {len(issues)} minor issue(s) detected. System is operational."
    
    async def get_health_report(self) -> Dict[str, Any]:
        """
        Get a complete health report by fetching and analyzing logs.
        
        Returns:
            Complete health report with logs and analysis
        """
        logs = await self.fetch_recent_logs()
        analysis = self.analyze_logs(logs)
        
        return {
            "report_time": datetime.now().isoformat(),
            "app_id": self.app_id,
            "analysis": analysis,
            "recent_logs": logs[-100:] if len(logs) > 100 else logs  # Last 100 lines
        }
    
    async def close(self):
        """Close the HTTP client"""
        if self._client:
            await self._client.aclose()
            self._client = None


# Global instance for easy access
_log_monitor: Optional[DOLogMonitor] = None

def get_log_monitor() -> DOLogMonitor:
    """Get or create the global log monitor instance"""
    global _log_monitor
    if _log_monitor is None:
        _log_monitor = DOLogMonitor()
    return _log_monitor


# Standalone script execution
async def main():
    """Main function for standalone execution"""
    print("=" * 60)
    print("🔍 DigitalOcean Log Monitor")
    print("=" * 60)
    
    monitor = DOLogMonitor()
    
    if not monitor.is_configured:
        print("\n⚠️ Monitor not configured!")
        print("Please set these environment variables:")
        print("  - DO_API_TOKEN: Your DigitalOcean API token")
        print("  - DO_APP_ID: Your app ID (from DigitalOcean dashboard)")
        print("\nTo get your API token:")
        print("  1. Go to https://cloud.digitalocean.com/account/api/tokens")
        print("  2. Generate a new token with read access")
        print("\nTo get your App ID:")
        print("  1. Go to your app in DigitalOcean")
        print("  2. The ID is in the URL: /apps/<APP_ID>")
        return
    
    print("\n📡 Fetching logs from DigitalOcean...")
    report = await monitor.get_health_report()
    
    print(f"\n📊 Health Score: {report['analysis']['health_score']}/100")
    print(f"📝 {report['analysis']['summary']}")
    
    if report['analysis']['issues']:
        print("\n🚨 Issues Found:")
        for issue in report['analysis']['issues']:
            print(f"\n  [{issue['severity']}] {issue['category']}")
            print(f"    {issue['message']}")
            print(f"    Fix: {issue['suggested_fix']}")
            if issue['sample_logs']:
                print(f"    Sample: {issue['sample_logs'][0][:100]}...")
    
    print("\n📈 Metrics:")
    for key, value in report['analysis']['metrics'].items():
        if value > 0:
            print(f"  - {key}: {value}")
    
    await monitor.close()


if __name__ == "__main__":
    asyncio.run(main())
