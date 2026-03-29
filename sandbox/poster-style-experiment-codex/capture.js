const playwright = require('playwright');
const path = require('path');

async function main() {
  const htmlPath = process.argv[2]
    ? path.resolve(process.argv[2])
    : path.join(__dirname, 'poster.html');
  const outputPath = process.argv[3]
    ? path.resolve(process.argv[3])
    : path.join(__dirname, 'claude-mem-poster.png');
  const width = Number.parseInt(process.argv[4] || '800', 10);

  const browser = await playwright.chromium.launch();
  const page = await browser.newPage({
    viewport: { width, height: 600 }
  });

  await page.goto(`file://${htmlPath}`);
  await page.waitForLoadState('networkidle');

  const bodyHeight = await page.evaluate(() => document.body.scrollHeight);
  await page.setViewportSize({ width, height: bodyHeight });

  await page.screenshot({
    path: outputPath,
    fullPage: true
  });

  console.log(`✅ Poster generated: ${outputPath}`);
  await browser.close();
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
