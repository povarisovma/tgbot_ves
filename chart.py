import io
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
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
    ax.fill_between(dates, weights, alpha=0.15, color=color)
    ax.plot(dates, weights, marker="o", linewidth=2, color=color,
            markersize=5, markerfacecolor=color, markeredgewidth=0)

    if len(rows) <= 25:
        for d, w in zip(dates, weights):
            ax.annotate(
                f"{w:.1f}",
                (d, w),
                textcoords="offset points",
                xytext=(0, 10),
                ha="center",
                fontsize=8,
                color=FG,
            )

    avg = sum(weights) / len(weights)
    ax.axhline(avg, color="#78909c", linestyle=":", linewidth=1.3,
               label=f"Среднее: {avg:.1f} кг")

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


def build_pressure_chart(rows) -> io.BytesIO:
    morning   = [r for r in rows if r["period"] == "morning"]
    evening   = [r for r in rows if r["period"] == "evening"]
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

    if morning:
        m_dates = _parse_dates(morning)
        m_sys = [r["systolic"] for r in morning]
        m_dia = [r["diastolic"] for r in morning]
        ax_p.fill_between(m_dates, m_sys, m_dia, alpha=0.08, color="#ef5350")
        ax_p.plot(m_dates, m_sys, marker="o", color="#ef5350", linewidth=2,
                  markersize=5, markeredgewidth=0, label="Утро верхнее")
        ax_p.plot(m_dates, m_dia, marker="o", color="#ef9a9a", linewidth=2,
                  markersize=5, markeredgewidth=0, linestyle="--", label="Утро нижнее")

    if evening:
        e_dates = _parse_dates(evening)
        e_sys = [r["systolic"] for r in evening]
        e_dia = [r["diastolic"] for r in evening]
        ax_p.fill_between(e_dates, e_sys, e_dia, alpha=0.08, color="#42a5f5")
        ax_p.plot(e_dates, e_sys, marker="s", color="#42a5f5", linewidth=2,
                  markersize=5, markeredgewidth=0, label="Вечер верхнее")
        ax_p.plot(e_dates, e_dia, marker="s", color="#90caf9", linewidth=2,
                  markersize=5, markeredgewidth=0, linestyle="--", label="Вечер нижнее")

    ax_p.set_title("Динамика давления", fontsize=14, pad=14)
    ax_p.set_ylabel("Давление (мм рт. ст.)")
    ax_p.legend(facecolor=BG, edgecolor=GRID, labelcolor=FG, fontsize=9, ncol=2)

    if has_pulse:
        p_dates = _parse_dates(pulse_rows)
        pulses  = [r["pulse"] for r in pulse_rows]
        ax_pulse.fill_between(p_dates, pulses, alpha=0.15, color="#66bb6a")
        ax_pulse.plot(p_dates, pulses, marker="^", color="#66bb6a", linewidth=2,
                      markersize=5, markeredgewidth=0, label="Пульс")
        ax_pulse.set_ylabel("Пульс (уд/мин)")
        ax_pulse.legend(facecolor=BG, edgecolor=GRID, labelcolor=FG, fontsize=9)

    ax_p.xaxis.set_major_locator(mdates.AutoDateLocator())
    ax_p.xaxis.set_major_formatter(mdates.DateFormatter("%d.%m.%y"))
    fig.autofmt_xdate(rotation=45)

    plt.tight_layout()
    buf = io.BytesIO()
    plt.savefig(buf, format="png", dpi=150)
    plt.close(fig)
    buf.seek(0)
    return buf
