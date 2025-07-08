/**
 * GET DETAILED SYSTEM STATUS
 * Fetch complete details from the working system status endpoint
 */

const BASE_URL = 'https://algoauto-9gx56.ondigitalocean.app';

async function getDetailedSystemStatus() {
    console.log('🔍 GETTING DETAILED SYSTEM STATUS');
    console.log('='.repeat(50));
    
    try {
        const response = await fetch(`${BASE_URL}/api/v1/system/status`);
        
        if (response.status === 200) {
            const data = await response.json();
            console.log('📊 FULL SYSTEM STATUS:');
            console.log(JSON.stringify(data, null, 2));
            
            // Analyze the data
            console.log('\n🔍 ANALYSIS:');
            if (data.components) {
                console.log('📋 Components:');
                Object.entries(data.components).forEach(([key, value]) => {
                    const status = value === 'connected' || value === 'running' || value === true ? '✅' : '❌';
                    console.log(`  ${status} ${key}: ${value}`);
                });
            }
            
            if (data.database) {
                console.log(`📊 Database: ${data.database}`);
            }
            
            if (data.redis) {
                console.log(`📊 Redis: ${data.redis}`);
            }
            
            if (data.trading_system) {
                console.log(`📊 Trading System: ${data.trading_system}`);
            }
            
        } else {
            console.log(`❌ Error: ${response.status}`);
            console.log(await response.text());
        }
        
    } catch (error) {
        console.log(`💥 Request failed: ${error.message}`);
    }
    
    console.log('\n' + '='.repeat(50));
}

// Run the detailed status check
getDetailedSystemStatus().catch(console.error); 