/* Real-browser walkthrough; Playwright is a test dependency, not a UI dependency. */
const {chromium} = require('playwright');
const {spawn} = require('node:child_process');
const path = require('node:path');
const assert = require('node:assert/strict');

(async () => {
  const child = spawn(process.env.CDC_DEMO_PYTHON || 'python3',
    ['-m','pipeline_reliability.cdc_interactive','--port','0'],
    {cwd:process.env.CDC_DEMO_CWD || path.resolve(__dirname,'..'),stdio:['ignore','pipe','pipe']});
  const url = await new Promise((resolve,reject) => {
    const timer = setTimeout(()=>reject(Error('server startup timeout')),15000);
    child.stdout.on('data',data=>{const match=data.toString().match(/http:\/\/127\.0\.0\.1:\d+/);if(match){clearTimeout(timer);resolve(match[0])}});
    child.on('error',reject);child.on('exit',code=>{clearTimeout(timer);reject(Error(`server exited ${code}`))});
  });
  let browser;
  try {
    browser=await chromium.launch({headless:true,executablePath:process.env.CDC_BROWSER_EXECUTABLE || undefined});
    const page=await browser.newPage({viewport:{width:1440,height:1100}});
    const errors=[];page.on('pageerror',error=>errors.push(error.message));
    await page.goto(url);
    await page.getByText('Incorrect final state',{exact:true}).waitFor();
    await page.locator('#counterexample').click();
    await page.waitForFunction(()=>document.querySelector('#actual').textContent.includes('"version": 3'));
    assert.match(await page.locator('#wrong').textContent(),/k0: stale version/);
    await page.locator('#strategy').selectOption('id_only');await page.locator('#run').click();
    await page.getByText('Incorrect final state',{exact:true}).waitFor();
    await page.locator('#strategy').selectOption('version');await page.locator('#run').click();
    await page.getByText('Matches the oracle',{exact:true}).waitFor();
    await page.locator('#next').click();
    assert.match(await page.locator('#event').textContent(),/"phase": "restart"/);
    await page.locator('#name').selectOption('post_recovery_redelivery');
    for(const [id,value] of Object.entries({keys:'3',checkpoint:'4',interruption:'8'}))await page.locator('#'+id).fill(value);
    await page.locator('#run').click();
    await page.waitForFunction(()=>document.querySelector('#metrics').textContent.includes('"lost_attempts": 4'));
    assert.match(await page.locator('#metrics').textContent(),/"redelivery_state_unchanged": true/);
    await page.locator('#name').selectOption('ledger_expiry');await page.locator('#validation').selectOption('online');
    for(const [id,value] of Object.entries({keys:'16',checkpoint:'0',interruption:'0',capacity:'4'}))await page.locator('#'+id).fill(value);
    await page.locator('#run').click();
    await page.waitForFunction(()=>document.querySelector('#explanation').textContent.includes('Injected conflict was not detected'));
    await page.locator('#capacity').fill('');await page.locator('#run').click();
    await page.getByText('Online processing stopped',{exact:true}).waitFor();
    assert.match(await page.locator('#explanation').textContent(),/conflicting event ID/);
    await page.locator('#counterexample').click();await page.getByText('Incorrect final state',{exact:true}).waitFor();
    if(process.env.CDC_SCREENSHOT)await page.screenshot({path:process.env.CDC_SCREENSHOT,fullPage:true});
    assert.deepEqual(errors,[]);
    console.log('Real-browser walkthrough passed: preset, strategies, trace, checkpoint/recovery, finite/unlimited ledger, conflict warning; no JS errors.');
  } finally {
    if(browser)await browser.close();child.kill('SIGTERM');
  }
})().catch(error=>{console.error(error);process.exitCode=1});
