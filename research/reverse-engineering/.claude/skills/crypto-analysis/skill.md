---
name: crypto-analysis
description: "加密算法识别与分析。当需要识别二进制中的加密算法、分析加密流量、或逆向加密实现时使用。"
---

# 加密分析

识别、分析和理解目标应用中的加密实现。

## 识别方法

### 1. 常量特征识别

常见加密算法的魔数常量：

| 算法 | 特征常量 |
|------|----------|
| AES | S-Box: `63 7c 77 7b f2 6b 6f c5` |
| SHA-256 | `6a09e667 bb67ae85 3c6ef372 a54ff53a` |
| MD5 | `67452301 efcdab89 98badcfe 10325476` |
| RSA | 大整数运算、`65537` (0x10001) 公钥指数 |
| ChaCha20 | `expand 32-byte k` |
| RC4 | 256 字节 S-Box 初始化 |

### 2. Ghidra 自动识别

```bash
# 使用 FindCrypt-Ghidra 插件
# 安装: 将 FindCrypt.java 放入 Ghidra/Extensions/
# 运行: Ghidra → Script Manager → FindCrypt

# 或使用 GhidraMCP（已配置）
# Claude 可通过 MCP 直接调用 Ghidra 分析
```

### 3. YARA 规则扫描

```bash
# 使用 crypto YARA 规则
yara crypto_signatures.yar target_binary

# findcrypt-yara 规则集
# https://github.com/polymorf/findcrypt-yara
```

## 流量加密分析

### TLS 分析

```bash
# 查看 TLS 握手信息
tshark -r capture.pcap -Y "tls.handshake" -T fields \
  -e tls.handshake.type \
  -e tls.handshake.ciphersuite \
  -e tls.handshake.extensions.server_name

# 使用 mitmproxy 解密 TLS
mitmproxy --mode regular --set ssl_insecure=true
```

### 自定义加密识别

| 特征 | 可能的加密方式 |
|------|----------------|
| 数据长度是 16 的倍数 | AES-CBC/ECB |
| 前 12-16 字节随机 + 固定长度 | AES-GCM (IV + ciphertext + tag) |
| 数据看起来完全随机 | 强加密或压缩后加密 |
| Base64 编码的固定长度 | 加密后 Base64 |
| 相同输入产生相同输出 | ECB 模式或确定性加密 |
| 相同输入产生不同输出 | CBC/GCM/CTR（含随机 IV） |

## Python 分析工具

```python
import hashlib
from collections import Counter

def analyze_entropy(data: bytes) -> float:
    """计算数据熵值，高熵值(>7.5)暗示加密或压缩"""
    if not data:
        return 0
    counter = Counter(data)
    length = len(data)
    entropy = -sum(
        (count/length) * __import__('math').log2(count/length)
        for count in counter.values()
    )
    return entropy

def detect_block_cipher(data: bytes) -> str:
    """检测是否为分组加密"""
    if len(data) % 16 == 0:
        return "可能是 AES (16 字节块)"
    if len(data) % 8 == 0:
        return "可能是 DES/3DES (8 字节块)"
    return "非标准分组或流加密"
```

## 常见陷阱

- **混淆 ≠ 加密** — XOR、Base64、字节翻转不是真正的加密
- **自研加密** — 很多应用使用自定义"加密"，通常很弱
- **密钥硬编码** — 检查二进制中的硬编码密钥和 IV
- **证书固定** — Certificate Pinning 会阻止 mitmproxy 拦截
