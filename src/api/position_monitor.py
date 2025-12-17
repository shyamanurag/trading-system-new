"""
Position Monitor API - Auto Square-Off Monitoring and Control
===========================================================

Provides API endpoints for monitoring and controlling the position monitor
service that handles continuous auto square-off functionality.
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, Optional
import logging
from datetime import datetime

from src.core.dependencies import get_orchestrator

logger = logging.getLogger(__name__)

router = APIRouter(tags=["position-monitor"])

@router.get("/status")
async def get_position_monitor_status():
    """Get current position monitor status"""
    try:
        orchestrator = await get_orchestrator()
        
        if not orchestrator.position_monitor:
            return {
                'available': False,
                'message': 'Position Monitor not initialized',
                'timestamp': datetime.now().isoformat()
            }
        
        status = await orchestrator.position_monitor.get_monitoring_status()
        
        return {
            'available': True,
            'status': status,
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting position monitor status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/start")
async def start_position_monitoring():
    """Start position monitoring"""
    try:
        orchestrator = await get_orchestrator()
        
        if not orchestrator.position_monitor:
            raise HTTPException(status_code=404, detail="Position Monitor not available")
        
        await orchestrator.position_monitor.start_monitoring()
        
        return {
            'success': True,
            'message': 'Position monitoring started',
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error starting position monitoring: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/stop")
async def stop_position_monitoring():
    """Stop position monitoring"""
    try:
        orchestrator = await get_orchestrator()
        
        if not orchestrator.position_monitor:
            raise HTTPException(status_code=404, detail="Position Monitor not available")
        
        await orchestrator.position_monitor.stop_monitoring()
        
        return {
            'success': True,
            'message': 'Position monitoring stopped',
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error stopping position monitoring: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/force-square-off")
async def force_square_off_all_positions(reason: Optional[str] = "Manual square-off"):
    """Force square-off all positions immediately"""
    try:
        orchestrator = await get_orchestrator()
        
        if not orchestrator.position_monitor:
            raise HTTPException(status_code=404, detail="Position Monitor not available")
        
        result = await orchestrator.position_monitor.force_square_off_all(reason)
        
        return result
        
    except Exception as e:
        logger.error(f"Error in force square-off: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/exit-conditions")
async def get_exit_conditions():
    """Get current exit conditions and monitoring parameters"""
    try:
        orchestrator = await get_orchestrator()
        
        if not orchestrator.position_monitor:
            raise HTTPException(status_code=404, detail="Position Monitor not available")
        
        # Get current positions
        positions = await orchestrator.position_tracker.get_all_positions()
        
        # Get monitoring configuration
        monitor = orchestrator.position_monitor
        
        return {
            'monitoring_active': monitor.is_running,
            'positions_count': len(positions),
            'monitoring_interval': monitor.monitoring_interval,
            'intraday_exit_time': monitor.intraday_exit_time.strftime('%H:%M'),
            'market_close_time': monitor.market_close_time.strftime('%H:%M'),
            'emergency_stop_active': monitor.emergency_stop_active,
            'market_close_initiated': monitor.market_close_initiated,
            'executed_exits_count': len(monitor.executed_exits),
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting exit conditions: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/positions-with-exits")
async def get_positions_with_exit_conditions():
    """Get all positions with their exit conditions"""
    try:
        orchestrator = await get_orchestrator()
        
        if not orchestrator.position_monitor:
            raise HTTPException(status_code=404, detail="Position Monitor not available")
        
        # Get current positions
        positions = await orchestrator.position_tracker.get_all_positions()
        
        # Evaluate exit conditions for each position
        positions_with_exits = []
        
        for symbol, position in positions.items():
            position_data = {
                'symbol': symbol,
                'quantity': position.quantity,
                'entry_price': position.average_price,
                'current_price': position.current_price,
                'unrealized_pnl': position.unrealized_pnl,
                'side': position.side,
                'entry_time': position.entry_time.isoformat(),
                'exit_conditions': []
            }
            
            # Check stop loss
            if hasattr(position, 'stop_loss') and position.stop_loss:
                position_data['stop_loss'] = position.stop_loss
                position_data['exit_conditions'].append({
                    'type': 'stop_loss',
                    'trigger_price': position.stop_loss,
                    'active': True
                })
            
            # Check target
            if hasattr(position, 'target') and position.target:
                position_data['target'] = position.target
                position_data['exit_conditions'].append({
                    'type': 'target',
                    'trigger_price': position.target,
                    'active': True
                })
            
            # Time-based exits
            position_data['exit_conditions'].extend([
                {
                    'type': 'intraday_exit',
                    'trigger_time': '15:15',
                    'active': True
                },
                {
                    'type': 'market_close',
                    'trigger_time': '15:30',
                    'active': True
                }
            ])
            
            positions_with_exits.append(position_data)
        
        return {
            'positions': positions_with_exits,
            'total_positions': len(positions_with_exits),
            'monitoring_active': orchestrator.position_monitor.is_running,
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting positions with exit conditions: {e}")
        raise HTTPException(status_code=500, detail=str(e)) 