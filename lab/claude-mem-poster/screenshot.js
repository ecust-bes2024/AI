const puppeteer = require('puppeteer');
const path = require('path');

(async () => {
  const browser = await puppeteer.launch();
  const page = await browser.newPage();

  await page.goto('file://' + path.join(__dirname, 'poster.html'), {
    waitUntil: 'networkidle0'
  });

  // 获取实际内容高度
  const bodyHeight = await page.evaluate(() => document.body.scrollHeight);

  // 设置视口大小为实际内容大小
  await page.setViewport({
    width: 800,
    height: bodyHeight
  });

  // 截图
  await page.screenshot({
    path: 'poster-auto.png',
    fullPage: false
  });

  console.log(`✅ Screenshot saved: 800x${bodyHeight}px`);

  await browser.close();
})();
