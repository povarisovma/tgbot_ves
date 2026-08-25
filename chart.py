import io
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime


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

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(dates, weights, marker="o", linewidth=2, color="#4A90D9", markersize=6)

    # подписи точек
    for d, w in zip(dates, weights):
        ax.annotate(
            f"{w:.1f}",
            (d, w),
            textcoords="offset points",
            xytext=(0, 10),
            ha="center",
            fontsize=8,
            color="#333333",
        )

    ax.xaxis.set_major_formatter(mdates.DateFormatter("%d.%m.%y"))
    fig.autofmt_xdate(rotation=45)

    ax.set_title("Динамика веса", fontsize=14, pad=12)
    ax.set_ylabel("Вес (кг)")
    ax.set_xlabel("Дата")
    ax.grid(True, linestyle="--", alpha=0.5)

    # горизонтальная линия — среднее
    avg = sum(weights) / len(weights)
    ax.axhline(avg, color="gray", linestyle=":", linewidth=1.2,
               label=f"Среднее: {avg:.1f} кг")
    ax.legend()

    plt.tight_layout()

    buf = io.BytesIO()
    plt.savefig(buf, format="png", dpi=150)
    plt.close(fig)
    buf.seek(0)
    return buf


def build_pressure_chart(rows) -> io.BytesIO:
    morning = [r for r in rows if r["period"] == "morning"]
    evening = [r for r in rows if r["period"] == "evening"]
    pulse_rows = [r for r in rows if r["pulse"] is not None]
    has_pulse = bool(pulse_rows)

    if has_pulse:
        fig, (ax_p, ax_pulse) = plt.subplots(
            2, 1, figsize=(12, 8), sharex=True,
            gridspec_kw={"height_ratios": [2, 1]}
        )
    else:
        fig, ax_p = plt.subplots(figsize=(12, 5))
        ax_pulse = None

    if morning:
        m_dates = _parse_dates(morning)
        ax_p.plot(m_dates, [r["systolic"] for r in morning],
                  marker="o", color="#E74C3C", linewidth=2, label="Утро верхнее")
        ax_p.plot(m_dates, [r["diastolic"] for r in morning],
                  marker="o", color="#F1948A", linewidth=2, linestyle="--", label="Утро нижнее")

    if evening:
        e_dates = _parse_dates(evening)
        ax_p.plot(e_dates, [r["systolic"] for r in evening],
                  marker="s", color="#2E86C1", linewidth=2, label="Вечер верхнее")
        ax_p.plot(e_dates, [r["diastolic"] for r in evening],
                  marker="s", color="#85C1E9", linewidth=2, linestyle="--", label="Вечер нижнее")

    ax_p.set_title("Динамика давления", fontsize=14, pad=12)
    ax_p.set_ylabel("Давление (мм рт. ст.)")
    ax_p.grid(True, linestyle="--", alpha=0.5)
    ax_p.legend()

    if has_pulse:
        p_dates = _parse_dates(pulse_rows)
        ax_pulse.plot(p_dates, [r["pulse"] for r in pulse_rows],
                      marker="^", color="#27AE60", linewidth=2, label="Пульс")
        ax_pulse.set_ylabel("Пульс (уд/мин)")
        ax_pulse.grid(True, linestyle="--", alpha=0.5)
        ax_pulse.legend()

    ax_p.xaxis.set_major_formatter(mdates.DateFormatter("%d.%m.%y"))
    fig.autofmt_xdate(rotation=45)
    plt.tight_layout()

    buf = io.BytesIO()
    plt.savefig(buf, format="png", dpi=150)
    plt.close(fig)
    buf.seek(0)
    return buf
