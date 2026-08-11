from __future__ import annotations

import tkinter as tk

import customtkinter as ctk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from matplotlib.ticker import FuncFormatter, MaxNLocator

from app.design_system.theme import SafeSendTheme, active_theme


CHART_BACKGROUND = "#07111F"
CHART_GRID = "#8CA0B3"
CHART_AXIS = "#6F8AA3"
CHART_TEXT = "#B8C8D8"
CHART_TITLE = "#D9E7F5"
STACK_COLORS = ("#FF9B85", "#4ECDD3", "#F5C989")
STACK_LABELS = ("Core", "Growth", "Review")


def _theme(theme: SafeSendTheme | None = None) -> SafeSendTheme:
    return theme or active_theme()


def _axis_label(value: float, _position: int | None = None) -> str:
    absolute = abs(value)
    if absolute >= 1_000_000:
        text = f"{value / 1_000_000:.1f}M"
        return text.replace("0.", ".")
    if absolute >= 1_000:
        return f"{value / 1_000:.0f}K"
    if value == 0:
        return "0"
    if float(value).is_integer():
        return str(int(value))
    return f"{value:.1f}"


def _style_chart_axes(ax, *, orientation: str = "vertical", title: str, x_axis_title: str, y_axis_title: str) -> None:
    ax.set_title(title, loc="left", color=CHART_TITLE, fontsize=10, fontweight="bold", pad=14)
    ax.set_xlabel(x_axis_title, color=CHART_TEXT, fontsize=8, labelpad=12)
    ax.set_ylabel(y_axis_title, color=CHART_TEXT, fontsize=8, labelpad=12)
    ax.tick_params(axis="both", colors=CHART_TEXT, labelsize=8, length=0, pad=8)
    ax.spines[["top", "right"]].set_visible(False)
    ax.spines["bottom"].set_color(CHART_AXIS)
    ax.spines["left"].set_color(CHART_AXIS)
    ax.spines["bottom"].set_linewidth(1.1)
    ax.spines["left"].set_linewidth(1.1)
    if orientation == "horizontal":
        ax.grid(axis="x", color=CHART_GRID, linewidth=1.0, alpha=0.72)
        ax.xaxis.set_major_locator(MaxNLocator(nbins=5))
        ax.xaxis.set_major_formatter(FuncFormatter(_axis_label))
    else:
        ax.grid(axis="y", color=CHART_GRID, linewidth=1.0, alpha=0.72)
        ax.yaxis.set_major_locator(MaxNLocator(nbins=5))
        ax.yaxis.set_major_formatter(FuncFormatter(_axis_label))
    ax.set_axisbelow(True)


def _segments(total: int | float) -> tuple[float, float, float]:
    if total <= 0:
        return (0, 0, 0)
    base = total * 0.58
    middle = total * 0.27
    final = total - base - middle
    return (base, middle, final)


class BarChart(ctk.CTkFrame):
    def __init__(
        self,
        parent: tk.Widget,
        values: list[tuple[str, int, str]],
        *,
        theme: SafeSendTheme | None = None,
        height: int = 260,
        title: str = "Workspace Sending Volume",
        x_axis_title: str = "Workspace metric",
        y_axis_title: str = "Count",
        stacked: bool = True,
    ) -> None:
        self.theme = _theme(theme)
        self.values = values
        palette = self.theme.palette
        super().__init__(parent, fg_color=palette.surface, corner_radius=0)
        self.configure(height=height)
        self.grid_propagate(False)

        fig = Figure(figsize=(6.9, 3.0), dpi=100, facecolor=CHART_BACKGROUND)
        ax = fig.add_subplot(111, facecolor=CHART_BACKGROUND)
        labels = [label for label, _value, _color in values]
        counts = [value for _label, value, _color in values]
        colors = [color for _label, _value, color in values]

        if stacked:
            bottoms = [0.0 for _ in counts]
            for index, color in enumerate(STACK_COLORS):
                segment_values = [_segments(count)[index] for count in counts]
                ax.bar(labels, segment_values, bottom=bottoms, color=color, width=0.58, label=STACK_LABELS[index])
                bottoms = [bottom + segment for bottom, segment in zip(bottoms, segment_values)]
        else:
            ax.bar(labels, counts, color=colors, width=0.58)

        max_count = max(counts + [1])
        ax.set_ylim(0, max_count * 1.34)
        _style_chart_axes(ax, title=title, x_axis_title=x_axis_title, y_axis_title=y_axis_title)
        for index, value in enumerate(counts):
            ax.text(
                index,
                value + max_count * 0.045,
                _axis_label(value),
                ha="center",
                va="bottom",
                color=CHART_TITLE,
                fontsize=9,
                fontweight="bold",
            )
        if stacked and any(counts):
            legend = ax.legend(
                loc="upper right",
                bbox_to_anchor=(1, 1.18),
                frameon=False,
                ncols=3,
                fontsize=7,
                labelcolor=CHART_TEXT,
                handlelength=1.2,
                columnspacing=1.1,
            )
            for text in legend.get_texts():
                text.set_color(CHART_TEXT)
        fig.subplots_adjust(left=0.09, right=0.98, bottom=0.24, top=0.82)

        self.canvas = FigureCanvasTkAgg(fig, master=self)
        self.canvas.draw()
        widget = self.canvas.get_tk_widget()
        widget.configure(bg=CHART_BACKGROUND, highlightthickness=0, bd=0)
        widget.pack(fill="both", expand=True)


