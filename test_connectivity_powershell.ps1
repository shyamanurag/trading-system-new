# Frontend-to-Backend Connectivity Test Script (PowerShell)
# Tests the connectivity fixes without requiring Python

Write-Host "🚀 Frontend-to-Backend Connectivity Test Suite (PowerShell)" -ForegroundColor Green
Write-Host "=============================================================" -ForegroundColor Green
Write-Host "⏰ Started at: $(Get-Date)" -ForegroundColor Cyan

# Test endpoints that were causing connectivity issues
$testEndpoints = @(
    @{
        name = "Users Performance (New)"
        url = "https://algoauto-9gx56.ondigitalocean.app/api/v1/users/performance"
        expectedFields = @("success", "data", "timestamp")
    },
    @{
        name = "Market Indices (New)"
        url = "https://algoauto-9gx56.ondigitalocean.app/api/market/indices"
        expectedFields = @("success", "data", "timestamp")
    },
    @{
        name = "Dashboard Data (Standardized)"
        url = "https://algoauto-9gx56.ondigitalocean.app/api/v1/dashboard/data"
        expectedFields = @("success", "data", "timestamp")
    },
    @{
        name = "Elite Recommendations"
        url = "https://algoauto-9gx56.ondigitalocean.app/api/v1/elite"
        expectedFields = @("success", "data", "timestamp")
    },
    @{
        name = "Strategies Management"
        url = "https://algoauto-9gx56.ondigitalocean.app/api/v1/strategies"
        expectedFields = @()  # May return empty array
    },
    @{
        name = "WebSocket Test Page"
        url = "https://algoauto-9gx56.ondigitalocean.app/ws/test"
        expectedFields = @()  # HTML page
    }
)

$results = @()
$totalTests = $testEndpoints.Count
$successfulTests = 0

foreach ($endpoint in $testEndpoints) {
    Write-Host ""
    Write-Host "🔍 Testing: $($endpoint.name)" -ForegroundColor Yellow
    Write-Host "📡 URL: $($endpoint.url)" -ForegroundColor Gray
    
    try {
        # Make HTTP request with timeout
        $response = Invoke-WebRequest -Uri $endpoint.url -TimeoutSec 10 -UseBasicParsing
        
        Write-Host "✅ Status Code: $($response.StatusCode)" -ForegroundColor Green
        
        # Check if it's JSON response
        $isJson = $false
        $jsonData = $null
        
        try {
            $jsonData = $response.Content | ConvertFrom-Json
            $isJson = $true
            Write-Host "📄 Response Type: JSON" -ForegroundColor Green
            
            # Check expected fields
            if ($endpoint.expectedFields.Count -gt 0) {
                foreach ($field in $endpoint.expectedFields) {
                    if ($jsonData.PSObject.Properties.Name -contains $field) {
                        Write-Host "✅ Field '$field': Present" -ForegroundColor Green
                    } else {
                        Write-Host "❌ Field '$field': Missing" -ForegroundColor Red
                    }
                }
            }
            
            # Show data structure
            if ($jsonData -is [PSCustomObject]) {
                $keys = $jsonData.PSObject.Properties.Name
                Write-Host "📊 Data Structure: $($keys -join ', ')" -ForegroundColor Cyan
            } elseif ($jsonData -is [Array]) {
                Write-Host "📊 Data Structure: Array with $($jsonData.Count) items" -ForegroundColor Cyan
            }
            
        } catch {
            Write-Host "📄 Response Type: Non-JSON (HTML/Text)" -ForegroundColor Yellow
            Write-Host "📝 Content Length: $($response.Content.Length) bytes" -ForegroundColor Gray
        }
        
        $results += @{
            endpoint = $endpoint.name
            success = $true
            statusCode = $response.StatusCode
            responseSize = $response.Content.Length
        }
        
        $successfulTests++
        
    } catch [System.Net.WebException] {
        Write-Host "⏱️ Request timed out or connection error" -ForegroundColor Red
        $results += @{
            endpoint = $endpoint.name
            success = $false
            error = "timeout_or_connection_error"
        }
    } catch {
        Write-Host "❌ Error: $($_.Exception.Message)" -ForegroundColor Red
        $results += @{
            endpoint = $endpoint.name
            success = $false
            error = $_.Exception.Message
        }
    }
}

# Summary
Write-Host ""
Write-Host "=============================================================" -ForegroundColor Green
Write-Host "📋 CONNECTIVITY TEST SUMMARY" -ForegroundColor Green
Write-Host "=============================================================" -ForegroundColor Green

Write-Host "✅ Successful: $successfulTests/$totalTests" -ForegroundColor Green
Write-Host "❌ Failed: $($totalTests - $successfulTests)/$totalTests" -ForegroundColor Red

# Details
Write-Host ""
foreach ($result in $results) {
    if ($result.success) {
        Write-Host "✅ PASS - $($result.endpoint)" -ForegroundColor Green
    } else {
        Write-Host "❌ FAIL - $($result.endpoint)" -ForegroundColor Red
        Write-Host "    Error: $($result.error)" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "⏰ Completed at: $(Get-Date)" -ForegroundColor Cyan

if ($successfulTests -eq $totalTests) {
    Write-Host "🎉 ALL CONNECTIVITY TESTS PASSED!" -ForegroundColor Green
    exit 0
} else {
    Write-Host "⚠️ Some connectivity issues remain" -ForegroundColor Yellow
    exit 1
} 