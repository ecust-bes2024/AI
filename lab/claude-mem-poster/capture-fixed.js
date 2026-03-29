const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({
    args: ['--disable-blink-features=AutomationControlled']
  });

  const context = await browser.newContext({
    viewport: { width: 800, height: 600 }
  });

  const page = await context.newPage();

  // 加载 HTML 文件
  await page.goto(`file://${__dirname}/poster.html`);

  // 等待页面完全加载
  await page.waitForLoadState('networkidle');

  // 获取 .container 元素的实际高度
  const containerHeight = await page.evaluate(() => {
    const container = document.querySelector('.container');
    return container ? container.offsetHeight : document.body.scrollHeight;
  });

  console.log(`Content height: ${containerHeight}px`);

  // 截取 .container 元素
  const container = await page.$('.container');
  await container.screenshot({
    path: 'claude-mem-poster.png'
  });

  console.log('✅ Poster generated: claude-mem-poster.png');

  await browser.close();
})();
