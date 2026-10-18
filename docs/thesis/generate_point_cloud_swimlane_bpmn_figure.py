#!/usr/bin/env python3
"""
PCFPS 点云滤波主链路 — BPMN 三泳道图。

布局：先按字号测量各节点外框，列间距取「相邻列半宽之和」的最大值以防重叠；
泳道高度取该泳道内节点最大高度，整体纵向紧凑；外边距与池区压缩。
在「尽量小的画布」上放大字号与框内留白，保证文字落在圆角矩形内。

Outputs:
  docs/thesis/images/point_cloud_swimlane_bpmn.png
  docs/thesis/images/point_cloud_swimlane_bpmn.svg

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
            "savefig.pad_inches": 0.05,
        }
    )


def stack_chars_vertical_line(label: str) -> str:
    character_list = [character for character in list(label) if not character.isspace()]
    return "\n".join(character_list)


def measure_text_size_data_units(
    axis,
    figure,
    text_content: str,
    fontsize: float,
    *,
    linespacing: float | None,
    fontweight: str | None = None,
) -> tuple[float, float]:
    kwargs: dict = {
        "fontsize": fontsize,
        "ha": "center",
        "va": "center",
        "visible": False,
        "color": "#1e293b",
    }
    if linespacing is not None:
        kwargs["linespacing"] = linespacing
    if fontweight is not None:
        kwargs["fontweight"] = fontweight
    text_artist = axis.text(0.0, 0.0, text_content, **kwargs)
    figure.canvas.draw()
    renderer = figure.canvas.get_renderer()
    window_bbox = text_artist.get_window_extent(renderer=renderer)
    bbox_data = window_bbox.transformed(axis.transData.inverted())
    text_artist.remove()
    return abs(bbox_data.width), abs(bbox_data.height)


def draw_swimlane_bpmn(output_dir: Path) -> None:
    import matplotlib.pyplot as plt
    import numpy as np
    from matplotlib.patches import Circle, FancyArrowPatch, FancyBboxPatch, Rectangle

    # —— 字号 / 内边距（略大：字在框内）——
    font_pool_title = 12.4
    font_pool_sub = 9.0
    font_lane_vertical = 9.8
    font_task = 11.0
    linespacing_task = 1.06
    pad_x_task = 0.22
    pad_y_task = 0.16
    pool_title_pad_y = 0.1
    stroke_outer = 1.0
    stroke_inner = 0.72
    arrow_shrink_points = 5.0
    pool_margin = 0.07
    header_column_width = 0.78
    lane_gap_y = 0.045
    column_gap_extra = 0.055
    inner_left_pad = 0.1
    inner_right_pad = 0.22

    color_canvas = "#f1f5f9"
    color_pool_bar = "#ffffff"
    color_pool_accent = "#0d9488"
    color_lane_header = "#e8eef3"
    color_lane_divider = "#cbd5e1"
    color_lane_python = "#ffffff"
    color_lane_spring = "#e8f4fc"
    color_lane_frontend = "#ffffff"
    color_task_fill = "#ffffff"
    color_task_edge = "#94a3b8"
    color_text_primary = "#0f172a"
    color_text_muted = "#475569"
    color_arrow_sequence = "#334155"
    color_arrow_message = "#64748b"

    figure, axis = plt.subplots()
    axis.set_xlim(0, 100)
    axis.set_ylim(0, 100)
    axis.axis("off")

    def task_outer_size(label: str) -> tuple[float, float]:
        text_width, text_height = measure_text_size_data_units(
            axis,
            figure,
            label,
            font_task,
            linespacing=linespacing_task,
        )
        return text_width + 2 * pad_x_task, text_height + 2 * pad_y_task

    label_submit = "提交滤波任务\nJWT · LAS 路径"
    label_preview = "双窗预览\ncomparison-bundle"
    label_create = "创建 FilterTask\nPENDING"
    label_post = "WebClient\nPOST /jobs"
    label_poll = "轮询\nGET /jobs/{uuid}"
    label_done = "回填元数据\nSUCCEEDED"
    label_accept = "接收作业\nHTTP 202"
    label_filter = "laspy 分块\nSOR / ROR"
    label_write = "写出\nfiltered.las"

    width_submit, height_submit = task_outer_size(label_submit)
    width_preview, height_preview = task_outer_size(label_preview)
    width_create, height_create = task_outer_size(label_create)
    width_post, height_post = task_outer_size(label_post)
    width_poll, height_poll = task_outer_size(label_poll)
    width_done, height_done = task_outer_size(label_done)
    width_accept, height_accept = task_outer_size(label_accept)
    width_filter, height_filter = task_outer_size(label_filter)
    width_write, height_write = task_outer_size(label_write)

    radius_start = 0.132
    radius_end_outer = 0.136

    pool_title_line1 = "PCFPS 点云滤波处理"
    pool_title_line2 = "泳道 · 滤波主链路 · Java / Python HTTP"
    pool_title_w1, pool_title_h1 = measure_text_size_data_units(
        axis, figure, pool_title_line1, font_pool_title, linespacing=None, fontweight="600"
    )
    pool_title_w2, pool_title_h2 = measure_text_size_data_units(
        axis, figure, pool_title_line2, font_pool_sub, linespacing=None, fontweight=None
    )
    pool_title_height = pool_title_h1 + pool_title_h2 + 2 * pool_title_pad_y + 0.12

    half_width_by_column: list[float] = [
        radius_start,
        max(width_submit, width_create) / 2.0,
        max(width_post, width_accept) / 2.0,
        max(width_poll, width_filter) / 2.0,
        max(width_preview, width_done, width_write) / 2.0,
        radius_end_outer,
    ]

    pitch_x = max(
        half_width_by_column[column_index] + half_width_by_column[column_index + 1] + column_gap_extra
        for column_index in range(5)
    )

    inner_content_width = 5.0 * pitch_x
    axis_width = pool_margin * 2.0 + header_column_width + inner_left_pad + inner_content_width + inner_right_pad

    lane_height_frontend = max(height_submit, height_preview, 2 * radius_start, 2 * radius_end_outer) + 0.12
    lane_height_spring = max(height_create, height_post, height_poll, height_done) + 0.12
    lane_height_python = max(height_accept, height_filter, height_write) + 0.12

    axis_height = (
        pool_margin
        + pool_title_height
        + lane_height_frontend
        + lane_gap_y
        + lane_height_spring
        + lane_gap_y
        + lane_height_python
        + pool_margin
    )

    axis.set_xlim(0, axis_width)
    axis.set_ylim(0, axis_height)
    figure.patch.set_facecolor(color_canvas)
    axis.set_facecolor(color_canvas)

    pool_inner_left = pool_margin
    pool_inner_width = axis_width - 2 * pool_margin
    lane_content_left = pool_inner_left + header_column_width + inner_left_pad
    column_center_array = np.array([lane_content_left + (pitch_x * index) for index in range(6)], dtype=float)

    content_top_y = axis_height - pool_margin - pool_title_height
    lane_frontend_top_y = content_top_y
    lane_frontend_bottom_y = lane_frontend_top_y - lane_height_frontend
    lane_spring_top_y = lane_frontend_bottom_y - lane_gap_y
    lane_spring_bottom_y = lane_spring_top_y - lane_height_spring
    lane_python_top_y = lane_spring_bottom_y - lane_gap_y
    lane_python_bottom_y = lane_python_top_y - lane_height_python

    lane_python_mid_y = (lane_python_bottom_y + lane_python_top_y) / 2.0
    lane_spring_mid_y = (lane_spring_bottom_y + lane_spring_top_y) / 2.0
    lane_frontend_mid_y = (lane_frontend_bottom_y + lane_frontend_top_y) / 2.0

    pool_frame = FancyBboxPatch(
        (pool_margin, pool_margin),
        axis_width - 2 * pool_margin,
        axis_height - 2 * pool_margin,
        boxstyle="round,pad=0.015,rounding_size=0.1",
        facecolor="#ffffff",
        edgecolor=color_lane_divider,
        linewidth=stroke_outer,
        zorder=0,
    )
    axis.add_patch(pool_frame)

    def draw_lane_row(
        lane_bottom_y: float,
        lane_top_y: float,
        body_facecolor: str,
        lane_title: str,
    ) -> None:
        header_rect = FancyBboxPatch(
            (pool_margin, lane_bottom_y),
            header_column_width,
            lane_top_y - lane_bottom_y,
            boxstyle="round,pad=0,rounding_size=0",
            facecolor=color_lane_header,
            edgecolor="none",
            zorder=1,
        )
        axis.add_patch(header_rect)
        axis.plot(
            [header_column_width + pool_margin, header_column_width + pool_margin],
            [lane_bottom_y, lane_top_y],
            color=color_lane_divider,
            linewidth=stroke_inner,
            solid_capstyle="round",
            zorder=2,
        )
        body_rect = Rectangle(
            (header_column_width + pool_margin, lane_bottom_y),
            axis_width - header_column_width - 2 * pool_margin,
            lane_top_y - lane_bottom_y,
            facecolor=body_facecolor,
            edgecolor="none",
            zorder=1,
        )
        axis.add_patch(body_rect)
        axis.plot(
            [pool_margin, axis_width - pool_margin],
            [lane_bottom_y, lane_bottom_y],
            color=color_lane_divider,
            linewidth=stroke_inner * 0.85,
            zorder=2,
        )
        stacked_lane_title = stack_chars_vertical_line(lane_title)
        lane_mid_y = (lane_bottom_y + lane_top_y) / 2.0
        axis.text(
            pool_margin + header_column_width / 2.0,
            lane_mid_y,
            stacked_lane_title,
            ha="center",
            va="center",
            fontsize=font_lane_vertical,
            fontweight="600",
            color=color_text_muted,
            linespacing=0.92,
            zorder=4,
        )

    pool_bar = Rectangle(
        (pool_inner_left, content_top_y),
        pool_inner_width,
        pool_title_height,
        facecolor=color_pool_bar,
        edgecolor="none",
        zorder=3,
    )
    axis.add_patch(pool_bar)
    axis.plot(
        [pool_inner_left, pool_inner_left + pool_inner_width],
        [content_top_y, content_top_y],
        color=color_lane_divider,
        linewidth=stroke_inner,
        zorder=4,
    )
    axis.plot(
        [pool_inner_left, pool_inner_left + pool_inner_width],
        [content_top_y + pool_title_height, content_top_y + pool_title_height],
        color=color_lane_divider,
        linewidth=stroke_inner,
        zorder=4,
    )
    axis.plot(
        [pool_inner_left, pool_inner_left],
        [content_top_y, content_top_y + pool_title_height],
        color=color_lane_divider,
        linewidth=stroke_inner,
        zorder=4,
    )
    axis.plot(
        [pool_inner_left + pool_inner_width, pool_inner_left + pool_inner_width],
        [content_top_y, content_top_y + pool_title_height],
        color=color_lane_divider,
        linewidth=stroke_inner,
        zorder=4,
    )
    axis.plot(
        [pool_inner_left, pool_inner_left + pool_inner_width],
        [content_top_y + pool_title_height - 0.035, content_top_y + pool_title_height - 0.035],
        color=color_pool_accent,
        linewidth=2.35,
        solid_capstyle="butt",
        zorder=5,
    )
    axis.text(
        pool_inner_left + pool_inner_width / 2.0,
        content_top_y + pool_title_height - pool_title_pad_y - pool_title_h1 / 2.0,
        pool_title_line1,
        ha="center",
        va="center",
        fontsize=font_pool_title,
        fontweight="600",
        color=color_text_primary,
        zorder=6,
    )
    axis.text(
        pool_inner_left + pool_inner_width / 2.0,
        content_top_y + pool_title_pad_y + pool_title_h2 / 2.0,
        pool_title_line2,
        ha="center",
        va="center",
        fontsize=font_pool_sub,
        color=color_text_muted,
        zorder=6,
    )

    draw_lane_row(lane_frontend_bottom_y, lane_frontend_top_y, color_lane_frontend, "用户与前端")
    draw_lane_row(lane_spring_bottom_y, lane_spring_top_y, color_lane_spring, "Spring Boot")
    draw_lane_row(lane_python_bottom_y, lane_python_top_y, color_lane_python, "Python 服务")

    def draw_rounded_task(center_x: float, center_y: float, label: str) -> dict[str, float]:
        text_width, text_height = measure_text_size_data_units(
            axis,
            figure,
            label,
            font_task,
            linespacing=linespacing_task,
        )
        box_width = text_width + 2 * pad_x_task
        box_height = text_height + 2 * pad_y_task
        left_edge = center_x - box_width / 2.0
        bottom_edge = center_y - box_height / 2.0
        rounding = min(0.2, box_height * 0.11)
        rounded = FancyBboxPatch(
            (left_edge, bottom_edge),
            box_width,
            box_height,
            boxstyle=f"round,pad=0.025,rounding_size={rounding}",
            facecolor=color_task_fill,
            edgecolor=color_task_edge,
            linewidth=stroke_inner,
            zorder=5,
        )
        axis.add_patch(rounded)
        axis.text(
            center_x,
            center_y,
            label,
            ha="center",
            va="center",
            fontsize=font_task,
            color=color_text_primary,
            linespacing=linespacing_task,
            zorder=6,
        )
        return {
            "left": left_edge,
            "right": left_edge + box_width,
            "bottom": bottom_edge,
            "top": bottom_edge + box_height,
            "center_x": center_x,
            "center_y": center_y,
        }

    def draw_start_event(center_x: float, center_y: float) -> dict[str, float]:
        ring = Circle(
            (center_x, center_y),
            radius_start,
            facecolor="#ecfdf5",
            edgecolor="#059669",
            linewidth=stroke_inner * 1.05,
            zorder=5,
        )
        axis.add_patch(ring)
        return {
            "left": center_x - radius_start,
            "right": center_x + radius_start,
            "bottom": center_y - radius_start,
            "top": center_y + radius_start,
            "center_x": center_x,
            "center_y": center_y,
        }

    def draw_end_event(center_x: float, center_y: float) -> dict[str, float]:
        radius_inner = 0.082
        outer = Circle(
            (center_x, center_y),
            radius_end_outer,
            facecolor="#ffffff",
            edgecolor="#64748b",
            linewidth=stroke_inner * 1.05,
            zorder=5,
        )
        inner = Circle(
            (center_x, center_y),
            radius_inner,
            facecolor="#475569",
            edgecolor="#475569",
            linewidth=0,
            zorder=6,
        )
        axis.add_patch(outer)
        axis.add_patch(inner)
        return {
            "left": center_x - radius_end_outer,
            "right": center_x + radius_end_outer,
            "bottom": center_y - radius_end_outer,
            "top": center_y + radius_end_outer,
            "center_x": center_x,
            "center_y": center_y,
        }

    def draw_sequence_arrow(from_shape: dict[str, float], to_shape: dict[str, float]) -> None:
        arrow = FancyArrowPatch(
            (from_shape["right"], from_shape["center_y"]),
            (to_shape["left"], to_shape["center_y"]),
            arrowstyle="-|>",
            mutation_scale=10,
            linewidth=stroke_inner * 1.12,
            color=color_arrow_sequence,
            shrinkA=arrow_shrink_points,
            shrinkB=arrow_shrink_points,
            zorder=4,
        )
        axis.add_patch(arrow)

    def draw_message_flow_down(from_shape: dict[str, float], to_shape: dict[str, float]) -> None:
        arrow = FancyArrowPatch(
            (from_shape["center_x"], from_shape["bottom"]),
            (to_shape["center_x"], to_shape["top"]),
            arrowstyle="-|>",
            mutation_scale=8,
            linewidth=stroke_inner,
            color=color_arrow_message,
            linestyle=(0, (5, 4)),
            shrinkA=arrow_shrink_points,
            shrinkB=arrow_shrink_points,
            connectionstyle="arc3,rad=0.06",
            zorder=4,
        )
        axis.add_patch(arrow)

    def draw_message_flow_up(from_shape: dict[str, float], to_shape: dict[str, float]) -> None:
        arrow = FancyArrowPatch(
            (from_shape["center_x"], from_shape["top"]),
            (to_shape["center_x"], to_shape["bottom"]),
            arrowstyle="-|>",
            mutation_scale=8,
            linewidth=stroke_inner,
            color=color_arrow_message,
            linestyle=(0, (5, 4)),
            shrinkA=arrow_shrink_points,
            shrinkB=arrow_shrink_points,
            connectionstyle="arc3,rad=-0.06",
            zorder=4,
        )
        axis.add_patch(arrow)

    def draw_message_flow_diagonal(from_shape: dict[str, float], to_shape: dict[str, float]) -> None:
        arrow = FancyArrowPatch(
            (from_shape["right"], from_shape["center_y"]),
            (to_shape["left"], to_shape["center_y"]),
            arrowstyle="-|>",
            mutation_scale=8,
            linewidth=stroke_inner,
            color=color_arrow_message,
            linestyle=(0, (5, 4)),
            shrinkA=arrow_shrink_points,
            shrinkB=arrow_shrink_points,
            connectionstyle="arc3,rad=0.14",
            zorder=4,
        )
        axis.add_patch(arrow)

    column_index_start = 0
    column_index_submit = 1
    column_index_create = 1
    column_index_post = 2
    column_index_accept = 2
    column_index_poll = 3
    column_index_filter = 3
    column_index_done = 4
    column_index_write = 4
    column_index_preview = 4
    column_index_end = 5

    start_shape = draw_start_event(column_center_array[column_index_start], lane_frontend_mid_y)
    submit_shape = draw_rounded_task(column_center_array[column_index_submit], lane_frontend_mid_y, label_submit)
    preview_shape = draw_rounded_task(column_center_array[column_index_preview], lane_frontend_mid_y, label_preview)
    end_shape = draw_end_event(column_center_array[column_index_end], lane_frontend_mid_y)

    create_shape = draw_rounded_task(column_center_array[column_index_create], lane_spring_mid_y, label_create)
    post_shape = draw_rounded_task(column_center_array[column_index_post], lane_spring_mid_y, label_post)
    poll_shape = draw_rounded_task(column_center_array[column_index_poll], lane_spring_mid_y, label_poll)
    done_shape = draw_rounded_task(column_center_array[column_index_done], lane_spring_mid_y, label_done)

    accept_shape = draw_rounded_task(column_center_array[column_index_accept], lane_python_mid_y, label_accept)
    filter_shape = draw_rounded_task(column_center_array[column_index_filter], lane_python_mid_y, label_filter)
    write_shape = draw_rounded_task(column_center_array[column_index_write], lane_python_mid_y, label_write)

    draw_sequence_arrow(start_shape, submit_shape)
    draw_sequence_arrow(create_shape, post_shape)
    draw_sequence_arrow(post_shape, poll_shape)
    draw_sequence_arrow(poll_shape, done_shape)
    draw_sequence_arrow(accept_shape, filter_shape)
    draw_sequence_arrow(filter_shape, write_shape)
    draw_sequence_arrow(preview_shape, end_shape)

    draw_message_flow_down(submit_shape, create_shape)
    draw_message_flow_down(post_shape, accept_shape)
    draw_message_flow_up(write_shape, poll_shape)
    draw_message_flow_diagonal(done_shape, preview_shape)

    aspect = axis_width / axis_height
    figure_width_inch = 11.2
    figure.set_size_inches(figure_width_inch, figure_width_inch / aspect)

    out_png = output_dir / "point_cloud_swimlane_bpmn.png"
    out_svg = output_dir / "point_cloud_swimlane_bpmn.svg"
    figure.savefig(out_png, facecolor=color_canvas)
    figure.savefig(out_svg, facecolor=color_canvas)
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

    try:
        import numpy as np  # noqa: F401
    except ImportError:
        print("numpy is required: pip install numpy", file=sys.stderr)
        return 1

    draw_swimlane_bpmn(output_dir)
    print("Wrote:")
    print(" ", output_dir / "point_cloud_swimlane_bpmn.png")
    print(" ", output_dir / "point_cloud_swimlane_bpmn.svg")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
