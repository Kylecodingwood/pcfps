#!/usr/bin/env python3
"""
Generate a Ball tree query illustration (2D only, no subplot title).

Fixed root ball; left/right training points outside the root ball are removed;
yellow note box uses high z-order. Narrative text for the thesis is maintained
in docs/thesis/ball_tree_knn_query_paragraph.md.

Outputs:
  docs/thesis/images/ball_tree_query_process.png
  docs/thesis/images/ball_tree_query_process.svg

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
            "savefig.pad_inches": 0.25,
        }
    )


def draw_ball_tree_query(output_dir: Path) -> None:
    import matplotlib.pyplot as plt
    import numpy as np
    from matplotlib.patches import Circle, FancyBboxPatch

    figure_width_inches = 6.8
    figure_height_inches = 5.35
    fig, ax_geo = plt.subplots(1, 1, figsize=(figure_width_inches, figure_height_inches))

    ax_geo.set_aspect("equal")
    margin = 0.35
    ax_geo.set_xlim(-0.2 - margin, 5.2 + margin)
    ax_geo.set_ylim(-0.2 - margin, 4.2 + margin)
    ax_geo.set_xlabel("x", fontsize=11)
    ax_geo.set_ylabel("y", fontsize=11)
    ax_geo.grid(True, linestyle=":", alpha=0.45)

    # 子树球（示意）：左 / 右子集各一颗闭球
    left_center = np.array([1.35, 1.25])
    left_radius = 1.15
    right_center = np.array([3.85, 2.35])
    right_radius = 1.05

    points_left = np.array(
        [
            [0.55, 0.55],
            [0.9, 1.55],
            [1.75, 0.65],
            [1.55, 1.95],
            [0.85, 0.95],
        ]
    )
    points_right = np.array(
        [
            [3.15, 1.55],
            [3.55, 2.95],
            [4.45, 2.05],
            [4.2, 3.15],
            [3.35, 2.25],
        ]
    )

    query_point = np.array([4.65, 0.55])

    # 与论文截图一致：固定根球（根结点包含全树训练点）
    root_center = np.array([2.6, 2.0])
    root_radius = 2.05

    def points_inside_ball(point_xy: np.ndarray, ball_center: np.ndarray, ball_radius: float) -> np.ndarray:
        distance_list = np.linalg.norm(point_xy - ball_center, axis=1)
        return distance_list <= ball_radius - 1e-9

    points_left = points_left[points_inside_ball(points_left, root_center, root_radius)]
    points_right = points_right[points_inside_ball(points_right, root_center, root_radius)]

    root_ball = Circle(
        root_center,
        root_radius,
        fill=False,
        edgecolor="#2b6cb0",
        linewidth=2.2,
        linestyle="-",
        label="根结点球 B_root",
        zorder=1,
    )
    left_ball = Circle(
        left_center,
        left_radius,
        fill=False,
        edgecolor="#276749",
        linewidth=1.6,
        linestyle="--",
        label="左子树球 B_L",
        zorder=2,
    )
    right_ball = Circle(
        right_center,
        right_radius,
        fill=False,
        edgecolor="#c05621",
        linewidth=1.6,
        linestyle="--",
        label="右子树球 B_R",
        zorder=2,
    )

    ax_geo.add_patch(root_ball)
    ax_geo.add_patch(left_ball)
    ax_geo.add_patch(right_ball)

    ax_geo.scatter(
        points_left[:, 0],
        points_left[:, 1],
        c="#276749",
        s=38,
        zorder=4,
        edgecolors="white",
        linewidths=0.6,
        label="左子树点",
    )
    ax_geo.scatter(
        points_right[:, 0],
        points_right[:, 1],
        c="#c05621",
        s=38,
        zorder=4,
        edgecolors="white",
        linewidths=0.6,
        label="右子树点",
    )
    ax_geo.scatter(
        [query_point[0]],
        [query_point[1]],
        c="#e53e3e",
        s=120,
        marker="*",
        zorder=6,
        edgecolors="#742a2a",
        linewidths=0.8,
        label="查询点 q",
    )

    ax_geo.plot(
        [query_point[0], root_center[0]],
        [query_point[1], root_center[1]],
        color="#805ad5",
        linewidth=1.0,
        linestyle=":",
        zorder=3,
    )
    ax_geo.plot(
        [query_point[0], right_center[0]],
        [query_point[1], right_center[1]],
        color="#dd6b20",
        linewidth=0.9,
        linestyle=":",
        zorder=3,
    )

    ax_geo.annotate(
        "c_root",
        xy=root_center,
        xytext=(root_center[0] - 0.55, root_center[1] + 0.55),
        fontsize=9,
        color="#2b6cb0",
        zorder=5,
        arrowprops=dict(arrowstyle="-|>", color="#2b6cb0", lw=0.8),
    )
    ax_geo.annotate(
        "c_R",
        xy=right_center,
        xytext=(right_center[0] + 0.35, right_center[1] + 0.65),
        fontsize=9,
        color="#c05621",
        zorder=5,
        arrowprops=dict(arrowstyle="-|>", color="#c05621", lw=0.8),
    )
    ax_geo.text(
        query_point[0] + 0.12,
        query_point[1] + 0.12,
        "q",
        fontsize=11,
        color="#c53030",
        fontweight="bold",
        zorder=7,
    )

    legend_geo = ax_geo.legend(loc="upper left", fontsize=8, framealpha=0.92)
    legend_geo.get_frame().set_linewidth(0.6)
    legend_geo.set_zorder(50)

    note_z = 200
    note_box = FancyBboxPatch(
        (0.02, 0.02),
        0.46,
        0.28,
        transform=ax_geo.transAxes,
        boxstyle="round,pad=0.02,rounding_size=0.05",
        facecolor="#fffaf0",
        edgecolor="#744210",
        linewidth=0.9,
        zorder=note_z,
    )
    ax_geo.add_patch(note_box)
    note_text = ax_geo.text(
        0.25,
        0.15,
        "下界：LB(B)=max(0, d(q,c)-r)\n若 LB 大于当前第 k 近邻上界则可剪枝",
        transform=ax_geo.transAxes,
        fontsize=7.8,
        va="center",
        ha="center",
        color="#4a5568",
        linespacing=1.35,
        zorder=note_z + 1,
    )

    out_png = output_dir / "ball_tree_query_process.png"
    out_svg = output_dir / "ball_tree_query_process.svg"
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

    draw_ball_tree_query(output_dir)
    print("Wrote:")
    print(" ", output_dir / "ball_tree_query_process.png")
    print(" ", output_dir / "ball_tree_query_process.svg")
    print("Narrative (thesis):", repo_root / "docs" / "thesis" / "ball_tree_knn_query_paragraph.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
