#!/usr/bin/env python3
"""
PCFPS 点云数据处理流程图（滤波主链路 + 派生说明脚注），
内容与 delta/1.req 下 pointcloud-pipeline、integration-python 及 README 一致。

Outputs:
  docs/thesis/images/point_cloud_data_flow.png
  docs/thesis/images/point_cloud_data_flow.svg

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
            "savefig.pad_inches": 0.22,
        }
    )


def measure_text_size_data_units(
    axis,
    figure,
    text_content: str,
    fontsize: float,
    *,
    linespacing: float | None,
) -> tuple[float, float]:
    kwargs: dict = {
        "fontsize": fontsize,
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


def draw_data_flow(output_dir: Path) -> None:
    import matplotlib.pyplot as plt
    from matplotlib.patches import FancyArrowPatch, Rectangle

    title_text = "PCFPS 点云数据处理流程（滤波主链路）"
    footnote_text = (
        "派生（分割/分类）：滤波成功后由 Spring 提交 POST /derived-jobs，python_derived 写 derived.las；\n"
        "双窗走 derived-comparison-bundle，分类视图 colorMode: classification。"
    )

    step_label_list: list[str] = [
        "① 用户（Web UI 或 API）\n"
        "JWT 鉴权后登记\n"
        "输入 LAS 路径与输出目录",
        "② Spring Boot / job 域\n"
        "创建 FilterTask\n"
        "状态 PENDING",
        "③ 调度器（并发配额）\n"
        "WebClient：POST /jobs → 202\n"
        "任务 RUNNING；\n"
        "轮询 GET /jobs/{uuid}",
        "④ Python（FastAPI）\n"
        "laspy 分块读 XYZ\n"
        "近邻：cKDTree / BallTree\n"
        "SOR 或 ROR 掩码\n"
        "写出 filtered.las\n"
        "与 N_before / N_after 等指标",
        "⑤ Java 回填\n"
        "file-metadata、路径角色\n"
        "任务 SUCCEEDED",
        "⑥ 前端\n"
        "GET comparison-bundle\n"
        "双窗 preview-points\n"
        "（SOURCE / FILTER 等 PLY）",
    ]

    font_title = 13.0
    font_step = 10.2
    font_foot = 8.4
    line_width = 1.05
    linespacing_step = 1.05
    pad_x = 0.14
    pad_y = 0.11
    gap_between_steps = 0.38

    figure_width = 11.0
    figure_height = 15.0
    figure, axis = plt.subplots(figsize=(figure_width, figure_height))

    axis_width = 9.2
    axis_height = 17.5
    axis.set_xlim(0, axis_width)
    axis.set_ylim(0, axis_height)
    axis.axis("off")
    figure.patch.set_facecolor("white")
    axis.set_facecolor("white")

    center_x = axis_width / 2

    def measure_step(label: str) -> tuple[float, float]:
        return measure_text_size_data_units(
            axis,
            figure,
            label,
            font_step,
            linespacing=linespacing_step,
        )

    title_width, title_height = measure_text_size_data_units(
        axis,
        figure,
        title_text,
        font_title,
        linespacing=None,
    )
    title_center_y = axis_height - 0.35 - title_height / 2
    title_box_w = title_width + 2 * pad_x
    title_box_h = title_height + 2 * pad_y
    title_bottom = title_center_y - title_box_h / 2
    title_rect = Rectangle(
        (center_x - title_box_w / 2, title_bottom),
        title_box_w,
        title_box_h,
        facecolor="white",
        edgecolor="black",
        linewidth=line_width,
        zorder=2,
    )
    axis.add_patch(title_rect)
    axis.text(center_x, title_center_y, title_text, ha="center", va="center", fontsize=font_title, color="black", zorder=3)

    cursor_bottom = title_bottom - gap_between_steps
    previous_step_bottom = title_bottom

    for step_index, step_label in enumerate(step_label_list):
        text_width, text_height = measure_step(step_label)
        box_width = text_width + 2 * pad_x
        box_height = text_height + 2 * pad_y
        step_center_y = cursor_bottom - box_height / 2
        step_left = center_x - box_width / 2
        step_bottom = step_center_y - box_height / 2
        rect = Rectangle(
            (step_left, step_bottom),
            box_width,
            box_height,
            facecolor="white",
            edgecolor="black",
            linewidth=line_width,
            zorder=2,
        )
        axis.add_patch(rect)
        axis.text(
            center_x,
            step_center_y,
            step_label,
            ha="center",
            va="center",
            fontsize=font_step,
            color="black",
            linespacing=linespacing_step,
            zorder=3,
        )
        arrow = FancyArrowPatch(
            (center_x, previous_step_bottom - 0.02),
            (center_x, step_center_y + box_height / 2 + 0.02),
            arrowstyle="-|>",
            mutation_scale=11,
            linewidth=line_width,
            color="black",
            zorder=1,
        )
        axis.add_patch(arrow)
        previous_step_bottom = step_bottom
        cursor_bottom = step_bottom - gap_between_steps

    foot_width, foot_height = measure_text_size_data_units(
        axis,
        figure,
        footnote_text,
        font_foot,
        linespacing=1.12,
    )
    foot_box_w = min(axis_width - 0.5, foot_width + 2 * pad_x)
    foot_box_h = foot_height + 2 * pad_y
    foot_top = cursor_bottom - 0.22
    foot_bottom = foot_top - foot_box_h
    foot_center_y = (foot_top + foot_bottom) / 2
    foot_left = center_x - foot_box_w / 2
    foot_rect = Rectangle(
        (foot_left, foot_bottom),
        foot_box_w,
        foot_box_h,
        facecolor="#f8fafc",
        edgecolor="black",
        linewidth=line_width * 0.85,
        zorder=2,
    )
    axis.add_patch(foot_rect)
    axis.text(
        center_x,
        foot_center_y,
        footnote_text,
        ha="center",
        va="center",
        fontsize=font_foot,
        color="#334155",
        linespacing=1.12,
        zorder=3,
    )

    out_png = output_dir / "point_cloud_data_flow.png"
    out_svg = output_dir / "point_cloud_data_flow.svg"
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

    draw_data_flow(output_dir)
    print("Wrote:")
    print(" ", output_dir / "point_cloud_data_flow.png")
    print(" ", output_dir / "point_cloud_data_flow.svg")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
