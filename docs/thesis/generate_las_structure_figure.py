#!/usr/bin/env python3
"""
Generate LAS/LAZ file structure figures for thesis documentation.

Outputs PNG and SVG under docs/thesis/images/.

Requires: matplotlib

Layout: colorful blocks (original style). Title is placed above the outer frame
with explicit vertical gap so it does not touch the border.

Also writes ``las_file_structure_diagram.png`` — three-column reference-style figure
(left overview, header table, point record table, notes, arrows).
"""

from __future__ import annotations

import sys
from pathlib import Path


def configure_matplotlib_fonts() -> None:
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


def draw_main_structure(output_dir: Path) -> None:
    import matplotlib.pyplot as plt
    from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

    fig, ax = plt.subplots(figsize=(10, 7))
    ax.set_xlim(0, 10)
    # Extra headroom so the title sits clearly above the outer box (top at y=9.5)
    ax.set_ylim(0, 10.35)
    ax.axis("off")

    outer = FancyBboxPatch(
        (0.4, 0.5),
        9.2,
        9.0,
        boxstyle="round,pad=0.02,rounding_size=0.25",
        linewidth=2,
        edgecolor="#1a365d",
        facecolor="#ebf4ff",
    )
    ax.add_patch(outer)

    outer_top = 0.5 + 9.0
    title_baseline = outer_top + 0.42
    ax.text(
        5,
        title_baseline,
        "LAS / LAZ 文件逻辑结构",
        ha="center",
        va="bottom",
        fontsize=16,
        fontweight="bold",
        color="#1a365d",
    )

    boxes = [
        (0.7, 7.35, 8.6, 1.35, "① Public Header Block（公共文件头）", "定长；版本、点数、点格式、offset、XYZ scale/offset 等", "#bee3f8", "#2b6cb0"),
        (0.7, 5.55, 8.6, 1.35, "② VLR（Variable Length Records）", "0～多条；坐标系、波形索引、扩展维度定义等", "#c6f6d5", "#276749"),
        (0.7, 3.75, 8.6, 1.35, "③ Point Data Records（点数据区）", "N 个点；每条为 point format 定义的定宽/含 extra 记录", "#feebc8", "#c05621"),
        (0.7, 1.95, 8.6, 1.35, "④ EVLR（Extended VLR，可选）", "LAS 1.4+ 常见置于文件末尾；大体量元数据", "#e9d8fd", "#553c9a"),
    ]

    for left, bottom, width, height, title, subtitle, face, edge in boxes:
        rect = FancyBboxPatch(
            (left, bottom),
            width,
            height,
            boxstyle="round,pad=0.02,rounding_size=0.12",
            linewidth=1.4,
            edgecolor=edge,
            facecolor=face,
        )
        ax.add_patch(rect)
        ax.text(left + width / 2, bottom + height - 0.38, title, ha="center", va="top", fontsize=12, fontweight="bold", color="#1a202c")
        ax.text(left + width / 2, bottom + 0.35, subtitle, ha="center", va="bottom", fontsize=9.5, color="#4a5568")

    arrow_style = "Simple, tail_width=0.5, head_width=4, head_length=8"
    for y_top, y_bottom in [(7.35, 6.9), (5.55, 5.1), (3.75, 3.3)]:
        arr = FancyArrowPatch(
            (5, y_top),
            (5, y_bottom),
            arrowstyle=arrow_style,
            color="#2d3748",
            mutation_scale=1,
            linewidth=1.2,
        )
        ax.add_patch(arr)

    ax.text(
        5,
        0.85,
        "LAZ：与 LAS 逻辑结构一致，点数据区经 LASzip 压缩；读写由 laspy 等库完成解码。",
        ha="center",
        va="center",
        fontsize=9,
        color="#4a5568",
    )

    png_path = output_dir / "las_file_structure.png"
    svg_path = output_dir / "las_file_structure.svg"
    fig.savefig(png_path)
    fig.savefig(svg_path)
    plt.close(fig)


