# CHM Converter

<div align="center">

🔄 将 CHM (Microsoft Compiled HTML Help) 文件转换为现代化静态网站

[功能特点](#功能特点) • [快速开始](#快速开始) • [使用说明](#使用说明) • [示例](#示例)

</div>

---

## 功能特点

✨ **智能转换**
- 自动解析 CHM 文件的目录结构（`.hhc`）
- 保留原始样式和布局
- 支持嵌套目录和章节

🎨 **现代界面**
- 响应式设计，支持桌面和移动设备
- 可折叠的侧边栏目录树
- 自动检测并支持明暗主题切换（如果原CHM支持）

🔍 **强大搜索**
- 全文搜索功能
- 实时搜索结果预览
- 支持中文搜索

📦 **完整资源**
- 自动复制所有图片、CSS等资源文件
- 保持原始文件路径结构
- 支持 GB18030/GBK 中文编码

## 系统要求

- **Python**: 3.8 或更高版本
- **7-Zip**: 用于解压 CHM 文件 ([下载地址](https://www.7-zip.org/))

## 快速开始

### 1. 克隆仓库

```bash
git clone https://github.com/yourusername/CHM_Conveter.git
cd CHM_Conveter
```

### 2. 安装依赖

```bash
# 创建虚拟环境（推荐）
python -m venv .venv

# 激活虚拟环境
# Windows:
.venv\Scripts\activate
# Linux/Mac:
source .venv/bin/activate

# 安装依赖包
pip install -r requirements.txt
```

### 3. 转换 CHM 文件

```bash
python main.py 输入文件.chm 输出目录
```

### 4. 查看结果

在输出目录中打开 `index.html` 文件即可查看转换后的网站。

## 使用说明

### 基本用法

```bash
# 转换单个CHM文件
python main.py input.chm output/

# 使用模块方式运行
python -m chm_converter input.chm output/

# 自定义网站标题
python main.py input.chm output/ --title "我的帮助文档"

# 安静模式（减少输出）
python main.py input.chm output/ -q
```

### 命令行选项

```
用法: python main.py <chm_path> <output_dir> [选项]

参数:
  chm_path              CHM文件路径
  output_dir            输出目录路径

选项:
  -t, --title TITLE    自定义网站标题（默认从CHM文件提取）
  -q, --quiet          安静模式，减少输出信息
  -v, --version        显示版本信息
  -h, --help           显示帮助信息
```

## 示例

### 转换帮助文档

```bash
python main.py "C:\docs\UserGuide.chm" "D:\website\guide"
```

转换完成后，会生成以下结构：

```
D:\website\guide\
├── index.html          # 主页面（在浏览器中打开此文件）
├── assets/             # 前端资源
│   ├── style.css
│   ├── app.js
│   ├── tree-data.js
│   └── search-index.js
└── content/            # 文档内容
    ├── *.html
    ├── *.css
    └── Images/
```

### 本地预览

转换完成后，可以使用 Python 内置的 HTTP 服务器预览：

```bash
cd output
python -m http.server 8000
```

然后在浏览器中访问 `http://localhost:8000`

## 特性说明

### 智能主题检测

转换器会自动检测 CHM 文件中是否包含明暗主题的 CSS 文件：
- 如果同时存在 `lesson_light.css` 和 `lesson_dark.css`，则启用主题切换按钮
- 如果只有单一主题，则隐藏主题切换按钮
- 保留原始 CHM 的所有样式定义

### 目录树交互

- **可点击目录项**：如果目录本身有内容，点击标题查看内容
- **可展开子项**：点击箭头图标展开/折叠子目录
- **自动定位**：点击内容后自动展开相关父级目录

### 搜索功能

- 输入 2 个或以上字符开始搜索
- 搜索结果显示标题和内容预览
- 点击搜索结果直接跳转到对应页面

## 常见问题

**Q: 提示找不到 7-Zip？**

A: 请确保已安装 7-Zip，程序会自动查找以下路径：
- `C:\Program Files\7-Zip\7z.exe`
- `C:\Program Files (x86)\7-Zip\7z.exe`

或者将 7-Zip 的安装目录添加到系统 PATH 环境变量。

**Q: 转换后的网页样式不正确？**

A: 本工具会保留 CHM 的原始样式。如果原 CHM 文件的样式定义有问题，转换后也会保留这些问题。

**Q: 图片无法显示？**

A: 确保使用 HTTP 服务器访问网站（如 `python -m http.server`），而不是直接双击打开 HTML 文件，因为浏览器的跨域安全策略可能会阻止本地文件访问。

**Q: 支持哪些 CHM 文件？**

A: 支持标准的 Microsoft CHM 格式，特别是包含 `.hhc` 目录文件的 CHM。对于中文 CHM，自动支持 GB18030、GBK、GB2312 等编码。

## 贡献

欢迎提交 Issue 和 Pull Request！

## 许可证

MIT License

---

<div align="center">

Made with ❤️ by the CHM Converter Team

</div>
