import io
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.lines import Line2D
from matplotlib.transforms import blended_transform_factory
from datetime import datetime

BG      = "#1a1a2e"
FG      = "#e0e0e0"
GRID    = "#2a2a4a"
SUBGRID = "#252540"


def _apply_dark(fig, *axes):
    fig.patch.set_facecolor(BG)
    for ax in axes:
        ax.set_facecolor(BG)
        ax.tick_params(colors=FG, labelsize=9)
        ax.yaxis.label.set_color(FG)
        ax.xaxis.label.set_color(FG)
        ax.title.set_color(FG)
        ax.grid(True, linestyle="--", alpha=0.25, color=GRID)
        for spine in ["top", "right"]:
            ax.spines[spine].set_visible(False)
        for spine in ["left", "bottom"]:
            ax.spines[spine].set_color(GRID)


def _parse_dates(rows) -> list[datetime]:
    dates = []
    for r in rows:
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"):
            try:
                dates.append(datetime.strptime(r["date"], fmt))
                break
            except ValueError:
                continue
    return dates


def build_chart(rows) -> io.BytesIO:
    dates = _parse_dates(rows)
    weights = [r["weight"] for r in rows]

    fig, ax = plt.subplots(figsize=(14, 6))
    _apply_dark(fig, ax)

    color = "#4fc3f7"
    avg = sum(weights) / len(weights)
    mn  = min(weights)
    mx  = max(weights)
    pad = max((mx - mn) * 0.2, 2.0)
    ax.set_ylim(bottom=mn - pad, top=mx + pad)

    ax.fill_between(dates, weights, alpha=0.15, color=color)
    ax.plot(dates, weights, marker="o", linewidth=2, color=color,
            markersize=5, markerfacecolor=color, markeredgewidth=0)

    # подписываем только ключевые точки: первую, последнюю, минимум, максимум
    idx_mn = weights.index(mn)
    idx_mx = weights.index(mx)
    key_indices = {0, len(weights) - 1, idx_mn, idx_mx}
    for i in key_indices:
        below = (i == idx_mn)
        ax.annotate(
            f"{weights[i]:.1f}",
            (dates[i], weights[i]),
            textcoords="offset points",
            xytext=(0, -14 if below else 10),
            ha="center",
            va="top" if below else "bottom",
            fontsize=9,
            fontweight="bold",
            color=FG,
        )

    ax.axhline(avg, color="#78909c", linestyle=":",  linewidth=1.3, label=f"Среднее: {avg:.1f} кг")
    ax.axhline(mn,  color="#66bb6a", linestyle="--", linewidth=1.0, label=f"Минимум: {mn:.1f} кг")
    ax.axhline(mx,  color="#ef5350", linestyle="--", linewidth=1.0, label=f"Максимум: {mx:.1f} кг")

    ax.xaxis.set_major_locator(mdates.AutoDateLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%d.%m.%y"))
    fig.autofmt_xdate(rotation=45)

    ax.set_title("Динамика веса", fontsize=14, pad=14)
    ax.set_ylabel("Вес (кг)")
    legend = ax.legend(facecolor=BG, edgecolor=GRID, labelcolor=FG, fontsize=9)

    plt.tight_layout()
    buf = io.BytesIO()
    plt.savefig(buf, format="png", dpi=150)
    plt.close(fig)
    buf.seek(0)
    return buf


PERIOD_COLOR = {"morning": "#ef5350", "evening": "#42a5f5"}
REF_STYLE = {"avg": ("#b0bec5", ":"), "min": ("#4db6ac", "--"), "max": ("#ffb74d", "--")}


def _add_ref_lines(ax, series):
    """Полупрозрачные пунктирные линии среднего/мин/макс на всю ширину графика,
    со значением, подписанным у правого края."""
    trans = blended_transform_factory(ax.transAxes, ax.transData)
    stats = {"avg": sum(series) / len(series), "min": min(series), "max": max(series)}
    for key, value in stats.items():
        color, linestyle = REF_STYLE[key]
        ax.axhline(value, color=color, linestyle=linestyle, linewidth=1, alpha=0.6, zorder=0)
        ax.text(1.012, value, f"{value:.0f}", transform=trans, color=color,
                fontsize=8, va="center", ha="left")


def build_pressure_chart(rows) -> io.BytesIO:
    pulse_rows = [r for r in rows if r["pulse"] is not None]
    has_pulse  = bool(pulse_rows)

    if has_pulse:
        fig, (ax_p, ax_pulse) = plt.subplots(
            2, 1, figsize=(14, 8), sharex=True,
            gridspec_kw={"height_ratios": [2, 1]}
        )
        _apply_dark(fig, ax_p, ax_pulse)
    else:
        fig, ax_p = plt.subplots(figsize=(14, 6))
        _apply_dark(fig, ax_p)
        ax_pulse = None

    dates = _parse_dates(rows)
    sys_vals = [r["systolic"] for r in rows]
    dia_vals = [r["diastolic"] for r in rows]
    point_colors = [PERIOD_COLOR.get(r["period"], "#9e9e9e") for r in rows]

    ax_p.plot(dates, sys_vals, color=FG, linewidth=2.2, alpha=0.55, zorder=1)
    ax_p.plot(dates, dia_vals, color=FG, linewidth=2.2, alpha=0.55, zorder=1)
    ax_p.scatter(dates, sys_vals, c=point_colors, marker="o", s=45, zorder=3, edgecolors="none")
    ax_p.scatter(dates, dia_vals, c=point_colors, marker="^", s=40, zorder=3, edgecolors="none")

    _add_ref_lines(ax_p, sys_vals)
    _add_ref_lines(ax_p, dia_vals)

    legend_handles = [
        Line2D([0], [0], marker="o", color=FG, linewidth=2.2, alpha=0.55, markersize=6, label="Верхнее"),
        Line2D([0], [0], marker="^", color=FG, linewidth=2.2, alpha=0.55, markersize=6, label="Нижнее"),
        Line2D([0], [0], marker="o", linestyle="none", markerfacecolor=PERIOD_COLOR["morning"],
               markeredgewidth=0, markersize=8, label="Утро"),
        Line2D([0], [0], marker="o", linestyle="none", markerfacecolor=PERIOD_COLOR["evening"],
               markeredgewidth=0, markersize=8, label="Вечер"),
    ]
    ax_p.set_title("Динамика давления", fontsize=14, pad=14)
    ax_p.set_ylabel("Давление (мм рт. ст.)")
    ax_p.legend(handles=legend_handles, facecolor=BG, edgecolor=GRID, labelcolor=FG, fontsize=9, ncol=4,
                loc="upper center", bbox_to_anchor=(0.5, 1.18))

    if has_pulse:
        p_dates = _parse_dates(pulse_rows)
        pulses  = [r["pulse"] for r in pulse_rows]
        mn_p, mx_p = min(pulses), max(pulses)
        ax_pulse.set_ylim(bottom=mn_p - 10, top=mx_p + 10)
        ax_pulse.fill_between(p_dates, pulses, mn_p - 10, alpha=0.15, color="#66bb6a")
        ax_pulse.plot(p_dates, pulses, marker="^", color="#66bb6a", linewidth=2,
                      markersize=5, markeredgewidth=0, label="Пульс")
        _add_ref_lines(ax_pulse, pulses)
        ax_pulse.set_ylabel("Пульс (уд/мин)")
        ax_pulse.legend(facecolor=BG, edgecolor=GRID, labelcolor=FG, fontsize=9)

    ax_p.xaxis.set_major_locator(mdates.AutoDateLocator())
    ax_p.xaxis.set_major_formatter(mdates.DateFormatter("%d.%m.%y"))
    fig.autofmt_xdate(rotation=45)

    plt.tight_layout()
    fig.subplots_adjust(right=0.92)
    buf = io.BytesIO()
    plt.savefig(buf, format="png", dpi=150)
    plt.close(fig)
    buf.seek(0)
    return buf
