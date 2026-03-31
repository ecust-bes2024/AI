# Claude Code 源码提取与架构分析

## 概述

Claude Code 是 Anthropic 官方推出的 AI 编程助手 CLI 工具。通过分析其发布的 `cli.js.map` 文件（57MB），我们可以完整提取其 TypeScript 源码，深入理解其架构设计。

**关键发现**：
- `cli.js.map` 包含 4756 个源文件的完整内容
- 1906 个 Claude Code 自身源码（TypeScript/TSX）
- 2850 个 node_modules 依赖
- **无需反编译**：sourcemap 的 `sourcesContent` 字段直接存储原始代码

**技术栈**：
- React + Ink（终端 UI）
- TypeScript（类型安全）
- Anthropic API（Claude 模型）
- 自定义工具系统（45+ 工具）
- Agent/Skill/Team 协作框架

---

## 源码提取方法

### 原理

Sourcemap 文件（`.js.map`）是 JavaScript 构建工具生成的调试文件，用于将压缩/转译后的代码映射回原始源码。其 JSON 结构包含：

```json
{
  "version": 3,
  "sources": ["src/file1.ts", "src/file2.tsx", ...],
  "sourcesContent": ["<file1 完整源码>", "<file2 完整源码>", ...],
  "mappings": "AAAA,CAAC,CAAC...",
  ...
}
```

- `sources`：源文件路径数组
- `sourcesContent`：对应的完整源码数组
- 两者索引一一对应

### 提取脚本（Node.js）

```javascript
#!/usr/bin/env node
const fs = require('fs');
const path = require('path');

// 读取 sourcemap 文件
const sourcemapPath = process.argv[2] || 'cli.js.map';
const outputDir = process.argv[3] || 'extracted-source';

console.log(`Reading sourcemap: ${sourcemapPath}`);
const sourcemap = JSON.parse(fs.readFileSync(sourcemapPath, 'utf8'));

const { sources, sourcesContent } = sourcemap;

if (!sources || !sourcesContent) {
  console.error('Invalid sourcemap: missing sources or sourcesContent');
  process.exit(1);
}

console.log(`Found ${sources.length} source files`);

// 提取源码
let extracted = 0;
let skipped = 0;

sources.forEach((sourcePath, index) => {
  const content = sourcesContent[index];
  
  if (!content) {
    skipped++;
    return;
  }

  // 过滤 node_modules（可选）
  if (sourcePath.includes('node_modules')) {
    skipped++;
    return;
  }

  // 构建输出路径
  const outputPath = path.join(outputDir, sourcePath);
  const outputDirPath = path.dirname(outputPath);

  // 创建目录
  fs.mkdirSync(outputDirPath, { recursive: true });

  // 写入文件
  fs.writeFileSync(outputPath, content, 'utf8');
  extracted++;
});

console.log(`\nExtraction complete:`);
console.log(`  Extracted: ${extracted} files`);
console.log(`  Skipped: ${skipped} files`);
console.log(`  Output: ${outputDir}/`);
```

**使用方法**：

```bash
node extract-sourcemap.js cli.js.map output/
```

