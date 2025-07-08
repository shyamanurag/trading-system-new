// Check current IST time and market status
const now = new Date();
const istOffset = 5.5 * 60 * 60 * 1000; // IST is UTC+5:30
const istTime = new Date(now.getTime() + istOffset);

console.log('🕐 TIME & MARKET STATUS CHECK');
console.log('==============================');

console.log(`📅 Current UTC: ${now.toISOString()}`);
console.log(`🇮🇳 Current IST: ${istTime.toLocaleString('en-IN', {
    timeZone: 'Asia/Kolkata',
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
})}`);

const istHour = istTime.getHours();
const istMinute = istTime.getMinutes();
const istDay = istTime.getDay(); // 0=Sunday, 1=Monday, etc.

console.log(`⏰ IST Time: ${istHour}:${istMinute.toString().padStart(2, '0')}`);
console.log(`📅 Day of Week: ${['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'][istDay]}`);

// Market hours: 9:15 AM to 3:30 PM IST, Monday to Friday
const isWeekday = istDay >= 1 && istDay <= 5; // Monday to Friday
const marketStartMinutes = 9 * 60 + 15; // 9:15 AM in minutes
const marketEndMinutes = 15 * 60 + 30; // 3:30 PM in minutes  
const currentMinutes = istHour * 60 + istMinute;

const isMarketHours = isWeekday && currentMinutes >= marketStartMinutes && currentMinutes <= marketEndMinutes;

console.log(`📈 Market Status:`);
console.log(`   Weekday: ${isWeekday ? '✅ Yes (Mon-Fri)' : '❌ No (Weekend)'}`);
console.log(`   Time Range: ${isMarketHours ? '✅ Within 9:15 AM - 3:30 PM IST' : '❌ Outside market hours'}`);
console.log(`   Overall: ${isMarketHours ? '🟢 MARKET OPEN' : '🔴 MARKET CLOSED'}`);

if (!isMarketHours) {
    if (!isWeekday) {
        console.log('\n💡 Market closed - Weekend');
    } else if (currentMinutes < marketStartMinutes) {
        const minutesToOpen = marketStartMinutes - currentMinutes;
        const hoursToOpen = Math.floor(minutesToOpen / 60);
        const minsToOpen = minutesToOpen % 60;
        console.log(`\n⏳ Market opens in: ${hoursToOpen}h ${minsToOpen}m`);
    } else {
        console.log('\n💤 Market closed for the day - Opens tomorrow at 9:15 AM IST');
    }
}

// Test the deployed app's market detection
console.log('\n🔍 Testing Deployed App Market Detection...');
(async () => {
    try {
        const res = await fetch('https://algoauto-9gx56.ondigitalocean.app/api/v1/autonomous/status');
        const data = await res.json();
        const marketOpen = data.data?.market_open || false;
        console.log(`   🌐 App Reports Market Open: ${marketOpen ? '✅ YES' : '❌ NO'}`);

        if (isMarketHours !== marketOpen) {
            console.log(`   ⚠️ MISMATCH: Local calculation (${isMarketHours}) vs App (${marketOpen})`);
            console.log(`   💡 This could explain the initialization failure`);
        } else {
            console.log(`   ✅ Local and App market status match`);
        }
    } catch (e) {
        console.log(`   ❌ Error checking app: ${e.message}`);
    }
})(); 