def draw_header_detail(output_dir: Path) -> None:
    import matplotlib.pyplot as plt
    from matplotlib.patches import FancyBboxPatch

    fig, ax = plt.subplots(figsize=(10, 5.2))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 6.15)
    ax.axis("off")

    title_baseline = 5.78
    ax.text(
        5,
        title_baseline,
        "公共文件头与单条点记录（示意）",
        ha="center",
        va="bottom",
        fontsize=15,
        fontweight="bold",
        color="#1a365d",
    )

    header = FancyBboxPatch(
        (0.45, 3.05),
        9.1,
        1.85,
        boxstyle="round,pad=0.02,rounding_size=0.15",
        linewidth=1.5,
        edgecolor="#2b6cb0",
        facecolor="#ebf8ff",
    )
    ax.add_patch(header)
    ax.text(5, 4.65, "Public Header：LASF 标识、版本、offset_to_point_data、point_data_format、", ha="center", va="center", fontsize=10, color="#2d3748")
    ax.text(5, 4.25, "number_of_point_records、x/y/z_scale、x/y/z_offset、max/min XYZ …", ha="center", va="center", fontsize=10, color="#2d3748")

    point_box = FancyBboxPatch(
        (0.45, 0.55),
        9.1,
        2.15,
        boxstyle="round,pad=0.02,rounding_size=0.15",
        linewidth=1.5,
        edgecolor="#c05621",
        facecolor="#fffaf0",
    )
    ax.add_patch(point_box)
    ax.text(5, 2.45, "单条 Point Data Record（列 = dimensions）", ha="center", va="center", fontsize=11, fontweight="bold", color="#9c4221")

    dims = ["X, Y, Z", "Intensity", "Return / N returns", "Classification", "GPS Time / RGB …", "Extra dims"]
    x0 = 0.75
    gap = 1.42
    for index, label in enumerate(dims):
        bx = x0 + index * gap
        if bx > 8.2:
            break
        cell = FancyBboxPatch(
            (bx, 0.85),
            1.25,
            1.05,
            boxstyle="round,pad=0.01,rounding_size=0.08",
            linewidth=1,
            edgecolor="#744210",
            facecolor="#fefcbf",
        )
        ax.add_patch(cell)
        ax.text(bx + 0.625, 1.375, label, ha="center", va="center", fontsize=8.2, color="#744210")

    ax.text(5, 0.28, "子集写出时需拷贝/对齐 LasHeader 尺度与点格式，以保留量纲与维度。", ha="center", va="center", fontsize=9, color="#4a5568")

    fig.savefig(output_dir / "las_header_and_point_record.png")
    fig.savefig(output_dir / "las_header_and_point_record.svg")
    plt.close(fig)


