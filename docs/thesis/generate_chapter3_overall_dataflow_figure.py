#!/usr/bin/env python3
"""
第三章 3.3 系统总体数据流程图（设计层，不含接口/状态码等实现细节）。

Outputs:
  docs/thesis/images/chapter3_overall_dataflow.svg
  docs/thesis/images/chapter3_overall_dataflow.png
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
            "savefig.pad_inches": 0.25,
        }
    )


def draw_overall_dataflow(output_dir: Path) -> None:
    import matplotlib.pyplot as plt
    from matplotlib.patches import FancyArrowPatch, Rectangle

    figure_width_inches = 14.0
    figure_height_inches = 5.2
    figure, axis = plt.subplots(figsize=(figure_width_inches, figure_height_inches))
    axis.set_xlim(0, 14)
    axis.set_ylim(0, 5.2)
    axis.axis("off")

    title_text = "图3-2  系统总体数据流程图"
    figure.suptitle(title_text, fontsize=16, fontweight="bold", y=0.98)

    lane_label_list = [
        ("用户与前端层", 4.35),
        ("后端编排层", 3.35),
        ("算法服务层", 2.35),
        ("数据与文件层", 1.35),
    ]
    lane_height = 0.78
    lane_left = 1.35
    lane_width = 12.2

    for lane_label, lane_center_y in lane_label_list:
        lane_rect = Rectangle(
            (lane_left, lane_center_y - lane_height / 2),
            lane_width,
            lane_height,
            facecolor="#f8fafc",
            edgecolor="#cbd5e1",
            linewidth=1.0,
            zorder=0,
        )
        axis.add_patch(lane_rect)
        axis.text(
            0.35,
            lane_center_y,
            lane_label,
            fontsize=11,
            fontweight="bold",
            va="center",
            ha="left",
            color="#374151",
        )

    def add_box(
        center_x: float,
        center_y: float,
        box_width: float,
        title_line: str,
        subtitle_line: str,
    ) -> tuple[float, float, float, float]:
        box_height = 0.52
        box_left = center_x - box_width / 2
        box_bottom = center_y - box_height / 2
        box_rect = Rectangle(
            (box_left, box_bottom),
            box_width,
            box_height,
            facecolor="#ffffff",
            edgecolor="#3b82f6",
            linewidth=1.4,
            zorder=2,
        )
        axis.add_patch(box_rect)
        axis.text(
            center_x,
            center_y + 0.1,
            title_line,
            ha="center",
            va="center",
            fontsize=10,
            fontweight="bold",
            color="#111827",
            zorder=3,
        )
        axis.text(
            center_x,
            center_y - 0.12,
            subtitle_line,
            ha="center",
            va="center",
            fontsize=8.5,
            color="#4b5563",
            zorder=3,
        )
        return box_left, box_bottom, box_width, box_height

    box_specs: list[tuple[float, float, float, str, str]] = [
        (2.55, 4.35, 1.55, "任务提交", "路径登记 + 参数配置"),
        (4.85, 3.35, 1.75, "请求校验与建档", "认证、参数检查、创建任务"),
        (7.25, 3.35, 1.65, "任务编排与调度", "生成标准化作业请求"),
        (9.65, 2.35, 1.65, "算法处理执行", "按任务类型完成计算"),
        (11.85, 2.35, 1.55, "结果生成", "输出结果文件与统计信息"),
        (9.65, 1.35, 1.85, "结果回填与索引更新", "任务状态回填、文件关联"),
        (11.85, 1.35, 1.75, "结果查询与可视化", "预览、对比分析、下载"),
        (4.85, 1.35, 1.55, "原始点云数据", "输入数据存储"),
    ]

    box_bounds_map: dict[str, tuple[float, float, float, float]] = {}
    for center_x, center_y, box_width, title_line, subtitle_line in box_specs:
        box_bounds_map[title_line] = add_box(
            center_x, center_y, box_width, title_line, subtitle_line
        )

    def box_right(title_line: str) -> float:
        left, _bottom, width, _height = box_bounds_map[title_line]
        return left + width

    def box_left(title_line: str) -> float:
        left, _bottom, _width, _height = box_bounds_map[title_line]
        return left

    def box_center(title_line: str) -> tuple[float, float]:
        left, bottom, width, height = box_bounds_map[title_line]
        return left + width / 2, bottom + height / 2

    def add_arrow(
        start_xy: tuple[float, float],
        end_xy: tuple[float, float],
        *,
        dashed: bool = False,
    ) -> None:
        linestyle = (0, (5, 4)) if dashed else "solid"
        arrow = FancyArrowPatch(
            start_xy,
            end_xy,
            arrowstyle="-|>",
            mutation_scale=12,
            linewidth=1.6,
            color="#4b5563",
            linestyle=linestyle,
            zorder=1,
        )
        axis.add_patch(arrow)

    submit_cx, submit_cy = box_center("任务提交")
    validate_cx, validate_cy = box_center("请求校验与建档")
    schedule_cx, schedule_cy = box_center("任务编排与调度")
    algo_cx, algo_cy = box_center("算法处理执行")
    result_gen_cx, result_gen_cy = box_center("结果生成")
    backfill_cx, backfill_cy = box_center("结果回填与索引更新")
    visualize_cx, visualize_cy = box_center("结果查询与可视化")
    raw_cx, raw_cy = box_center("原始点云数据")

    add_arrow((box_right("任务提交"), submit_cy), (box_left("请求校验与建档"), validate_cy))
    add_arrow((box_right("请求校验与建档"), validate_cy), (box_left("任务编排与调度"), schedule_cy))
    add_arrow((box_right("任务编排与调度"), schedule_cy), (box_left("算法处理执行"), algo_cy))
    add_arrow((box_right("算法处理执行"), algo_cy), (box_left("结果生成"), result_gen_cy))
    add_arrow((result_gen_cx, box_bounds_map["结果生成"][1]), (backfill_cx, box_bounds_map["结果回填与索引更新"][1] + 0.52))
    add_arrow((box_right("结果回填与索引更新"), backfill_cy), (box_left("结果查询与可视化"), visualize_cy))
    add_arrow((raw_cx + 0.4, box_bounds_map["原始点云数据"][1] + 0.52), (algo_cx - 0.3, algo_cy - 0.26), dashed=True)

    footnote_text = (
        "说明：本图为设计层总体数据流；接口路径、HTTP 状态码、轮询策略等实现细节见第四章。"
    )
    axis.text(
        0.35,
        0.12,
        footnote_text,
        fontsize=8.5,
        color="#6b7280",
        ha="left",
        va="bottom",
    )

    output_dir.mkdir(parents=True, exist_ok=True)
    png_path = output_dir / "chapter3_overall_dataflow.png"
    svg_path = output_dir / "chapter3_overall_dataflow.svg"
    figure.savefig(png_path, format="png")
    figure.savefig(svg_path, format="svg")
    plt.close(figure)
    print(f"Wrote {png_path}")
    print(f"Wrote {svg_path}")


def main() -> int:
    configure_fonts()
    script_dir = Path(__file__).resolve().parent
    images_dir = script_dir / "images"
    draw_overall_dataflow(images_dir)
    return 0


if __name__ == "__main__":
    sys.exit(main())
