#!/usr/bin/env python3
"""
PCFPS 系统结构树状图（参考：顶层竖链 + 横杆分叉 + 底层竖排字），
内容严格对应本仓库已实现/设计文档中的模块与术语，不填入与本系统无关的算法名。

底层叶子：每个框内文字为「一字一行」竖排（换行连接字符），不用整句旋转。

Outputs:
  docs/thesis/images/point_cloud_processing_tree.png
  docs/thesis/images/point_cloud_processing_tree.svg

Requires: matplotlib
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
            "savefig.pad_inches": 0.2,
        }
    )


def stack_chars_vertically(label: str) -> str:
    """One non-whitespace character per line (top-to-bottom), for leaf boxes."""
    character_list = [character for character in list(label) if not character.isspace()]
    return "\n".join(character_list)


def measure_text_size_data_units(
    axis,
    figure,
    text_content: str,
    fontsize: float,
    *,
    rotation_degrees: float,
    linespacing: float | None,
) -> tuple[float, float]:
    kwargs = {
        "fontsize": fontsize,
        "rotation": rotation_degrees,
        "ha": "center",
        "va": "center",
        "visible": False,
    }
    if linespacing is not None:
        kwargs["linespacing"] = linespacing
    text_artist = axis.text(0.0, 0.0, text_content, **kwargs)
    figure.canvas.draw()
    renderer = figure.canvas.get_renderer()
    window_bbox = text_artist.get_window_extent(renderer=renderer)
    bbox_data = window_bbox.transformed(axis.transData.inverted())
    text_artist.remove()
    return abs(bbox_data.width), abs(bbox_data.height)


def draw_processing_tree(output_dir: Path) -> None:
    import matplotlib.pyplot as plt
    from matplotlib.patches import FancyArrowPatch, Rectangle

    # PCFPS: root -> Java 编排 -> 协同层 -> 五个并列子系统 -> 各子项（竖排字）
    root_title = "PCFPS 点云滤波自动化系统"
    layer2_title = "Spring Boot 编排与持久化"
    layer3_title = "前端与 Python 协同"
    category_leaf_rows: list[tuple[str, list[str]]] = [
        (
            "前端应用",
            ["Vite + React", "Three.js 预览", "双窗与路由", "Ant Design"],
        ),
        (
            "鉴权与任务",
            ["JWT 登录", "滤波任务", "派生作业", "任务状态机"],
        ),
        (
            "数据持久化",
            ["PostgreSQL", "filter_task", "file_asset", "JSONB"],
        ),
        (
            "Python 服务",
            ["FastAPI", "POST /jobs", "SOR / ROR", "laspy 分块读"],
        ),
        (
            "产物与预览",
            ["filtered.las", "preview JSON", "comparison-bundle", "runMetrics"],
        ),
    ]

    font_root = 15.0
    font_chain = 13.5
    font_category = 11.8
    font_leaf = 9.8
    line_width = 1.05
    box_edge = "black"
    linespacing_tight = 0.95

    figure_width = 15.0
    figure_height = 18.5
    figure, axis = plt.subplots(figsize=(figure_width, figure_height))

    axis_width = 13.0
    axis_height = 20.0
    axis.set_xlim(0, axis_width)
    axis.set_ylim(0, axis_height)
    axis.axis("off")
    figure.patch.set_facecolor("white")
    axis.set_facecolor("white")

    def measure_horizontal(label: str, fontsize: float) -> tuple[float, float]:
        return measure_text_size_data_units(
            axis,
            figure,
            label,
            fontsize,
            rotation_degrees=0,
            linespacing=None,
        )

    def measure_vertical_stack(label: str, fontsize: float) -> tuple[float, float]:
        stacked = stack_chars_vertically(label)
        return measure_text_size_data_units(
            axis,
            figure,
            stacked,
            fontsize,
            rotation_degrees=0,
            linespacing=linespacing_tight,
        )

    # Tight padding (data units): keep border close to glyphs
    pad_x_chain = 0.1
    pad_y_chain = 0.08
    pad_x_leaf = 0.06
    pad_y_leaf = 0.05

    def draw_horizontal_box_tight(center_x: float, center_y: float, label: str, fontsize: float) -> tuple[float, float]:
        text_width, text_height = measure_horizontal(label, fontsize)
        box_width = text_width + 2 * pad_x_chain
        box_height = text_height + 2 * pad_y_chain
        left = center_x - box_width / 2
        bottom = center_y - box_height / 2
        rect = Rectangle(
            (left, bottom),
            box_width,
            box_height,
            facecolor="white",
            edgecolor=box_edge,
            linewidth=line_width,
            zorder=2,
        )
        axis.add_patch(rect)
        axis.text(center_x, center_y, label, ha="center", va="center", fontsize=fontsize, color="black", zorder=3)
        bottom_edge_y = center_y - box_height / 2
        top_edge_y = center_y + box_height / 2
        return bottom_edge_y, top_edge_y

    def draw_down_arrow(x_start: float, y_start: float, x_end: float, y_end: float) -> None:
        arrow = FancyArrowPatch(
            (x_start, y_start),
            (x_end, y_end),
            arrowstyle="-|>",
            mutation_scale=12,
            linewidth=line_width,
            color="black",
            linestyle="solid",
            zorder=1,
        )
        axis.add_patch(arrow)

    def draw_vertical_double_arrow(center_x: float, y_low: float, y_high: float) -> None:
        arrow = FancyArrowPatch(
            (center_x, y_low),
            (center_x, y_high),
            arrowstyle="<|-|>",
            mutation_scale=11,
            linewidth=line_width,
            color="black",
            zorder=1,
        )
        axis.add_patch(arrow)

    center_x = axis_width / 2
    margin_top = 0.38

    _, root_text_h = measure_horizontal(root_title, font_root)
    root_box_height = root_text_h + 2 * pad_y_chain
    root_center_y = axis_height - margin_top - root_box_height / 2
    root_bottom_y, root_top_y = draw_horizontal_box_tight(center_x, root_center_y, root_title, font_root)

    gap_after_root = 0.42
    _, layer2_text_h = measure_horizontal(layer2_title, font_chain)
    layer2_box_height = layer2_text_h + 2 * pad_y_chain
    layer2_center_y = root_bottom_y - gap_after_root - layer2_box_height / 2
    draw_down_arrow(center_x, root_bottom_y - 0.02, center_x, layer2_center_y + layer2_box_height / 2 + 0.02)
    layer2_bottom_y, layer2_top_y = draw_horizontal_box_tight(center_x, layer2_center_y, layer2_title, font_chain)

    double_gap = 0.3
    _, layer3_text_h = measure_horizontal(layer3_title, font_chain)
    layer3_box_height = layer3_text_h + 2 * pad_y_chain
    layer3_center_y = layer2_bottom_y - double_gap - layer3_box_height / 2
    layer3_top_y = layer3_center_y + layer3_box_height / 2
    layer2_bottom_edge_y = layer2_center_y - layer2_box_height / 2
    draw_vertical_double_arrow(center_x, layer3_top_y + 0.04, layer2_bottom_edge_y - 0.04)
    layer3_bottom_y, layer3_top_y = draw_horizontal_box_tight(center_x, layer3_center_y, layer3_title, font_chain)

    branch_drop = 0.55
    rail_y = layer3_bottom_y - branch_drop
    draw_down_arrow(center_x, layer3_bottom_y - 0.02, center_x, rail_y + 0.06)

    category_count = len(category_leaf_rows)
    margin_x = 0.35
    usable_x1 = margin_x
    usable_x2 = axis_width - margin_x
    column_pitch = (usable_x2 - usable_x1) / max(1, (category_count - 1))
    category_center_x_list = [usable_x1 + column_index * column_pitch for column_index in range(category_count)]

    rail_x_left = min(category_center_x_list)
    rail_x_right = max(category_center_x_list)
    axis.plot(
        [rail_x_left, rail_x_right],
        [rail_y, rail_y],
        color="black",
        linewidth=line_width,
        solid_capstyle="butt",
        zorder=1,
    )

    category_drop = 0.48
    category_center_y = rail_y - category_drop
    category_bottom_per_column: list[float] = []

    max_category_half_width = column_pitch * 0.46
    for column_index, (category_title, _) in enumerate(category_leaf_rows):
        column_center_x = category_center_x_list[column_index]
        text_width, text_height = measure_horizontal(category_title, font_category)
        half_w = min(max_category_half_width, text_width / 2 + pad_x_chain)
        box_width = 2 * half_w
        box_height = text_height + 2 * pad_y_chain
        left = column_center_x - box_width / 2
        bottom = category_center_y - box_height / 2
        rect = Rectangle(
            (left, bottom),
            box_width,
            box_height,
            facecolor="white",
            edgecolor=box_edge,
            linewidth=line_width,
            zorder=2,
        )
        axis.add_patch(rect)
        axis.text(column_center_x, category_center_y, category_title, ha="center", va="center", fontsize=font_category, color="black", zorder=3)
        category_top_y = category_center_y + box_height / 2
        draw_down_arrow(column_center_x, rail_y - 0.02, column_center_x, category_top_y + 0.02)
        category_bottom_per_column.append(bottom)

    global_category_bottom = min(category_bottom_per_column)

    leaf_gap_x = 0.08
    leaf_drop = 0.38

    for column_index, (_, leaf_label_list) in enumerate(category_leaf_rows):
        column_center_x = category_center_x_list[column_index]
        leaf_count = len(leaf_label_list)
        if leaf_count <= 0:
            continue

        leaf_specs: list[tuple[float, float, str]] = []
        for leaf_label in leaf_label_list:
            stacked = stack_chars_vertically(leaf_label)
            character_column_width, character_column_height = measure_vertical_stack(leaf_label, font_leaf)
            box_w = character_column_width + 2 * pad_x_leaf
            box_h = character_column_height + 2 * pad_y_leaf
            leaf_specs.append((box_w, box_h, stacked))

        total_width = sum(spec[0] for spec in leaf_specs) + max(0, leaf_count - 1) * leaf_gap_x
        row_left = column_center_x - total_width / 2
        leaf_top_y = global_category_bottom - leaf_drop

        cursor_x = row_left
        for leaf_index, (box_w, box_h, stacked_text) in enumerate(leaf_specs):
            box_center_x = cursor_x + box_w / 2
            box_center_y = leaf_top_y - box_h / 2
            cursor_x += box_w + leaf_gap_x

            draw_down_arrow(
                column_center_x,
                category_bottom_per_column[column_index] - 0.02,
                box_center_x,
                box_center_y + box_h / 2 + 0.03,
            )
            rect = Rectangle(
                (box_center_x - box_w / 2, box_center_y - box_h / 2),
                box_w,
                box_h,
                facecolor="white",
                edgecolor=box_edge,
                linewidth=line_width,
                zorder=2,
            )
            axis.add_patch(rect)
            axis.text(
                box_center_x,
                box_center_y,
                stacked_text,
                ha="center",
                va="center",
                fontsize=font_leaf,
                color="black",
                linespacing=linespacing_tight,
                zorder=3,
            )

    out_png = output_dir / "point_cloud_processing_tree.png"
    out_svg = output_dir / "point_cloud_processing_tree.svg"
    figure.savefig(out_png)
    figure.savefig(out_svg)
    plt.close(figure)


def main() -> int:
    repo_root = Path(__file__).resolve().parents[2]
    output_dir = repo_root / "docs" / "thesis" / "images"
    output_dir.mkdir(parents=True, exist_ok=True)

    try:
        configure_fonts()
    except ImportError:
        print("matplotlib is required: pip install matplotlib", file=sys.stderr)
        return 1

    draw_processing_tree(output_dir)
    print("Wrote:")
    print(" ", output_dir / "point_cloud_processing_tree.png")
    print(" ", output_dir / "point_cloud_processing_tree.svg")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
