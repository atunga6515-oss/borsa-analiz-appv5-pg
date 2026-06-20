const fs = require('fs');
const { createChart, CandlestickSeries } = require('lightweight-charts');

const candles = JSON.parse(fs.readFileSync('../test_candles.json', 'utf8'));

// We need a DOM element, so we can't fully run createChart in Node easily without JSDOM.
// Let's just check the array for lightweight-charts ascending rules natively.

let prevTime = -1;
for (let i = 0; i < candles.length; i++) {
    const c = candles[i];
    if (c.time <= prevTime) {
        console.error(`Validation Failed at index ${i}: time ${c.time} is not strictly greater than prevTime ${prevTime}`);
        process.exit(1);
    }
    prevTime = c.time;
    if (c.open == null || c.high == null || c.low == null || c.close == null) {
        console.error(`Validation Failed at index ${i}: contains null`);
        process.exit(1);
    }
}
console.log("Validation PASSED. Data is strictly ascending and contains no nulls.");
