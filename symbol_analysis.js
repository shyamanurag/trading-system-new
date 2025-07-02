// Symbol Fetching Analysis for F&O Expansion
console.log('📊 SYMBOL FETCHING ANALYSIS');
console.log('===========================');

async function analyzeSymbols() {
    try {
        // 1. Check Market Data API
        console.log('\n1️⃣ Checking Market Data API...');
        const marketData = await fetch('https://algoauto-9gx56.ondigitalocean.app/api/v1/market-data');
        const mdData = await marketData.json();

        console.log('Status:', mdData.success ? '✅' : '❌');

        if (mdData.data) {
            const symbols = Object.keys(mdData.data);
            console.log('🔢 Current Symbol Count:', symbols.length);
            console.log('📈 Active Symbols:', symbols.join(', '));

            console.log('\n💰 Sample Prices:');
            symbols.slice(0, 5).forEach(symbol => {
                if (mdData.data[symbol]?.current_price) {
                    console.log(`   ${symbol}: ₹${mdData.data[symbol].current_price}`);
                }
            });
        }

        // 2. Check TrueData Integration
        console.log('\n2️⃣ Checking TrueData Integration...');
        const trueDataRes = await fetch('https://algoauto-9gx56.ondigitalocean.app/api/v1/truedata-options');
        const tdData = await trueDataRes.json();

        if (tdData.success && tdData.data) {
            console.log('TrueData Status: ✅');
            console.log('Available Symbols:', Object.keys(tdData.data).length);
            console.log('Sample TrueData Symbols:', Object.keys(tdData.data).slice(0, 10).join(', '));
        } else {
            console.log('TrueData Status: ❌ Not accessible');
        }

        // 3. Check Intelligent Symbol Manager
        console.log('\n3️⃣ Checking Intelligent Symbol Manager...');
        const symbolMgrRes = await fetch('https://algoauto-9gx56.ondigitalocean.app/api/v1/intelligent-symbols');
        const symData = await symbolMgrRes.json();

        if (symData.success) {
            console.log('Intelligent Symbol Manager: ✅');
            console.log('Managed Symbols:', symData.data?.managed_symbols?.length || 0);
        } else {
            console.log('Intelligent Symbol Manager: ❌ Not accessible');
        }

        // 4. System Recommendations
        console.log('\n🎯 EXPANSION ANALYSIS:');
        console.log('Current: 6 hardcoded symbols');
        console.log('Target: 250 F&O symbols');
        console.log('Gap: 244 additional symbols needed');

        console.log('\n🚀 NEXT STEPS:');
        console.log('1. Enable F&O symbol auto-discovery');
        console.log('2. Configure IntelligentSymbolManager for 250 symbols');
        console.log('3. Auto-subscribe to F&O segment symbols');
        console.log('4. Implement dynamic symbol expansion');

    } catch (e) {
        console.log('❌ Analysis Error:', e.message);
    }
}

analyzeSymbols(); 