// 获取页面实际高度
const fs = require('fs');
const path = require('path');

const html = fs.readFileSync(path.join(__dirname, 'poster.html'), 'utf8');

// 简单计算：统计 section 数量和内容
const sectionCount = (html.match(/class="section"/g) || []).length;
const cardCount = (html.match(/class="card"/g) || []).length;

// 估算高度：
// header: ~120px
// 每个 section: ~40px (title + margin)
// 每个 card: ~100-200px (平均 150px)
// footer: ~60px
// padding: 80px (top + bottom)

const estimatedHeight = 120 + (sectionCount * 40) + (cardCount * 150) + 60 + 80;

console.log(estimatedHeight);
