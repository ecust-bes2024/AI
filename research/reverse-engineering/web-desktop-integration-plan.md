# Web 端与桌面工具集成方案

## 问题对齐

**用户需求**：Web 端上传配置后，桌面工具（Chip_Debug_Tool.py）能实时收到新增提示。

**当前状态**：
- **Web 端**：独立的 Web 服务（后端框架未知，疑似 FastAPI，nginx 反向代理）
- **桌面工具**：PySide6 桌面应用，已有 TCP 自动化服务器（端口 9527）
- **数据存储**：共享文件系统（`chips/` 目录）

---

## 后端技术栈识别

### 证据链

1. **API 响应特征**：
   - 错误格式：`{"detail": [{"type": "missing", "loc": ["body", "chip_model_id"], ...}]}`
   - 这是 **Pydantic 验证错误**，FastAPI 的标准格式

2. **HTTP 响应头**：
   ```
   Server: nginx/1.18.0 (Ubuntu)
   ```
   - nginx 作为反向代理，后端可能是 FastAPI + Uvicorn

3. **API 端点风格**：
   - RESTful 风格：`/api/chips/{chip_id}`
   - 符合 FastAPI 路由规范

4. **依赖文件**：
   - `requirements.txt` 和 `pyproject.toml` 中**没有** FastAPI/Flask
   - 说明 Web 端是**独立项目**，不在当前仓库

**结论**：Web 端后端 **99% 是 FastAPI**，但代码不在 `chip-deug-tool` 仓库中。

---

## 集成方案设计

### 方案对比

| 方案 | 实时性 | 复杂度 | 可靠性 | 推荐 |
|------|--------|--------|--------|------|
| **1. 文件监听（QFileSystemWatcher）** | 秒级 | 低 | 高 | ⭐⭐⭐⭐⭐ |
| **2. 轮询检查（QTimer）** | 分钟级 | 低 | 中 | ⭐⭐⭐ |
| **3. WebSocket 推送** | 毫秒级 | 高 | 高 | ⭐⭐⭐⭐ |
| **4. HTTP 轮询 API** | 秒级 | 中 | 中 | ⭐⭐ |
| **5. 共享数据库** | 秒级 | 高 | 高 | ⭐⭐ |

---

## 推荐方案：文件监听 + 通知

### 架构图

```
┌─────────────────┐         ┌──────────────────┐
│   Web 端        │         │  桌面工具        │
│  (FastAPI)      │         │  (PySide6)       │
└────────┬────────┘         └────────┬─────────┘
         │                           │
         │ 1. 上传配置               │
         ▼                           │
┌─────────────────────────────────┐  │
│  共享文件系统                    │  │
│  chips/{chip_id}/               │  │
│    ├── batch_scripts/           │  │
│    └── versions/                │  │
└────────┬────────────────────────┘  │
         │                           │
         │ 2. 文件变更事件           │
         └──────────────────────────►│
                                     │
                                     ▼
                            ┌────────────────┐
                            │ QFileSystemWatcher │
                            │ 监听 chips/ 目录   │
                            └────────┬───────┘
                                     │
                                     ▼
                            ┌────────────────┐
                            │ 弹出通知对话框  │
                            │ "新配置已上传"  │
                            └────────────────┘
```

---

## 实现步骤

### Step 1: 在桌面工具中添加文件监听

**位置**：`Chip_Debug_Tool.py` 的 `__init__` 方法

