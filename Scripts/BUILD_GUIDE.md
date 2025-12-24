# AI 作业批改工具 - 打包部署指南

本文档介绍如何将 AI 作业批改工具打包成可执行文件，实现一键启动和源码保护。

## 目录

- [打包方案概述](#打包方案概述)
- [Windows 平台打包](#windows-平台打包)
- [Mac 平台打包](#mac-平台打包)
- [源码保护说明](#源码保护说明)
- [常见问题解答](#常见问题解答)

---

## 打包方案概述

### 技术方案

| 组件 | 技术 | 保护措施 |
|------|------|----------|
| 前端 | Vue3 + Vite | 构建时自动压缩混淆 |
| 后端 | FastAPI + Uvicorn | PyInstaller 编译为字节码 |
| 打包 | PyInstaller | 单目录/单文件模式 |

### 打包产物

- **Windows**: `AI作业批改工具.exe` + 依赖目录
- **Mac**: `AI作业批改工具.app` 或可执行二进制文件

### 运行流程

```
双击可执行文件
    ↓
启动 FastAPI 后端服务
    ↓
自动打开默认浏览器
    ↓
访问前端界面
    ↓
正常使用所有功能
```

---

## Windows 平台打包

### 环境要求

- **Python**: 3.9 或更高版本
- **Node.js**: 16 或更高版本
- **npm**: 随 Node.js 安装

### 打包步骤

#### 方式一：使用一键打包脚本（推荐）

1. 双击运行 `Scripts/build-win.bat`
2. 等待脚本自动完成以下步骤：
   - 检查 Python 环境
   - 安装 PyInstaller
   - 构建前端
   - 打包后端
3. 打包完成后，产物位于 `backend/dist/AI作业批改工具/`

#### 方式二：手动打包

```bash
# 1. 进入虚拟环境（如果有）
cd /path/to/AIHomeworkGrader
.venv\Scripts\activate

# 2. 安装 PyInstaller
pip install pyinstaller

# 3. 构建前端
cd frontend
npm install
npm run build
cd ..

# 4. 打包后端
cd backend
pyinstaller build_config.spec --noconfirm
```

### 分发说明

将 `backend/dist/AI作业批改工具/` 整个目录复制给用户，用户双击 `启动.bat` 或 `AI作业批改工具.exe` 即可运行。

---

## Mac 平台打包

### 环境要求

- **macOS**: 10.14 或更高版本
- **Python**: 3.9 或更高版本
- **Node.js**: 16 或更高版本

### 打包方式

Mac 提供两种打包方式：

| 方式 | 脚本 | 产物 | 适用场景 |
|------|------|------|----------|
| 普通打包 | `build-mac.sh` | 可执行文件 + 依赖目录 | 开发测试 |
| 应用程序包 | `build-mac-app.sh` | `.app` 应用程序 | 正式分发 |

### 方式一：普通打包

```bash
cd Scripts
./build-mac.sh
```

产物位于 `backend/dist/AI作业批改工具/`，双击 `启动.command` 运行。

### 方式二：应用程序包（推荐）

```bash
cd Scripts
./build-mac-app.sh
```

产物为 `backend/dist/AI作业批改工具.app`，可拖入「应用程序」文件夹。

### 首次运行注意事项

由于应用未签名，首次运行时可能被系统拦截：

1. **按住 Control 键**，点击应用程序图标
2. 从弹出菜单中选择「打开」
3. 在确认对话框中点击「打开」

之后可以正常双击启动。

---

## 源码保护说明

### 保护级别

打包后的源码保护分为以下几个层级：

#### 前端代码（高保护）

- Vite 构建时自动进行代码压缩和混淆
- 变量名和函数名被重命名
- 代码结构被重组
- 源码映射文件不包含在产物中

#### 后端代码（中等保护）

- Python 源码编译为 `.pyc` 字节码
- 打包到 PyInstaller 的归档文件中
- 不直接暴露 `.py` 源文件

#### 额外保护建议

如需更高级别的保护，可以考虑：

1. **代码混淆**: 使用 `pyarmor` 加密 Python 代码
   ```bash
   pip install pyarmor
   pyarmor gen --output dist app_launcher.py app/
   ```

2. **Cython 编译**: 将关键模块编译为 C 扩展
   ```bash
   pip install cython
   # 创建 setup.py 并编译
   ```

3. **Nuitka 打包**: 将 Python 编译为原生机器码
   ```bash
   pip install nuitka
   nuitka --standalone --onefile app_launcher.py
   ```

### 安全注意事项

⚠️ **重要提醒**：

- 所有客户端软件都无法做到绝对的源码保护
- 如有严格的知识产权保护需求，建议采用 SaaS 模式将核心逻辑部署在服务器端
- 配置文件（如 API 密钥）应在运行时由用户输入，不要硬编码

---

## 常见问题解答

### 打包相关

**Q: 打包后文件体积太大？**

A: PyInstaller 会包含完整的 Python 运行时和所有依赖。可以尝试：
- 在 spec 文件的 `excludes` 中排除不需要的模块
- 使用 UPX 压缩（默认已启用）
- 使用虚拟环境，只安装必要依赖

**Q: 打包失败，提示找不到模块？**

A: 检查 `build_config.spec` 中的 `hiddenimports` 列表，添加缺失的模块。

**Q: Windows 上打包后杀毒软件报警？**

A: 这是 PyInstaller 的常见问题。可以：
- 添加到杀毒软件白名单
- 使用代码签名证书签署可执行文件

### 运行相关

**Q: 双击无反应或闪退？**

A: 通过命令行运行可执行文件查看错误信息：
```bash
# Windows
cmd /k "AI作业批改工具.exe"

# Mac
./AI作业批改工具
```

**Q: 端口被占用无法启动？**

A: 程序会自动尝试 18088-18187 范围内的端口。如果仍有问题，请关闭占用端口的程序。

**Q: 浏览器没有自动打开？**

A: 手动访问控制台显示的地址，默认为 `http://localhost:18088`

---

## 文件清单

```
Scripts/
├── build-win.bat       # Windows 一键打包脚本
├── build-mac.sh        # Mac 一键打包脚本
├── build-mac-app.sh    # Mac 应用程序包打包脚本
├── start.bat           # Windows 开发启动脚本
├── start.sh            # Mac 开发启动脚本
├── reset-env.bat       # Windows 环境重置脚本
└── reset-env.sh        # Mac 环境重置脚本

backend/
├── app_launcher.py     # 打包入口脚本
├── build_config.spec   # PyInstaller 打包配置
└── dist/               # 打包产物目录
    └── AI作业批改工具/
```

---

## 更新日志

- **2024-12-15**: 初始版本，支持 Windows 和 Mac 平台打包
