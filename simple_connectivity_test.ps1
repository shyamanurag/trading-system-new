Write-Host "🚀 Frontend-to-Backend Connectivity Test Suite" -ForegroundColor Green
Write-Host "=============================================================" -ForegroundColor Green
Write-Host "⏰ Started at: $(Get-Date)" -ForegroundColor Cyan

$urls = @(
    "https://algoauto-9gx56.ondigitalocean.app/api/v1/users/performance",
    "https://algoauto-9gx56.ondigitalocean.app/api/market/indices",
    "https://algoauto-9gx56.ondigitalocean.app/api/v1/dashboard/data",
    "https://algoauto-9gx56.ondigitalocean.app/api/v1/elite",
    "https://algoauto-9gx56.ondigitalocean.app/api/v1/strategies",
    "https://algoauto-9gx56.ondigitalocean.app/ws/test"
)

$successCount = 0
$totalCount = $urls.Count

foreach ($url in $urls) {
    Write-Host ""
    Write-Host "🔍 Testing: $url" -ForegroundColor Yellow
    
    try {
        $response = Invoke-WebRequest -Uri $url -TimeoutSec 10 -UseBasicParsing
        Write-Host "✅ Status: $($response.StatusCode)" -ForegroundColor Green
        
        if ($response.StatusCode -eq 200) {
            $successCount++
            Write-Host "✅ SUCCESS" -ForegroundColor Green
        }
        else {
            Write-Host "⚠️ UNEXPECTED STATUS" -ForegroundColor Yellow
        }
    }
    catch {
        Write-Host "❌ FAILED: $($_.Exception.Message)" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "=============================================================" -ForegroundColor Green
Write-Host "📋 SUMMARY" -ForegroundColor Green
Write-Host "=============================================================" -ForegroundColor Green
Write-Host "✅ Successful: $successCount/$totalCount" -ForegroundColor Green
Write-Host "❌ Failed: $($totalCount - $successCount)/$totalCount" -ForegroundColor Red

if ($successCount -eq $totalCount) {
    Write-Host "🎉 ALL TESTS PASSED!" -ForegroundColor Green
}
else {
    Write-Host "⚠️ Some connectivity issues remain" -ForegroundColor Yellow
}

Write-Host "⏰ Completed at: $(Get-Date)" -ForegroundColor Cyan 