```python
from PySide6.QtCore import QFileSystemWatcher

class MainWindow(QMainWindow, Ui_chip_debug_tool):
    # 添加新信号
    config_file_changed_signal = Signal(str, str)  # (chip_id, file_path)
    
    def __init__(self):
        super().__init__()
        # ... 现有初始化代码 ...
        
        # 初始化文件监听器
        self._init_config_file_watcher()
        
        # 连接信号
        self.config_file_changed_signal.connect(self._on_config_file_changed)
    
    def _init_config_file_watcher(self):
        """初始化配置文件监听器"""
        self.config_watcher = QFileSystemWatcher(self)
        
        # 监听 chips 目录
        chips_dir = HOME_DIR / "chips"
        if chips_dir.exists():
            # 监听所有芯片的 batch_scripts 和 versions 目录
            for chip_dir in chips_dir.iterdir():
                if chip_dir.is_dir():
                    batch_scripts_dir = chip_dir / "batch_scripts"
                    versions_dir = chip_dir / "versions"
                    
                    if batch_scripts_dir.exists():
                        self.config_watcher.addPath(str(batch_scripts_dir))
                    if versions_dir.exists():
                        self.config_watcher.addPath(str(versions_dir))
        
        # 连接目录变更信号
        self.config_watcher.directoryChanged.connect(self._on_directory_changed)
        self.config_watcher.fileChanged.connect(self._on_file_changed)
        
        logger_main.info(f"Config file watcher initialized, monitoring {len(self.config_watcher.directories())} directories")
    
    def _on_directory_changed(self, path: str):
        """目录内容变更回调"""
        path_obj = Path(path)
        
        # 判断是哪个芯片的目录
        chip_id = path_obj.parent.name
        
        # 发射信号到主线程
        self.config_file_changed_signal.emit(chip_id, path)
        
        logger_main.info(f"Directory changed: {path} (chip: {chip_id})")
    
    def _on_file_changed(self, path: str):
        """文件变更回调"""
        path_obj = Path(path)
        chip_id = path_obj.parent.parent.name
        
        self.config_file_changed_signal.emit(chip_id, path)
        
        logger_main.info(f"File changed: {path} (chip: {chip_id})")
    
    @Slot(str, str)
    def _on_config_file_changed(self, chip_id: str, file_path: str):
        """处理配置文件变更（主线程）"""
        # 弹出通知
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Information)
        msg.setWindowTitle("配置更新通知")
        msg.setText(f"芯片 {chip_id} 的配置已更新")
        msg.setInformativeText(f"文件路径：{file_path}\n\n是否重新加载配置？")
        msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        msg.setDefaultButton(QMessageBox.Yes)
        
        result = msg.exec()
        
        if result == QMessageBox.Yes:
            # 重新加载配置
            self._reload_chip_config(chip_id)
    
    def _reload_chip_config(self, chip_id: str):
        """重新加载指定芯片的配置"""
        # 如果当前选中的芯片就是更新的芯片，刷新界面
        if hasattr(self, 'current_chip_id') and self.current_chip_id == chip_id:
            # 重新加载批处理脚本列表
            self._load_batch_scripts_for_chip(chip_id)
            
            # 显示状态栏消息
            self.status_message_signal.emit(f"已重新加载 {chip_id} 的配置", 3000)
            
            logger_main.info(f"Reloaded config for chip: {chip_id}")
```

---

### Step 2: 优化通知体验

**问题**：每次文件变更都弹窗会很烦。

**优化方案**：

1. **状态栏通知** - 不打断用户操作
2. **批量合并** - 5 秒内的多次变更合并为一次通知
3. **可配置** - 用户可以关闭通知

```python
class MainWindow(QMainWindow, Ui_chip_debug_tool):
    def __init__(self):
        # ... 现有代码 ...
        
        # 配置变更通知队列
        self._pending_config_changes = {}  # {chip_id: timestamp}
        self._config_change_timer = QTimer(self)
        self._config_change_timer.timeout.connect(self._process_pending_config_changes)
        self._config_change_timer.setInterval(5000)  # 5 秒合并窗口
    
    def _on_config_file_changed(self, chip_id: str, file_path: str):
        """处理配置文件变更（主线程）- 优化版"""
        # 记录变更
        self._pending_config_changes[chip_id] = time.time()
        
        # 启动定时器（如果未启动）
        if not self._config_change_timer.isActive():
            self._config_change_timer.start()
        
        # 状态栏即时提示
        self.status_message_signal.emit(
            f"检测到 {chip_id} 配置更新...", 
            2000
        )
    
    def _process_pending_config_changes(self):
        """处理待处理的配置变更"""
        if not self._pending_config_changes:
            self._config_change_timer.stop()
            return
        
        # 获取所有变更的芯片
        changed_chips = list(self._pending_config_changes.keys())
        self._pending_config_changes.clear()
        
        # 停止定时器
        self._config_change_timer.stop()
        
        # 显示汇总通知
        if len(changed_chips) == 1:
            chip_id = changed_chips[0]
            message = f"芯片 {chip_id} 的配置已更新"
        else:
            message = f"{len(changed_chips)} 个芯片的配置已更新：\n" + "\n".join(changed_chips)
        
        # 使用状态栏 + 可选弹窗
        self.status_message_signal.emit(message, 5000)
        
        # 如果用户启用了弹窗通知
        if self.settings.value("notifications/config_update", True, type=bool):
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Information)
            msg.setWindowTitle("配置更新通知")
            msg.setText(message)
            msg.setInformativeText("是否重新加载配置？")
            msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
            msg.setDefaultButton(QMessageBox.Yes)
            
            # 添加"不再提示"选项
            dont_ask_again = msg.addButton("不再提示", QMessageBox.ActionRole)
            
            result = msg.exec()
            
            if msg.clickedButton() == dont_ask_again:
                self.settings.setValue("notifications/config_update", False)
            elif result == QMessageBox.Yes:
                for chip_id in changed_chips:
                    self._reload_chip_config(chip_id)
```

