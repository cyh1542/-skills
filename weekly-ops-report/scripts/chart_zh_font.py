#!/usr/bin/env python3
"""matplotlib/seaborn 中文图表：用字体文件路径绑定，避免仅设 rcParams 仍回退到 Arial。"""
from __future__ import annotations

import sys
import warnings
from pathlib import Path

import matplotlib
from matplotlib import font_manager
from matplotlib.font_manager import FontProperties

WINDOWS_FONT_FILES = [
    Path(r"C:\Windows\Fonts\msyh.ttc"),
    Path(r"C:\Windows\Fonts\msyhbd.ttc"),
    Path(r"C:\Windows\Fonts\simhei.ttf"),
    Path(r"C:\Windows\Fonts\msyhl.ttc"),
]

MACOS_FONT_FILES = [
    Path("/System/Library/Fonts/PingFang.ttc"),
    Path("/System/Library/Fonts/Supplemental/Songti.ttc"),
    Path("/Library/Fonts/Arial Unicode.ttf"),
]

LINUX_FONT_FILES = [
    Path("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"),
    Path("/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc"),
    Path("/usr/share/fonts/google-noto-cjk/NotoSansCJK-Regular.ttc"),
    Path("/usr/share/fonts/noto-cjk/NotoSansCJK-Regular.ttc"),
]

CJK_FONT_FILE_CANDIDATES = WINDOWS_FONT_FILES + MACOS_FONT_FILES + LINUX_FONT_FILES

CJK_FONT_NAMES = [
    "Microsoft YaHei",
    "Microsoft YaHei UI",
    "SimHei",
    "PingFang SC",
    "Noto Sans CJK SC",
    "Noto Sans SC",
]

_cached_prop: FontProperties | None = None
_cached_name: str | None = None


def resolve_cjk_font_file() -> tuple[str, str]:
    for path in CJK_FONT_FILE_CANDIDATES:
        if path.is_file():
            try:
                font_manager.fontManager.addfont(str(path))
            except Exception:
                pass
            prop = FontProperties(fname=str(path))
            return prop.get_name(), str(path)

    available = {f.name: f.fname for f in font_manager.fontManager.ttflist}
    for name in CJK_FONT_NAMES:
        if name in available:
            return name, available[name]

    for f in font_manager.fontManager.ttflist:
        if any(k in f.name for k in ("YaHei", "SimHei", "PingFang", "Noto Sans SC", "CJK")):
            return f.name, f.fname

    raise RuntimeError(
        "未找到中文字体。Windows 请确认微软雅黑已安装；"
        "macOS/Linux 请安装 Noto Sans CJK SC 或 PingFang SC。"
    )


def get_cjk_font_properties() -> FontProperties:
    global _cached_prop, _cached_name
    if _cached_prop is None:
        name, path = resolve_cjk_font_file()
        _cached_name = name
        _cached_prop = FontProperties(fname=path)
    return _cached_prop


def setup_chinese_chart(style: str = "whitegrid") -> str:
    import seaborn as sns

    name, path = resolve_cjk_font_file()
    prop = FontProperties(fname=path)

    matplotlib.rcParams["font.family"] = "sans-serif"
    matplotlib.rcParams["font.sans-serif"] = [name, "DejaVu Sans"]
    matplotlib.rcParams["axes.unicode_minus"] = False

    sns.set_theme(style=style, font=name)
    matplotlib.rcParams["font.sans-serif"] = [name, "DejaVu Sans"]
    matplotlib.rcParams["axes.unicode_minus"] = False

    global _cached_prop, _cached_name
    _cached_name = name
    _cached_prop = prop

    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
    return name


def apply_cjk_font(ax, fig=None) -> None:
    fp = get_cjk_font_properties()
    if ax.get_title():
        ax.title.set_fontproperties(fp)
    if ax.get_xlabel():
        ax.xaxis.label.set_fontproperties(fp)
    if ax.get_ylabel():
        ax.yaxis.label.set_fontproperties(fp)
    for label in ax.get_xticklabels() + ax.get_yticklabels():
        label.set_fontproperties(fp)
    leg = ax.get_legend()
    if leg:
        for text in leg.get_texts():
            text.set_fontproperties(fp)
    if fig is not None:
        for cax in fig.axes:
            if cax is ax:
                continue
            if hasattr(cax, "get_ylabel"):
                if cax.get_ylabel():
                    cax.set_ylabel(cax.get_ylabel(), fontproperties=fp)
                for label in cax.get_yticklabels():
                    label.set_fontproperties(fp)


def style_axes(ax, title: str, xlabel: str | None = None, ylabel: str | None = None, fig=None) -> None:
    ax.set_title(title)
    if xlabel:
        ax.set_xlabel(xlabel)
    if ylabel:
        ax.set_ylabel(ylabel)
    apply_cjk_font(ax, fig)


if __name__ == "__main__":
    name = setup_chinese_chart()
    print(f"OK: font={name!r} file={get_cjk_font_properties().get_file()}")
    sys.exit(0)
