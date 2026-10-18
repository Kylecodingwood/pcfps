#!/usr/bin/env python3
"""
第四章业务实现 — 各小节配套流程图（PNG + SVG）。

Outputs under docs/thesis/images/:
  chapter4_fig4_1_filter_sequence.*
  chapter4_fig4_2_task_state_machine.*
  chapter4_fig4_3_scheduler_pipeline.*
  chapter4_fig4_4_data_persistence.*
  chapter4_fig4_5_backend_orchestration.*
  chapter4_fig4_6_filter_task_flow.*
  chapter4_fig4_7_sor_ror_algorithm.*
  chapter4_fig4_8_derived_task_flow.*
  chapter4_fig4_9_semantic_prune_flow.*
  chapter4_fig4_10_euclidean_segment.*
  chapter4_fig4_11_region_grow_segment.*
  chapter4_fig4_12_pmf_classify.*
  chapter4_fig4_13_csf_classify.*

Requires: matplotlib
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Sequence


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


def save_figure(figure, output_dir: Path, base_name: str) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    png_path = output_dir / f"{base_name}.png"
    svg_path = output_dir / f"{base_name}.svg"
    figure.savefig(png_path, format="png")
    figure.savefig(svg_path, format="svg")
    import matplotlib.pyplot as plt

    plt.close(figure)
    print(f"Wrote {png_path}")
    print(f"Wrote {svg_path}")


def draw_horizontal_flow(
    title_text: str,
    step_label_list: Sequence[str],
    *,
    figsize: tuple[float, float] = (13.5, 2.8),
    box_width: float = 1.55,
    box_height: float = 0.72,
    y_center: float = 0.5,
) -> "matplotlib.figure.Figure":
    import matplotlib.pyplot as plt
    from matplotlib.patches import FancyArrowPatch, Rectangle

    step_count = len(step_label_list)
    gap = 0.35
    total_width = step_count * box_width + (step_count - 1) * gap + 1.2
    figure, axis = plt.subplots(figsize=figsize)
    axis.set_xlim(0, total_width)
    axis.set_ylim(0, 1.2)
    axis.axis("off")
    figure.suptitle(title_text, fontsize=14, fontweight="bold", y=0.98)

    start_x = 0.6
    for step_index, step_label in enumerate(step_label_list):
        box_left = start_x + step_index * (box_width + gap)
        box_bottom = y_center - box_height / 2
        axis.add_patch(
            Rectangle(
                (box_left, box_bottom),
                box_width,
                box_height,
                facecolor="#ffffff",
                edgecolor="#3b82f6",
                linewidth=1.3,
                zorder=2,
            )
        )
        axis.text(
            box_left + box_width / 2,
            y_center,
            step_label,
            ha="center",
            va="center",
            fontsize=8.5,
            color="#111827",
            zorder=3,
        )
        if step_index < step_count - 1:
            arrow_start_x = box_left + box_width
            arrow_end_x = box_left + box_width + gap
            axis.add_patch(
                FancyArrowPatch(
                    (arrow_start_x + 0.02, y_center),
                    (arrow_end_x - 0.02, y_center),
                    arrowstyle="-|>",
                    mutation_scale=11,
                    linewidth=1.4,
                    color="#4b5563",
                )
            )
    return figure


def draw_fig4_1_filter_sequence(output_dir: Path) -> None:
    import matplotlib.pyplot as plt
    from matplotlib.patches import FancyArrowPatch, Rectangle

    figure, axis = plt.subplots(figsize=(14, 6.2))
    axis.set_xlim(0, 14)
    axis.set_ylim(0, 6.2)
    axis.axis("off")
    figure.suptitle("图4-1  滤波主链路实现时序（泳道）", fontsize=14, fontweight="bold", y=0.98)

    lane_specs = [
        ("用户与前端层", 5.0, "#f8fafc"),
        ("Spring Boot 编排层", 3.6, "#eff6ff"),
        ("Python 算法网关", 2.2, "#f0fdf4"),
        ("数据与文件层", 0.8, "#fafafa"),
    ]
    lane_height = 0.95
    lane_left = 1.4
    lane_width = 12.0

    for lane_label, lane_y, lane_color in lane_specs:
        axis.add_patch(
            Rectangle(
                (lane_left, lane_y - lane_height / 2),
                lane_width,
                lane_height,
                facecolor=lane_color,
                edgecolor="#cbd5e1",
                linewidth=0.9,
            )
        )
        axis.text(0.2, lane_y, lane_label, fontsize=9, fontweight="bold", va="center", color="#374151")

    node_list = [
        (2.5, 5.0, "提交滤波任务\nJWT + LAS 路径"),
        (5.0, 3.6, "创建 FilterTask\nPENDING"),
        (7.3, 3.6, "POST /jobs"),
        (9.4, 2.2, "HTTP 202\nSOR/ROR"),
        (11.2, 2.2, "写 filtered.las"),
        (9.2, 3.6, "GET /jobs/{id}"),
        (6.8, 3.6, "SUCCEEDED\n回填"),
        (4.0, 5.0, "comparison_bundle"),
        (10.8, 0.8, "input / filtered"),
    ]
    for center_x, center_y, node_label in node_list:
        box_width = 1.85
        box_height = 0.5
        axis.add_patch(
            Rectangle(
                (center_x - box_width / 2, center_y - box_height / 2),
                box_width,
                box_height,
                facecolor="#ffffff",
                edgecolor="#3b82f6",
                linewidth=1.2,
            )
        )
        axis.text(center_x, center_y, node_label, ha="center", va="center", fontsize=7.5)

    arrow_pairs = [
        ((3.45, 5.0), (4.05, 5.0)),
        ((3.45, 4.72), (4.15, 3.88)),
        ((5.95, 3.6), (6.35, 3.6)),
        ((8.15, 3.6), (8.55, 2.48)),
        ((10.25, 2.2), (10.65, 2.2)),
        ((10.25, 2.48), (9.2, 3.32)),
        ((8.55, 3.6), (7.75, 3.6)),
        ((6.25, 3.6), (4.85, 4.72)),
        ((11.2, 1.92), (10.8, 1.08)),
    ]
    for start_xy, end_xy in arrow_pairs:
        axis.add_patch(
            FancyArrowPatch(
                start_xy,
                end_xy,
                arrowstyle="-|>",
                mutation_scale=10,
                linewidth=1.3,
                color="#475569",
            )
        )
    save_figure(figure, output_dir, "chapter4_fig4_1_filter_sequence")


def draw_fig4_2_task_state_machine(output_dir: Path) -> None:
    import matplotlib.pyplot as plt
    from matplotlib.patches import Circle, FancyArrowPatch, Rectangle

    figure, axis = plt.subplots(figsize=(10, 5.5))
    axis.set_xlim(0, 10)
    axis.set_ylim(0, 5.5)
    axis.axis("off")
    figure.suptitle("图4-2  任务状态机", fontsize=14, fontweight="bold", y=0.98)

    states = [
        (2.0, 3.0, "PENDING\n待执行"),
        (5.0, 3.0, "RUNNING\n执行中"),
        (8.0, 3.8, "SUCCEEDED\n成功"),
        (8.0, 2.0, "FAILED\n失败"),
    ]
    for cx, cy, label in states:
        axis.add_patch(Circle((cx, cy), 0.55, facecolor="#ffffff", edgecolor="#3b82f6", linewidth=1.4))
        axis.text(cx, cy, label, ha="center", va="center", fontsize=9)

    transitions = [
        ((2.55, 3.0), (4.45, 3.0), "调度派发\nPOST 作业"),
        ((5.55, 3.0), (7.45, 3.65), "网关成功\n+文件登记"),
        ((5.55, 3.0), (7.45, 2.35), "网关失败"),
        ((2.0, 2.45), (7.45, 2.0), "派发/回填异常"),
        ((5.0, 2.45), (7.45, 2.0), "轮询异常"),
    ]
    for start_xy, end_xy, edge_label in transitions:
        axis.add_patch(
            FancyArrowPatch(
                start_xy,
                end_xy,
                arrowstyle="-|>",
                mutation_scale=11,
                linewidth=1.3,
                color="#475569",
                connectionstyle="arc3,rad=0.12",
            )
        )
        mid_x = (start_xy[0] + end_xy[0]) / 2
        mid_y = (start_xy[1] + end_xy[1]) / 2
        axis.text(mid_x, mid_y + 0.15, edge_label, fontsize=7.5, ha="center", color="#64748b")

    axis.text(5.0, 0.5, "状态由 TaskService 统一更新，与外部作业结果强绑定", ha="center", fontsize=9, color="#6b7280")
    save_figure(figure, output_dir, "chapter4_fig4_2_task_state_machine")


def draw_fig4_3_scheduler_pipeline(output_dir: Path) -> None:
    figure = draw_horizontal_flow(
        "图4-3  定时调度与并发控制流程",
        [
            "调度节拍\n(2s)",
            "统计 RUNNING\n任务数",
            "未达并发上限?",
            "锁定 PENDING\nPOST 作业",
            "轮询 RUNNING\nGET 状态",
            "成功/失败\n回填",
        ],
        figsize=(14, 2.9),
    )
    save_figure(figure, output_dir, "chapter4_fig4_3_scheduler_pipeline")


def draw_fig4_4_data_persistence(output_dir: Path) -> None:
    import matplotlib.pyplot as plt
    from matplotlib.patches import FancyArrowPatch, Rectangle

    figure, axis = plt.subplots(figsize=(11, 6))
    axis.set_xlim(0, 11)
    axis.set_ylim(0, 6)
    axis.axis("off")
    figure.suptitle("图4-4  数据持久化与文件组织", fontsize=14, fontweight="bold", y=0.98)

    entities = [
        (2.0, 4.5, "User\n用户账户"),
        (5.5, 4.5, "FilterTask\n任务 + JSONB 快照"),
        (9.0, 4.5, "FileAsset\n文件资产/角色"),
        (5.5, 2.0, "output/{taskId}/\nfiltered.las / derived.las"),
        (2.0, 2.0, "登记 LAS 路径\n(输入不在 output)"),
    ]
    for cx, cy, label in entities:
        axis.add_patch(
            Rectangle(
                (cx - 1.1, cy - 0.45),
                2.2,
                0.9,
                facecolor="#ffffff",
                edgecolor="#3b82f6",
                linewidth=1.2,
            )
        )
        axis.text(cx, cy, label, ha="center", va="center", fontsize=8.5)

    for start_xy, end_xy, lbl in [
        ((3.1, 4.5), (4.4, 4.5), "1:N"),
        ((6.6, 4.5), (7.9, 4.5), "1:N"),
        ((5.5, 4.05), (5.5, 2.45), "任务目录"),
        ((3.1, 2.0), (4.4, 4.05), "input 路径"),
    ]:
        axis.add_patch(
            FancyArrowPatch(
                start_xy,
                end_xy,
                arrowstyle="-|>",
                mutation_scale=10,
                linewidth=1.2,
                color="#475569",
            )
        )
        axis.text((start_xy[0] + end_xy[0]) / 2, (start_xy[1] + end_xy[1]) / 2 + 0.12, lbl, fontsize=7.5, ha="center")
    save_figure(figure, output_dir, "chapter4_fig4_4_data_persistence")


def draw_fig4_5_backend_orchestration(output_dir: Path) -> None:
    figure = draw_horizontal_flow(
        "图4-5  后端三层编排与网关抽象",
        [
            "Controller\nREST 接入",
            "TaskService\n业务编排",
            "JPA Repository\n持久化",
            "PythonGatewayService\nHTTP 作业",
        ],
        figsize=(12, 2.6),
    )
    save_figure(figure, output_dir, "chapter4_fig4_5_backend_orchestration")


def draw_fig4_6_filter_task_flow(output_dir: Path) -> None:
    figure = draw_horizontal_flow(
        "图4-6  滤波任务业务流程",
        [
            "配置 SOR/ROR\n与参数",
            "创建 FILTER\nPENDING",
            "派发 POST /jobs",
            "写 filtered.las",
            "登记 FILTERED_LAS",
            "comparison_bundle",
        ],
        figsize=(14, 2.8),
    )
    save_figure(figure, output_dir, "chapter4_fig4_6_filter_task_flow")


def draw_fig4_7_sor_ror_algorithm(output_dir: Path) -> None:
    import matplotlib.pyplot as plt
    from matplotlib.patches import FancyArrowPatch, Rectangle

    figure, axis = plt.subplots(figsize=(12, 5))
    axis.set_xlim(0, 12)
    axis.set_ylim(0, 5)
    axis.axis("off")
    figure.suptitle("图4-7  滤波算法处理流程（SOR / ROR）", fontsize=14, fontweight="bold", y=0.98)

    steps = [
        (2.0, 3.5, "laspy 读取 LAS"),
        (5.0, 3.5, "NumPy 坐标矩阵"),
        (8.0, 3.5, "方法?\nSOR / ROR"),
        (3.5, 1.8, "cKDTree\nk 近邻 + 阈值"),
        (8.5, 1.8, "BallTree\n半径邻域计数"),
        (6.0, 0.6, "布尔掩码写回\n(可选分块)"),
    ]
    for cx, cy, label in steps:
        axis.add_patch(
            Rectangle(
                (cx - 1.0, cy - 0.38),
                2.0,
                0.76,
                facecolor="#ffffff",
                edgecolor="#3b82f6",
                linewidth=1.2,
            )
        )
        axis.text(cx, cy, label, ha="center", va="center", fontsize=8.5)

    for start_xy, end_xy in [
        ((3.0, 3.5), (4.0, 3.5)),
        ((6.0, 3.5), (7.0, 3.5)),
        ((8.0, 3.12), (3.5, 2.18)),
        ((8.0, 3.12), (8.5, 2.18)),
        ((3.5, 1.42), (5.5, 0.98)),
        ((8.5, 1.42), (6.5, 0.98)),
    ]:
        axis.add_patch(
            FancyArrowPatch(
                start_xy,
                end_xy,
                arrowstyle="-|>",
                mutation_scale=10,
                linewidth=1.2,
                color="#475569",
            )
        )
    save_figure(figure, output_dir, "chapter4_fig4_7_sor_ror_algorithm")


def draw_fig4_8_derived_task_flow(output_dir: Path) -> None:
    figure = draw_horizontal_flow(
        "图4-8  派生任务流程（分割 / 分类）",
        [
            "父任务 SUCCEEDED\n(filtered.las)",
            "创建子任务\nsegment/classify",
            "POST /derived-jobs",
            "写 derived.las\nclassification",
            "derived_metrics\n双窗伪彩",
        ],
        figsize=(13.5, 2.8),
    )
    save_figure(figure, output_dir, "chapter4_fig4_8_derived_task_flow")


def draw_fig4_9_semantic_prune_flow(output_dir: Path) -> None:
    figure = draw_horizontal_flow(
        "图4-9  语义裁剪扩展流程",
        [
            "父分类任务\nSUCCEEDED",
            "创建 PRUNE\n子任务",
            "体素化地面精简\n剔除植被/其它",
            "写裁剪 LAS",
            "语义裁剪\n双窗对比包",
        ],
        figsize=(13, 2.8),
    )
    save_figure(figure, output_dir, "chapter4_fig4_9_semantic_prune_flow")


def draw_fig4_10_euclidean_segment(output_dir: Path) -> None:
    figure = draw_horizontal_flow(
        "图4-10  欧式聚类分割流程（DBSCAN）",
        ["读取 filtered.las", "DBSCAN 聚类", "写 classification\n(0–31)", "输出 derived.las", "伪彩双窗"],
        figsize=(12.5, 2.6),
    )
    save_figure(figure, output_dir, "chapter4_fig4_10_euclidean_segment")


def draw_fig4_11_region_grow_segment(output_dir: Path) -> None:
    figure = draw_horizontal_flow(
        "图4-11  区域生长分割流程",
        ["读取 filtered.las", "邻域生长聚类", "写 classification", "输出 derived.las", "伪彩双窗"],
        figsize=(12.5, 2.6),
    )
    save_figure(figure, output_dir, "chapter4_fig4_11_region_grow_segment")


def draw_fig4_12_pmf_classify(output_dir: Path) -> None:
    figure = draw_horizontal_flow(
        "图4-12  PMF 地面分类流程",
        ["读取 filtered.las", "渐进形态学滤波", "地面/非地面标签", "derived.las", "双窗对比"],
        figsize=(12.5, 2.6),
    )
    save_figure(figure, output_dir, "chapter4_fig4_12_pmf_classify")


def draw_fig4_13_csf_classify(output_dir: Path) -> None:
    figure = draw_horizontal_flow(
        "图4-13  CSF 地面分类流程",
        ["读取 filtered.las", "布料模拟滤波", "地面/非地面标签", "derived.las", "双窗对比"],
        figsize=(12.5, 2.6),
    )
    save_figure(figure, output_dir, "chapter4_fig4_13_csf_classify")


def main() -> int:
    configure_fonts()
    images_dir = Path(__file__).resolve().parent / "images"
    draw_fig4_1_filter_sequence(images_dir)
    draw_fig4_2_task_state_machine(images_dir)
    draw_fig4_3_scheduler_pipeline(images_dir)
    draw_fig4_4_data_persistence(images_dir)
    draw_fig4_5_backend_orchestration(images_dir)
    draw_fig4_6_filter_task_flow(images_dir)
    draw_fig4_7_sor_ror_algorithm(images_dir)
    draw_fig4_8_derived_task_flow(images_dir)
    draw_fig4_9_semantic_prune_flow(images_dir)
    draw_fig4_10_euclidean_segment(images_dir)
    draw_fig4_11_region_grow_segment(images_dir)
    draw_fig4_12_pmf_classify(images_dir)
    draw_fig4_13_csf_classify(images_dir)
    return 0


if __name__ == "__main__":
    sys.exit(main())