---

### Step 3: Web 端触发通知（可选）

如果需要 Web 端主动通知桌面工具，可以通过 TCP 自动化接口：

**Web 端代码（FastAPI）**：

```python
import socket
import json

def notify_desktop_tool(chip_id: str, action: str):
    """通知桌面工具配置已更新"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        sock.connect(('127.0.0.1', 9527))
        
        # 发送自定义通知消息
        request = {
            "action": "notify_config_update",
            "chip": chip_id,
            "update_type": action  # "upload", "delete", "modify"
        }
        
        sock.send(json.dumps(request).encode() + b'\n')
        
        # 读取响应
        response = sock.recv(4096)
        sock.close()
        
        return True
    except Exception as e:
        print(f"Failed to notify desktop tool: {e}")
        return False

# 在上传接口中调用
@app.post("/api/upload")
async def upload_config(
    chip_model_id: str,
    module_id: str,
    file: UploadFile
):
    # ... 保存文件逻辑 ...
    
    # 通知桌面工具
    notify_desktop_tool(chip_model_id, "upload")
    
    return {"status": "success"}
```

**桌面工具扩展 TCP 服务器**：

```python
# 在 tcp_automation_server.py 中添加新的 action 处理

def _handle_request(self, payload: dict) -> dict:
    action = payload.get("action")
    
    # ... 现有 action 处理 ...
    
    if action == "notify_config_update":
        chip = payload.get("chip")
        update_type = payload.get("update_type", "unknown")
        
        # 发射信号到主线程
        self.config_update_notification.emit(chip, update_type)
        
        return {
            "ok": True,
            "status": "accepted",
            "message": f"Config update notification received for {chip}"
        }
```

---

## 部署清单

### 1. 修改桌面工具

- [ ] 添加 `QFileSystemWatcher` 初始化代码
- [ ] 添加配置变更信号和槽函数
- [ ] 添加通知合并逻辑
- [ ] 添加用户设置（是否显示通知）
- [ ] 测试文件监听功能

### 2. 修改 Web 端（可选）

- [ ] 找到 Web 端代码仓库
- [ ] 在上传接口添加 TCP 通知调用
- [ ] 测试 TCP 连接

### 3. 测试流程

1. 启动桌面工具
2. 在 Web 端上传配置
3. 验证桌面工具收到通知
4. 验证配置自动重新加载

---

## 风险与注意事项

### 风险

1. **文件系统延迟**：网络文件系统（NFS/SMB）可能有延迟
2. **权限问题**：确保桌面工具有读取 `chips/` 目录的权限
3. **并发冲突**：Web 端和桌面工具同时写入同一文件

### 缓解措施

1. **文件锁**：使用文件锁防止并发写入
2. **重试机制**：文件读取失败时自动重试
3. **版本号**：使用版本号检测冲突

---

## 总结

**最简单的方案**：只需在桌面工具中添加 `QFileSystemWatcher`，监听 `chips/` 目录，无需修改 Web 端。

**最完整的方案**：文件监听 + TCP 通知双保险，确保实时性。

**推荐**：先实现文件监听，验证效果后再考虑是否需要 TCP 通知。
