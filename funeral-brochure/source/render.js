const { chromium } = require('/opt/node-tools/node_modules/playwright');
(async () => {
  const [,, htmlPath, pdfPath] = process.argv;
  const browser = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium-1194/chrome-linux/chrome' });
  const page = await browser.newPage();
  await page.goto('file://' + htmlPath, { waitUntil: 'load' });
  await page.evaluate(() => document.fonts.ready);
  await page.pdf({ path: pdfPath, preferCSSPageSize: true, printBackground: true });
  await browser.close();
  console.log('pdf written', pdfPath);
})().catch(e => { console.error(e); process.exit(1); });
