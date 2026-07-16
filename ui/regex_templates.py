"""Regex Assistant 内置模板 — 静态数据。

新增模板只需在此文件添加一个条目。
"""

TEMPLATES: list[dict] = [
    # ── Filename Cleanup ──
    {
        "name": "移除数字",
        "category": "文件名清理",
        "pattern": r"\d+",
        "replacement": "",
        "description": "删除文件名中的所有数字。",
        "example_before": "Photo_00123",
        "example_after": "Photo_",
    },
    {
        "name": "移除空白字符",
        "category": "文件名清理",
        "pattern": r"\s+",
        "replacement": "",
        "description": "删除所有空格、制表符、换行。",
        "example_before": "My Photo 2024",
        "example_after": "MyPhoto2024",
    },
    {
        "name": "合并连续空白",
        "category": "文件名清理",
        "pattern": r"\s+",
        "replacement": " ",
        "description": "多个连续空白替换为单个空格。",
        "example_before": "My   Photo   2024",
        "example_after": "My Photo 2024",
    },
    {
        "name": "移除括号及内容",
        "category": "文件名清理",
        "pattern": r"\(.*?\)",
        "replacement": "",
        "description": "删除圆括号及其内部内容。",
        "example_before": "Movie(1080P).mkv",
        "example_after": "Movie.mkv",
    },
    {
        "name": "移除方括号及内容",
        "category": "文件名清理",
        "pattern": r"\[.*?\]",
        "replacement": "",
        "description": "删除方括号及其内部内容。",
        "example_before": "Song[Official].mp3",
        "example_after": "Song.mp3",
    },
    {
        "name": "移除花括号及内容",
        "category": "文件名清理",
        "pattern": r"\{.*?\}",
        "replacement": "",
        "description": "删除花括号及其内部内容。",
        "example_before": "Doc{Draft}.txt",
        "example_after": "Doc.txt",
    },
    {
        "name": "移除前缀 Episode_",
        "category": "文件名清理",
        "pattern": r"^Episode_",
        "replacement": "",
        "description": "删除文件名开头的 Episode_。",
        "example_before": "Episode_01.mkv",
        "example_after": "01.mkv",
    },
    {
        "name": "移除后缀 _final",
        "category": "文件名清理",
        "pattern": r"_final$",
        "replacement": "",
        "description": "删除文件名末尾的 _final。",
        "example_before": "Report_final.pdf",
        "example_after": "Report.pdf",
    },

    # ── Content Extraction ──
    {
        "name": "保留数字",
        "category": "内容提取",
        "pattern": r"\D+",
        "replacement": "",
        "description": "删除所有非数字字符，只保留数字。",
        "example_before": "IMG_0042.jpg",
        "example_after": "0042.jpg",
    },
    {
        "name": "保留英文字母",
        "category": "内容提取",
        "pattern": r"[^a-zA-Z]",
        "replacement": "",
        "description": "删除所有非英文字母。",
        "example_before": "Song01-歌手.mp3",
        "example_after": "Song.mp3",
    },
    {
        "name": "保留中文字符",
        "category": "内容提取",
        "pattern": r"[^\u4e00-\u9fff]",
        "replacement": "",
        "description": "删除所有非中文字符。",
        "example_before": "ABC歌手123.mp3",
        "example_after": "歌手.mp3",
    },

    # ── Advanced ──
    {
        "name": "捕获组替换",
        "category": "高级",
        "pattern": r"(\w+)_(\d+)",
        "replacement": r"\2_\1",
        "description": "交换下划线前后的内容（捕获组重排）。",
        "example_before": "Photo_001.jpg",
        "example_after": "001_Photo.jpg",
    },
    {
        "name": "提取集数编号",
        "category": "高级",
        "pattern": r".*?(\d+)",
        "replacement": r"\1",
        "description": "提取文件名中第一组数字作为新名称。",
        "example_before": "EP_05_Title.mkv",
        "example_after": "05.mkv",
    },
]