class HorizontalStackedBarChart(ctk.CTkFrame):
    def __init__(
        self,
        parent: tk.Widget,
        values: list[tuple[str, int, str]],
        *,
        theme: SafeSendTheme | None = None,
        height: int = 260,
        title: str = "Campaign Performance",
        x_axis_title: str = "Volume",
        y_axis_title: str = "Segment",
    ) -> None:
        self.theme = _theme(theme)
        palette = self.theme.palette
        super().__init__(parent, fg_color=palette.surface, corner_radius=0)
        self.configure(height=height)
        self.grid_propagate(False)

        labels = [label for label, _value, _color in values]
        counts = [value for _label, value, _color in values]
        fig = Figure(figsize=(6.9, 3.0), dpi=100, facecolor=CHART_BACKGROUND)
        ax = fig.add_subplot(111, facecolor=CHART_BACKGROUND)

        lefts = [0.0 for _ in counts]
        for index, color in enumerate(STACK_COLORS):
            segment_values = [_segments(count)[index] for count in counts]
            ax.barh(labels, segment_values, left=lefts, color=color, height=0.46, label=STACK_LABELS[index])
            lefts = [left + segment for left, segment in zip(lefts, segment_values)]

        max_count = max(counts + [1])
        ax.set_xlim(0, max_count * 1.24)
        ax.invert_yaxis()
        _style_chart_axes(ax, orientation="horizontal", title=title, x_axis_title=x_axis_title, y_axis_title=y_axis_title)
        if any(counts):
            legend = ax.legend(
                loc="upper right",
                bbox_to_anchor=(1, 1.18),
                frameon=False,
                ncols=3,
                fontsize=7,
                labelcolor=CHART_TEXT,
                handlelength=1.2,
                columnspacing=1.1,
            )
            for text in legend.get_texts():
                text.set_color(CHART_TEXT)
        fig.subplots_adjust(left=0.13, right=0.98, bottom=0.22, top=0.82)

        self.canvas = FigureCanvasTkAgg(fig, master=self)
        self.canvas.draw()
        widget = self.canvas.get_tk_widget()
        widget.configure(bg=CHART_BACKGROUND, highlightthickness=0, bd=0)
        widget.pack(fill="both", expand=True)


class ReputationDonut(ctk.CTkFrame):
    def __init__(
        self,
        parent: tk.Widget,
        score: int,
        *,
        theme: SafeSendTheme | None = None,
        size: int = 126,
        background: str | None = None,
        text_color: str | None = None,
        nested: bool = True,
    ) -> None:
        self.theme = _theme(theme)
        palette = self.theme.palette
        bg = background or palette.surface
        fg = text_color or palette.text
        score = max(0, min(100, int(score)))
        super().__init__(parent, fg_color=bg, corner_radius=0)
        self.configure(width=size, height=size)
        self.pack_propagate(False)

        fig = Figure(figsize=(size / 100, size / 100), dpi=100, facecolor=bg)
        ax = fig.add_subplot(111, facecolor=bg)
        remainder = 100 - score
        ring_track = "#425B76" if bg.startswith("#2") else palette.border_soft
        ax.pie(
            [score, remainder],
            radius=1.0,
            startangle=90,
            counterclock=False,
            colors=[palette.success, ring_track],
            wedgeprops={"width": 0.18, "edgecolor": bg, "linewidth": 2},
        )
        if nested:
            ax.pie(
                [42, 30, 20, 8],
                radius=0.74,
                startangle=90,
                counterclock=False,
                colors=[palette.success, palette.info, palette.warning, ring_track],
                wedgeprops={"width": 0.14, "edgecolor": bg, "linewidth": 2},
            )
        ax.text(0, 0.08, str(score), ha="center", va="center", color=fg, fontsize=max(14, int(size * 0.18)), fontweight="bold")
        ax.text(0, -0.23, _score_label(score), ha="center", va="center", color=palette.success, fontsize=max(6, int(size * 0.065)))
        ax.set(aspect="equal")
        ax.axis("off")
        fig.subplots_adjust(0.02, 0.02, 0.98, 0.98)

        self.canvas = FigureCanvasTkAgg(fig, master=self)
        self.canvas.draw()
        widget = self.canvas.get_tk_widget()
        widget.configure(bg=bg, highlightthickness=0, bd=0)
        widget.pack(fill="both", expand=True)


def _score_label(score: int) -> str:
    if score >= 90:
        return "Excellent"
    if score >= 75:
        return "Healthy"
    if score >= 55:
        return "Watch"
    return "Risk"
