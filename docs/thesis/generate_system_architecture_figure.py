#!/usr/bin/env python3
"""
Generate PCFPS system architecture diagram: three-column EDIP-style layout.
运维与切换不含 mock-python（仅毕设联调用，不出现在最终架构图）。

Outputs:
  docs/thesis/images/system_architecture.png
  docs/thesis/images/system_architecture.svg

Requires: matplotlib, numpy
"""

from __future__ import annotations

import sys
from pathlib import Path


def configure_fonts() -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    plt.rcParams.update(
        {
            "font.sans-serif": [
                "PingFang SC",
                "Heiti SC",
                "Songti SC",
                "Arial Unicode MS",
                "Noto Sans CJK SC",
                "SimHei",
                "DejaVu Sans",
            ],
            "axes.unicode_minus": False,
            "figure.dpi": 150,
            "savefig.dpi": 300,
            "savefig.bbox": "tight",
            "savefig.pad_inches": 0.3,
        }
    )


def _teal_blue_cmap():
    from matplotlib.colors import LinearSegmentedColormap

    return LinearSegmentedColormap.from_list("teal_blue", ["#0f766e", "#0e7490", "#0369a1", "#075985"], N=256)


def draw_architecture(output_dir: Path) -> None:
    import matplotlib.pyplot as plt
    import numpy as np
    from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

    figure_width = 20.5
    figure_height = 13.0
    fig, ax = plt.subplots(figsize=(figure_width, figure_height))

    axis_width = 20.8
    axis_height = 14.0
    ax.set_xlim(0, axis_width)
    ax.set_ylim(0, axis_height)
    ax.axis("off")
    fig.patch.set_facecolor("#f8fafc")
    ax.set_facecolor("#f8fafc")

    cmap = _teal_blue_cmap()
    content_z = 12
    arrow_z = 4
    foot_z = 28

    def outer_panel(left: float, bottom: float, width: float, height: float, title: str) -> None:
        rect = FancyBboxPatch(
            (left, bottom),
            width,
            height,
            boxstyle="round,pad=0.02,rounding_size=0.16",
            linewidth=1.5,
            edgecolor="#7dd3fc",
            facecolor="#e8eef5",
            zorder=1,
        )
        ax.add_patch(rect)
        ax.text(
            left + width / 2,
            bottom + height - 0.3,
            title,
            ha="center",
            va="top",
            fontsize=17.2,
            fontweight="bold",
            color="#0c4a6e",
            zorder=content_z,
        )

    def dashed_group(left: float, bottom: float, width: float, height: float, subtitle: str = "") -> None:
        rect = FancyBboxPatch(
            (left, bottom),
            width,
            height,
            boxstyle="round,pad=0.018,rounding_size=0.12",
            linewidth=1.2,
            edgecolor="#38bdf8",
            facecolor="none",
            linestyle=(0, (6, 4)),
            zorder=3,
        )
        ax.add_patch(rect)
        if subtitle:
            ax.text(
                left + 0.11,
                bottom + height - 0.15,
                subtitle,
                ha="left",
                va="top",
                fontsize=12.8,
                color="#0369a1",
                fontweight="semibold",
                zorder=content_z,
            )

    def gray_pill(cx: float, cy: float, width: float, height: float, text: str) -> None:
        rect = FancyBboxPatch(
            (cx - width / 2, cy - height / 2),
            width,
            height,
            boxstyle="round,pad=0.02,rounding_size=0.16",
            linewidth=0,
            facecolor="#64748b",
            zorder=content_z,
        )
        ax.add_patch(rect)
        ax.text(
            cx,
            cy,
            text,
            ha="center",
            va="center",
            fontsize=13.8,
            color="white",
            fontweight="semibold",
            zorder=content_z + 1,
        )

    def gradient_column(
        left: float,
        bottom: float,
        width: float,
        height: float,
        title: str,
        pill_text_list: list[str],
    ) -> None:
        gradient_array = np.linspace(0, 1, 500).reshape(-1, 1)
        ax.imshow(
            gradient_array,
            extent=[left, left + width, bottom, bottom + height],
            origin="lower",
            cmap=cmap,
            aspect="auto",
            zorder=2,
            interpolation="bilinear",
        )
        border = FancyBboxPatch(
            (left, bottom),
            width,
            height,
            boxstyle="round,pad=0.02,rounding_size=0.14",
            linewidth=1.65,
            edgecolor="#bae6fd",
            facecolor="none",
            zorder=3,
        )
        ax.add_patch(border)
        title_band = 0.76
        ax.text(
            left + width / 2,
            bottom + height - 0.3,
            title,
            ha="center",
            va="top",
            fontsize=14.6,
            color="white",
            fontweight="bold",
            zorder=content_z,
        )
        pill_count = len(pill_text_list)
        margin_x = 0.1
        pill_width = width - 2 * margin_x
        inner_top = bottom + height - title_band - 0.12
        inner_bottom = bottom + 0.14
        usable = max(0.45, inner_top - inner_bottom)
        pill_gap = 0.15
        if pill_count <= 0:
            return
        pill_height = min(0.88, (usable - (pill_count - 1) * pill_gap) / pill_count)
        pill_height = max(0.58, pill_height)
        total_stack = pill_count * pill_height + (pill_count - 1) * pill_gap
        y_top_edge = inner_bottom + (usable - total_stack) / 2 + total_stack
        for index, pill_text in enumerate(pill_text_list):
            pill_center_y = y_top_edge - pill_height / 2 - index * (pill_height + pill_gap)
            prect = FancyBboxPatch(
                (left + margin_x, pill_center_y - pill_height / 2),
                pill_width,
                pill_height,
                boxstyle="round,pad=0.018,rounding_size=0.11",
                linewidth=0.65,
                edgecolor="#e0f2fe",
                facecolor="white",
                zorder=content_z,
            )
            ax.add_patch(prect)
            ax.text(
                left + width / 2,
                pill_center_y,
                pill_text,
                ha="center",
                va="center",
                fontsize=13.2,
                color="#0e7490",
                zorder=content_z + 1,
            )

    def dark_header(left: float, bottom: float, width: float, height: float, text: str) -> None:
        rect = FancyBboxPatch(
            (left, bottom),
            width,
            height,
            boxstyle="round,pad=0.02,rounding_size=0.11",
            linewidth=0,
            facecolor="#334155",
            zorder=content_z,
        )
        ax.add_patch(rect)
        ax.text(
            left + width / 2,
            bottom + height / 2,
            text,
            ha="center",
            va="center",
            fontsize=13.2,
            color="white",
            fontweight="bold",
            zorder=content_z + 1,
        )

    def white_pill(cx: float, cy: float, width: float, height: float, text: str) -> None:
        rect = FancyBboxPatch(
            (cx - width / 2, cy - height / 2),
            width,
            height,
            boxstyle="round,pad=0.02,rounding_size=0.13",
            linewidth=0.75,
            edgecolor="#cbd5e1",
            facecolor="white",
            zorder=content_z,
        )
        ax.add_patch(rect)
        ax.text(cx, cy, text, ha="center", va="center", fontsize=13.2, color="#334155", zorder=content_z + 1)

    ax.text(
        axis_width / 2,
        axis_height - 0.34,
        "PCFPS 点云滤波系统总体架构",
        ha="center",
        va="bottom",
        fontsize=22.5,
        fontweight="bold",
        color="#0c4a6e",
        zorder=content_z + 2,
    )

    column_gap = 0.22
    left_x = 0.22
    left_w = 3.65
    mid_x = left_x + left_w + column_gap
    mid_w = axis_width - mid_x - column_gap - 3.65
    right_x = mid_x + mid_w + column_gap
    right_w = 3.65
    panel_bottom = 0.62
    panel_h = 11.45

    outer_panel(left_x, panel_bottom, left_w, panel_h, "接入与用户")
    outer_panel(mid_x, panel_bottom, mid_w, panel_h, "核心服务与计算")
    outer_panel(right_x, panel_bottom, right_w, panel_h, "展示与交付")

    inner_margin = 0.14
    lx = left_x + inner_margin
    lw = left_w - 2 * inner_margin
    inner_floor = panel_bottom + 0.54
    inner_ceiling = panel_bottom + panel_h - 0.75
    group_gap = 0.28
    group_count = 3
    group_height = (inner_ceiling - inner_floor - (group_count - 1) * group_gap) / group_count

    left_blocks = [
        ("认证与任务", ["JWT 登录", "新建滤波任务", "派生分割 / 分类"]),
        ("数据入口", ["LAS 路径登记", "preview 请求", "bundle 查询"]),
        ("运维与切换", ["真实网关 (HTTP)", "环境变量配置"]),
    ]
    for group_index, (subtitle, pill_labels) in enumerate(left_blocks):
        group_bottom = inner_floor + group_index * (group_height + group_gap)
        dashed_group(lx, group_bottom, lw, group_height, subtitle)
        subtitle_reserve = 0.56
        pill_area_top = group_bottom + group_height - subtitle_reserve
        pill_area_bottom = group_bottom + 0.16
        pill_count = len(pill_labels)
        pill_gap_local = 0.15
        usable_height = pill_area_top - pill_area_bottom
        pill_height = min(0.84, (usable_height - (pill_count - 1) * pill_gap_local) / pill_count)
        pill_height = max(0.58, pill_height)
        stack = pill_count * pill_height + (pill_count - 1) * pill_gap_local
        start_top = pill_area_bottom + (usable_height - stack) / 2 + stack
        for pill_index, label in enumerate(pill_labels):
            center_y = start_top - pill_height / 2 - pill_index * (pill_height + pill_gap_local)
            gray_pill(lx + lw / 2, center_y, lw - 0.14, pill_height, label)

    mx0 = mid_x + 0.16
    col_gap = 0.13
    col_w = (mid_w - 0.32 - 3 * col_gap) / 4
    row2_bottom = panel_bottom + 0.58
    row2_h = 4.1
    row_gap = 0.28
    row1_bottom = row2_bottom + row2_h + row_gap
    row1_h = max(5.65, inner_ceiling - row1_bottom)

    gradient_column(
        mx0,
        row1_bottom,
        col_w,
        row1_h,
        "前端应用",
        ["Vite + React + TypeScript", "Ant Design 布局 / 表单", "Three.js 点云预览", "双窗与路由"],
    )
    gradient_column(
        mx0 + col_w + col_gap,
        row1_bottom,
        col_w,
        row1_h,
        "Spring Boot",
        ["REST API", "JWT 鉴权", "任务状态机", "WebClient 调度"],
    )
    gradient_column(
        mx0 + 2 * (col_w + col_gap),
        row1_bottom,
        col_w,
        row1_h,
        "数据持久化",
        ["PostgreSQL", "filter_task / file_asset", "JSONB 参数与指标", "JDBC"],
    )
    gradient_column(
        mx0 + 3 * (col_w + col_gap),
        row1_bottom,
        col_w,
        row1_h,
        "python_gateway",
        ["FastAPI", "POST /jobs", "POST /derived-jobs", "GET 轮询状态"],
    )

    gradient_column(
        mx0,
        row2_bottom,
        col_w,
        row2_h,
        "python_filter",
        ["SOR / ROR", "laspy + numpy", "cKDTree / BallTree"],
    )
    gradient_column(
        mx0 + col_w + col_gap,
        row2_bottom,
        col_w,
        row2_h,
        "python_derived",
        ["分割 / 分类算法", "derived.las 写出"],
    )
    gradient_column(
        mx0 + 2 * (col_w + col_gap),
        row2_bottom,
        col_w,
        row2_h,
        "磁盘产物",
        ["input LAS", "filtered.las", "指标与日志"],
    )
    gradient_column(
        mx0 + 3 * (col_w + col_gap),
        row2_bottom,
        col_w,
        row2_h,
        "预览管线",
        ["preview-points", "LAS 子进程抽稀", "JSON 下发"],
    )

    rx = right_x + inner_margin
    rw = right_w - 2 * inner_margin
    right_sections = [
        ("可视化", ["双窗对比", "JSON 点云渲染", "classification 伪彩色"]),
        ("产物与指标", ["runMetrics", "metrics_bundle", "输出目录"]),
        ("交互角色", ["单角色登录", "毕设演示账号"]),
    ]
    right_floor = inner_floor
    right_ceiling = inner_ceiling
    right_gap = 0.32
    right_header_h = 0.74
    section_count_right = len(right_sections)
    right_span = right_ceiling - right_floor - (section_count_right - 1) * right_gap
    section_height_right = right_span / section_count_right
    pill_gap_r = 0.15
    for section_index, (header_text, pills) in enumerate(right_sections):
        section_bottom = right_floor + section_index * (section_height_right + right_gap)
        dark_header(rx, section_bottom + section_height_right - right_header_h, rw, right_header_h, header_text)
        pill_area_bottom = section_bottom + 0.12
        pill_area_top = section_bottom + section_height_right - right_header_h - 0.12
        pill_n = len(pills)
        usable_r = pill_area_top - pill_area_bottom
        if pill_n <= 0:
            continue
        ph = min(0.86, (usable_r - (pill_n - 1) * pill_gap_r) / pill_n)
        ph = max(0.58, ph)
        stack_r = pill_n * ph + (pill_n - 1) * pill_gap_r
        y_top_r = pill_area_bottom + (usable_r - stack_r) / 2 + stack_r
        for pill_index, pill_label in enumerate(pills):
            cy = y_top_r - ph / 2 - pill_index * (ph + pill_gap_r)
            white_pill(rx + rw / 2, cy, rw - 0.12, ph, pill_label)

    for y_line in (row1_bottom + row1_h * 0.55, row1_bottom + row1_h * 0.3, row2_bottom + row2_h * 0.52):
        arr = FancyArrowPatch(
            (left_x + left_w - 0.04, y_line),
            (mid_x + 0.1, y_line),
            arrowstyle="-|>",
            mutation_scale=17,
            linewidth=1.25,
            color="#94a3b8",
            linestyle=(0, (5, 4)),
            zorder=arrow_z,
        )
        ax.add_patch(arr)
    for y_line in (row1_bottom + row1_h * 0.52, row2_bottom + row2_h * 0.55):
        arr = FancyArrowPatch(
            (mid_x + mid_w - 0.08, y_line),
            (right_x + 0.06, y_line),
            arrowstyle="-|>",
            mutation_scale=17,
            linewidth=1.25,
            color="#94a3b8",
            linestyle=(0, (5, 4)),
            zorder=arrow_z,
        )
        ax.add_patch(arr)

    foot = FancyBboxPatch(
        (0.18, 0.08),
        axis_width - 0.36,
        0.44,
        boxstyle="round,pad=0.02,rounding_size=0.1",
        facecolor="#e2e8f0",
        edgecolor="#cbd5e1",
        linewidth=0.85,
        zorder=foot_z,
    )
    ax.add_patch(foot)
    ax.text(
        axis_width / 2,
        0.3,
        "三栏：接入侧 | 编排与算法（HTTP + JDBC + 磁盘）| 展示侧；全精度 LAS 在磁盘，浏览器仅加载抽稀 JSON",
        ha="center",
        va="center",
        fontsize=11.0,
        color="#475569",
        zorder=foot_z + 1,
    )

    out_png = output_dir / "system_architecture.png"
    out_svg = output_dir / "system_architecture.svg"
    fig.savefig(out_png)
    fig.savefig(out_svg)
    plt.close(fig)


def main() -> int:
    repo_root = Path(__file__).resolve().parents[2]
    output_dir = repo_root / "docs" / "thesis" / "images"
    output_dir.mkdir(parents=True, exist_ok=True)

    try:
        configure_fonts()
    except ImportError:
        print("matplotlib is required: pip install matplotlib", file=sys.stderr)
        return 1

    try:
        import numpy as np  # noqa: F401
    except ImportError:
        print("numpy is required: pip install numpy", file=sys.stderr)
        return 1

    draw_architecture(output_dir)
    print("Wrote:")
    print(" ", output_dir / "system_architecture.png")
    print(" ", output_dir / "system_architecture.svg")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
