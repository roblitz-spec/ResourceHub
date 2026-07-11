# ResourceHub 构建指南

## 环境要求

- Python 3.12+
- Windows（目标平台）、Linux 或 macOS（开发平台）

## 安装依赖

```bash
pip install -r requirements.txt
```

## 构建

```bash
python scripts/build.py
```

构建成功后输出：

```
dist/ResourceHub/ResourceHub.exe    (Windows)
dist/ResourceHub/ResourceHub        (Linux/macOS)
```

## 手动构建

```bash
pyinstaller build.spec
```

## 运行

直接双击 `dist/ResourceHub/ResourceHub.exe`（Windows），或终端执行：

```bash
dist/ResourceHub/ResourceHub
```

## 包含资源

- `translations/` — 中文/英文语言文件
