import io
import matplotlib
matplotlib.use("Agg")  # без GUI
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime


def build_chart(rows) -> io.BytesIO:
    dates = [datetime.strptime(r["date"], "%Y-%m-%d %H:%M") for r in rows]
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