def draw_las_three_column_diagram(output_dir: Path) -> None:
    """
    LAS file structure in a three-column layout (similar to common thesis diagrams):
    left — sequential blocks; middle — public header field table; right — point format 1;
    bottom-right — notes; dashed arrows header↔table, solid arrow point data→table.
    """
    import matplotlib.pyplot as plt
    from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Rectangle

    fig, ax = plt.subplots(figsize=(16.5, 10.2))
    ax.set_xlim(-0.15, 16.35)
    ax.set_ylim(-0.15, 11.05)
    ax.axis("off")

    title_y = 10.58
    ax.text(
        8.1,
        title_y,
        "LAS 文件结构图",
        ha="center",
        va="bottom",
        fontsize=18,
        fontweight="bold",
        color="#1a365d",
    )

    # ---- Left column: LAS file overview ----
    left_x0 = 0.22
    left_w = 2.75
    ax.text(left_x0 + left_w / 2, 9.72, "LAS 文件", ha="center", va="bottom", fontsize=12, fontweight="bold", color="#2d3748")

    left_boxes: list[tuple[float, float, str, str, str, str]] = []
    y_top = 9.55
    row_h = 0.52
    gap = 0.06

    def add_left_box(title_line: str, detail: str, face: str, edge: str, height: float | None = None) -> tuple[float, float, float, float]:
        nonlocal y_top
        h = row_h if height is None else height
        bottom = y_top - h
        left_boxes.append((bottom, bottom + h, title_line, face, edge, detail))
        y_top = bottom - gap
        return (left_x0, bottom, left_w, h)

    def draw_left_stack() -> None:
        specs = [
            ("1. 文件签名（LASF）", "4 字节", "#c5e8ff", "#2b6cb0", None),
            ("2. 文件源 ID", "2 字节", "#c6f6d5", "#276749", None),
            ("3. 全局编码", "2 字节", "#fef3c7", "#b7791f", None),
            (
                "4. 公共文件头（主体）",
                "227 / 375 字节（依版本）\n"
                "4.1 版本号　4.2 系统标识　4.3 生成软件\n"
                "4.4 创建日期　4.5 头部长度　4.6 点数据偏移\n"
                "4.7 点格式与尺度　4.8 边界与点数　4.9 回波统计等",
                "#ffd6e8",
                "#97266d",
                1.38,
            ),
            ("5. VLR（可变长记录）", "0～多条，可选", "#e9d8fd", "#553c9a", None),
            ("6. 点数据记录区", "N × 每条点字节数（由点格式决定）", "#c5e8ff", "#2c5282", 0.78),
        ]
        for title_line, detail, face, edge, custom_h in specs:
            left, bottom, width, height = add_left_box(title_line, detail, face, edge, custom_h)
            rect = FancyBboxPatch(
                (left, bottom),
                width,
                height,
                boxstyle="round,pad=0.015,rounding_size=0.1",
                linewidth=1.15,
                edgecolor=edge,
                facecolor=face,
            )
            ax.add_patch(rect)
            ax.text(left + width / 2, bottom + height - 0.12, title_line, ha="center", va="top", fontsize=9.2, fontweight="bold", color="#1a202c")
            ax.text(left + width / 2, bottom + 0.1, detail, ha="center", va="bottom", fontsize=7.8, color="#4a5568", linespacing=1.25)

    draw_left_stack()

    # Record y-range of header block (item 4) and point block (item 6) for arrows
    header_block_y: tuple[float, float] | None = None
    point_block_y: tuple[float, float] | None = None
    for bottom, top, title_line, _face, _edge, _detail in left_boxes:
        if title_line.startswith("4."):
            header_block_y = (bottom, top)
        if title_line.startswith("6."):
            point_block_y = (bottom, top)

    # ---- Middle: public header table ----
    mid_left = 3.18
    mid_w = 5.35
    mid_bottom = 2.05
    mid_h = 7.45
    mid_outer = FancyBboxPatch(
        (mid_left, mid_bottom),
        mid_w,
        mid_h,
        boxstyle="round,pad=0.02,rounding_size=0.12",
        linewidth=1.25,
        edgecolor="#4a5568",
        facecolor="#f7fafc",
    )
    ax.add_patch(mid_outer)
    ax.text(
        mid_left + mid_w / 2,
        mid_bottom + mid_h - 0.2,
        "4. 公共文件头（主体）主要内容",
        ha="center",
        va="top",
        fontsize=11,
        fontweight="bold",
        color="#1a365d",
    )

    header_rows = [
        ("文件版本号", "2", "主版本 / 次版本（如 1.2、1.4）"),
        ("系统标识符", "32", "数据采集系统标识"),
        ("生成软件", "32", "生成该 LAS 的软件名称"),
        ("创建日 / 年", "4", "文件创建日期（Julian day / year）"),
        ("头部长度", "2", "公共文件头总字节数"),
        ("点数据起始偏移", "4", "offset_to_point_data"),
        ("VLR 条数", "4", "可变长记录数量"),
        ("点数据格式 ID", "1", "0～10 等，决定每条点布局"),
        ("点记录总数", "4", "number_of_point_records"),
        ("X/Y/Z scale", "24", "各轴量化比例因子"),
        ("X/Y/Z offset", "24", "各轴偏移量"),
        ("最大 / 最小 XYZ", "24", "数据空间范围"),
    ]

    table_top = mid_bottom + mid_h - 0.68
    table_bottom = mid_bottom + 0.35
    n_data_rows = len(header_rows)
    row_height = (table_top - table_bottom) / (n_data_rows + 1)
    col_x = [mid_left + 0.08, mid_left + 2.35, mid_left + 2.95]
    col_w = [2.2, 0.52, 2.55]

    def cell_rect(r_index: int, c_index: int) -> tuple[float, float, float, float]:
        y_high = table_top - r_index * row_height
        y_low = y_high - row_height
        x0 = col_x[c_index]
        width = col_w[c_index]
        return (x0, y_low, width, y_high - y_low)

    header_bg = "#edf2f7"
    for column_index, header_text in enumerate(["字段名称", "大小（字节）", "说明"]):
        x0, y_low, width, height = cell_rect(0, column_index)
        ax.add_patch(Rectangle((x0, y_low), width, height, facecolor=header_bg, edgecolor="#a0aec0", linewidth=0.8))
        ax.text(x0 + width / 2, y_low + height / 2, header_text, ha="center", va="center", fontsize=8.5, fontweight="bold", color="#2d3748")

    for row_index, row_cells in enumerate(header_rows, start=1):
        for column_index, text in enumerate(row_cells):
            x0, y_low, width, height = cell_rect(row_index, column_index)
            fill = "#ffffff" if row_index % 2 == 1 else "#f8fafc"
            ax.add_patch(Rectangle((x0, y_low), width, height, facecolor=fill, edgecolor="#cbd5e0", linewidth=0.55))
            ax.text(x0 + width / 2, y_low + height / 2, text, ha="center", va="center", fontsize=7.6, color="#2d3748")

    # ---- Right: point data format 1 ----
    right_left = 8.85
    right_w = 7.15
    right_bottom = 2.45
    right_h = 7.05
    right_outer = FancyBboxPatch(
        (right_left, right_bottom),
        right_w,
        right_h,
        boxstyle="round,pad=0.02,rounding_size=0.12",
        linewidth=1.25,
        edgecolor="#9c4221",
        facecolor="#fffaf0",
    )
    ax.add_patch(right_outer)
    ax.text(
        right_left + right_w / 2,
        right_bottom + right_h - 0.2,
        "6. 点数据记录结构（以 Point Data Record Format 1 为例）",
        ha="center",
        va="top",
        fontsize=11,
        fontweight="bold",
        color="#9c4221",
    )

    point_rows = [
        ("X 坐标", "4", "有符号整型；×X_scale + X_offset"),
        ("Y 坐标", "4", "有符号整型；×Y_scale + Y_offset"),
        ("Z 坐标", "4", "有符号整型；×Z_scale + Z_offset"),
        ("强度 Intensity", "2", "回波强度"),
        ("回波信息", "1", "回波号、回波总数等（位域）"),
        ("分类 Classification", "1", "地物 / 噪声等编码"),
        ("扫描角 Rank", "1", "scan angle（与版本相关）"),
        ("用户数据 User Data", "1", "可扩展用途"),
        ("点源 ID", "2", "point source id"),
        ("GPS 时间", "8", "GPS Time（双精度）"),
    ]

    r_table_top = right_bottom + right_h - 0.52
    r_table_bottom = right_bottom + 0.32
    r_n_rows = len(point_rows)
    r_row_h = (r_table_top - r_table_bottom) / (r_n_rows + 1)
    r_col_x = [right_left + 0.08, right_left + 2.85, right_left + 3.45]
    r_col_w = [2.7, 0.52, 3.35]
    header_fill = "#feebc8"

    def r_cell_rect(r_index: int, c_index: int) -> tuple[float, float, float, float]:
        y_high = r_table_top - r_index * r_row_h
        y_low = y_high - r_row_h
        x0 = r_col_x[c_index]
        width = r_col_w[c_index]
        return (x0, y_low, width, y_high - y_low)

    for column_index, header_text in enumerate(["字段名称", "大小（字节）", "说明"]):
        x0, y_low, width, height = r_cell_rect(0, column_index)
        ax.add_patch(Rectangle((x0, y_low), width, height, facecolor=header_fill, edgecolor="#c05621", linewidth=0.8))
        ax.text(x0 + width / 2, y_low + height / 2, header_text, ha="center", va="center", fontsize=8.5, fontweight="bold", color="#744210")

    for row_index, row_cells in enumerate(point_rows, start=1):
        for column_index, text in enumerate(row_cells):
            x0, y_low, width, height = r_cell_rect(row_index, column_index)
            fill = "#ffffff" if row_index % 2 == 1 else "#fffaf0"
            ax.add_patch(Rectangle((x0, y_low), width, height, facecolor=fill, edgecolor="#ecc94b", linewidth=0.55))
            ax.text(x0 + width / 2, y_low + height / 2, text, ha="center", va="center", fontsize=7.5, color="#2d3748")

    # ---- Notes ----
    note_left = 8.85
    note_bottom = 0.18
    note_w = 7.15
    note_h = 1.95
    note_box = FancyBboxPatch(
        (note_left, note_bottom),
        note_w,
        note_h,
        boxstyle="round,pad=0.02,rounding_size=0.1",
        linewidth=1.1,
        edgecolor="#4a5568",
        facecolor="#f0fff4",
    )
    ax.add_patch(note_box)
    ax.text(note_left + note_w / 2, note_bottom + note_h - 0.14, "说明", ha="center", va="top", fontsize=10, fontweight="bold", color="#22543d")
    note_lines = [
        "· LAS 为二进制文件，公共字段以小端（Little-Endian）存储为主（依规范）。",
        "· 公共文件头描述点格式、坐标 scale/offset、数据范围与点数等元信息。",
        "· VLR 常用于投影、坐标系与扩展维度说明；点记录布局随「点数据格式」变化。",
        "· LAZ 与 LAS 逻辑结构一致，点数据区经 LASzip 压缩；读写可由 laspy 等库完成。",
    ]
    note_y = note_bottom + note_h - 0.42
    for line in note_lines:
        ax.text(note_left + 0.12, note_y, line, ha="left", va="top", fontsize=7.6, color="#2f855a")
        note_y -= 0.38

    # ---- Arrows ----
    if header_block_y is not None:
        hx_lo, hx_hi = header_block_y
        mid_x = mid_left
        arr_d1 = FancyArrowPatch(
            (left_x0 + left_w, (hx_lo + hx_hi) / 2 + 0.35),
            (mid_x, table_top - 0.15),
            arrowstyle="-|>",
            mutation_scale=14,
            linewidth=1.0,
            color="#718096",
            linestyle="--",
        )
        ax.add_patch(arr_d1)
        arr_d2 = FancyArrowPatch(
            (left_x0 + left_w, (hx_lo + hx_hi) / 2 - 0.35),
            (mid_x, table_bottom + 0.35),
            arrowstyle="-|>",
            mutation_scale=14,
            linewidth=1.0,
            color="#718096",
            linestyle="--",
        )
        ax.add_patch(arr_d2)

    if point_block_y is not None:
        py_lo, py_hi = point_block_y
        arr_s = FancyArrowPatch(
            (left_x0 + left_w, (py_lo + py_hi) / 2),
            (right_left, (r_table_bottom + r_table_top) / 2),
            arrowstyle="-|>",
            mutation_scale=16,
            linewidth=1.15,
            color="#2c5282",
        )
        ax.add_patch(arr_s)

    out_png = output_dir / "las_file_structure_diagram.png"
    out_svg = output_dir / "las_file_structure_diagram.svg"
    fig.savefig(out_png)
    fig.savefig(out_svg)
    plt.close(fig)


def main() -> int:
    repo_root = Path(__file__).resolve().parents[2]
    output_dir = repo_root / "docs" / "thesis" / "images"
    output_dir.mkdir(parents=True, exist_ok=True)

    try:
        configure_matplotlib_fonts()
    except ImportError:
        print("matplotlib is required: pip install matplotlib", file=sys.stderr)
        return 1

    draw_main_structure(output_dir)
    draw_header_detail(output_dir)
    draw_las_three_column_diagram(output_dir)

    print("Wrote:")
    for name in (
        "las_file_structure.png",
        "las_file_structure.svg",
        "las_header_and_point_record.png",
        "las_header_and_point_record.svg",
        "las_file_structure_diagram.png",
        "las_file_structure_diagram.svg",
    ):
        print(" ", output_dir / name)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
