# Trading System Log Watcher
# Polls the API every 5 seconds and shows status updates

$baseUrl = "https://algoauto-9gx56.ondigitalocean.app"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  ALGO AUTO - Live Trading Monitor" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$lastStatus = ""
$iteration = 0

while ($true) {
    $iteration++
    
    try {
        # Get trading status
        $status = Invoke-RestMethod -Uri "$baseUrl/api/v1/autonomous/status" -Method Get -TimeoutSec 10
        
        # Get market status
        $market = Invoke-RestMethod -Uri "$baseUrl/api/market/market-status" -Method Get -TimeoutSec 10
        
        # Clear and display
        Clear-Host
        Write-Host "========================================" -ForegroundColor Cyan
        Write-Host "  ALGO AUTO - Live Trading Monitor" -ForegroundColor Cyan
        Write-Host "  $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Gray
        Write-Host "========================================" -ForegroundColor Cyan
        Write-Host ""
        
        # Market Status
        $marketColor = if ($market.data.market_status -eq "OPEN") { "Green" } else { "Red" }
        Write-Host "MARKET: " -NoNewline
        Write-Host "$($market.data.market_status)" -ForegroundColor $marketColor -NoNewline
        Write-Host " | IST: $($market.data.ist_time)" -ForegroundColor Gray
        Write-Host ""
        
        # Trading Status
        $tradingColor = if ($status.data.is_active) { "Green" } else { "Yellow" }
        Write-Host "TRADING: " -NoNewline
        Write-Host $(if ($status.data.is_active) { "ACTIVE" } else { "STOPPED" }) -ForegroundColor $tradingColor
        Write-Host ""
        
        # Strategies
        Write-Host "STRATEGIES ($($status.data.active_strategies_count)):" -ForegroundColor White
        foreach ($strat in $status.data.active_strategies) {
            Write-Host "  - $strat" -ForegroundColor Gray
        }
        Write-Host ""
        
        # Positions & PnL
        Write-Host "POSITIONS: $($status.data.active_positions)" -ForegroundColor White
        $pnlColor = if ($status.data.daily_pnl -ge 0) { "Green" } else { "Red" }
        Write-Host "DAILY P&L: " -NoNewline
        Write-Host "Rs. $($status.data.daily_pnl)" -ForegroundColor $pnlColor
        Write-Host "TRADES TODAY: $($status.data.total_trades)" -ForegroundColor White
        Write-Host ""
        
        # Data Provider
        $dataColor = if ($market.data.data_provider.status -eq "CONNECTED") { "Green" } else { "Red" }
        Write-Host "DATA: " -NoNewline
        Write-Host "$($market.data.data_provider.status)" -ForegroundColor $dataColor -NoNewline
        Write-Host " ($($market.data.data_provider.name))" -ForegroundColor Gray
        Write-Host ""
        
        # Risk Status
        Write-Host "RISK: $($status.data.risk_status.status)" -ForegroundColor Gray
        Write-Host ""
        
        Write-Host "----------------------------------------" -ForegroundColor DarkGray
        Write-Host "Polling #$iteration | Press Ctrl+C to stop" -ForegroundColor DarkGray
        
    } catch {
        Write-Host "ERROR: $($_.Exception.Message)" -ForegroundColor Red
    }
    
    Start-Sleep -Seconds 5
}



