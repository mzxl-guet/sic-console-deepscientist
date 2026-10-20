from pathlib import Path

import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


FS = 8000.0
DURATION = 1.0
FREQ = 440.0
AMPLITUDE = 0.8
Q_LIST = [8, 10, 12, 16]
OUTPUT_DIR = Path(__file__).resolve().parent / "outputs"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def quantize_uniform(signal, bits):
    levels = 2 ** bits
    step = 2.0 / levels
    quantized = np.clip(np.round(signal / step) * step, -1.0, 1.0)
    return quantized, step


def sqnr_db(signal, quantized):
    signal_power = float(np.mean(signal ** 2))
    noise_power = float(np.mean((quantized - signal) ** 2))
    return 10.0 * np.log10(signal_power / noise_power), signal_power, noise_power


n = int(FS * DURATION)
time = np.arange(n) / FS
signal = AMPLITUDE * np.sin(2.0 * np.pi * FREQ * time)

rows = []
quantized_by_bits = {}
step_by_bits = {}
for bits in Q_LIST:
    quantized, step = quantize_uniform(signal, bits)
    measured, signal_power, noise_power = sqnr_db(signal, quantized)
    theory_full_scale = 6.02 * bits + 1.76
    theory_amplitude_adjusted = theory_full_scale + 20.0 * np.log10(AMPLITUDE)
    quantized_by_bits[bits] = quantized
    step_by_bits[bits] = step
    rows.append(
        {
            "Q": bits,
            "theory_sqnr_db": theory_full_scale,
            "measured_sqnr_db": measured,
            "difference_db": measured - theory_full_scale,
            "theory_amplitude_adjusted_db": theory_amplitude_adjusted,
            "difference_vs_adjusted_db": measured - theory_amplitude_adjusted,
            "signal_power": signal_power,
            "noise_power": noise_power,
            "step": step,
        }
    )

# Figure 1: original waveform and 8-bit stair-step waveform over the first 20 ms.
first_20ms = int(0.020 * FS)
t_zoom = time[:first_20ms]
plt.figure(figsize=(10, 5.2))
plt.plot(t_zoom * 1e3, signal[:first_20ms], color="#1f77b4", linewidth=1.8, label="Original signal")
plt.step(
    t_zoom * 1e3,
    quantized_by_bits[8][:first_20ms],
    where="post",
    color="#d62728",
    linewidth=1.5,
    label="8-bit quantized signal",
)
plt.title("Uniform Quantization of a 440 Hz Sine Wave (first 20 ms)")
plt.xlabel("Time (ms)")
plt.ylabel("Amplitude")
plt.xlim(0.0, 20.0)
plt.ylim(-0.9, 0.9)
plt.grid(True, alpha=0.25)
plt.legend(loc="upper right")
plt.tight_layout()
plt.savefig(OUTPUT_DIR / "quantization_waveform.png", dpi=200)
plt.close()

# Figure 2: 8-bit quantization error over 1 s and a 20 ms zoom.
noise_8bit = quantized_by_bits[8] - signal
half_step_8bit = step_by_bits[8] / 2.0
fig, axes = plt.subplots(2, 1, figsize=(10, 7.2), sharey=True)
axes[0].plot(time, noise_8bit, color="#2ca02c", linewidth=0.6)
axes[0].axhline(half_step_8bit, color="#d62728", linestyle="--", linewidth=1.2, label="+Delta/2")
axes[0].axhline(-half_step_8bit, color="#d62728", linestyle="--", linewidth=1.2, label="-Delta/2")
axes[0].set_title("8-bit Quantization Error Over 1 s")
axes[0].set_ylabel("Error")
axes[0].set_xlim(0.0, 1.0)
axes[0].grid(True, alpha=0.25)
axes[0].legend(loc="upper right", ncol=2, fontsize=9)
axes[1].plot(t_zoom * 1e3, noise_8bit[:first_20ms], color="#2ca02c", linewidth=1.2)
axes[1].axhline(half_step_8bit, color="#d62728", linestyle="--", linewidth=1.2)
axes[1].axhline(-half_step_8bit, color="#d62728", linestyle="--", linewidth=1.2)
axes[1].set_title("Zoom: First 20 ms")
axes[1].set_xlabel("Time (ms)")
axes[1].set_ylabel("Error")
axes[1].set_xlim(0.0, 20.0)
axes[1].grid(True, alpha=0.25)
fig.suptitle("8-bit Quantization Error and the Theoretical Bounds +/-Delta/2", fontsize=13)
fig.tight_layout(rect=(0, 0, 1, 0.96))
plt.savefig(OUTPUT_DIR / "quantization_error.png", dpi=200)
plt.close()

# Figure 3: theoretical and measured SQNR versus bit depth.
q_values = np.array([row["Q"] for row in rows])
measured_values = np.array([row["measured_sqnr_db"] for row in rows])
theory_values = np.array([row["theory_sqnr_db"] for row in rows])
adjusted_values = np.array([row["theory_amplitude_adjusted_db"] for row in rows])
plt.figure(figsize=(8.6, 5.2))
plt.plot(q_values, theory_values, "o--", color="#1f77b4", linewidth=1.5, label="Theory: 6.02Q + 1.76 dB")
plt.plot(
    q_values,
    adjusted_values,
    "s:",
    color="#2ca02c",
    linewidth=1.4,
    label="Theory adjusted for A = 0.8",
)
plt.plot(q_values, measured_values, "D-", color="#d62728", linewidth=1.8, label="Measured")
for bits, measured in zip(q_values, measured_values):
    plt.annotate(f"{measured:.2f} dB", (bits, measured), textcoords="offset points", xytext=(0, 9), ha="center", fontsize=8)
plt.title("SQNR versus Uniform Quantizer Bit Depth")
plt.xlabel("Quantizer bits Q")
plt.ylabel("SQNR (dB)")
plt.xticks(q_values)
plt.grid(True, alpha=0.25)
plt.legend(loc="upper left")
plt.tight_layout()
plt.savefig(OUTPUT_DIR / "sqnr_comparison.png", dpi=200)
plt.close()

# CSV output.
csv_path = OUTPUT_DIR / "sqnr_results.csv"
headers = [
    "Q",
    "theory_sqnr_db",
    "measured_sqnr_db",
    "difference_db",
    "theory_amplitude_adjusted_db",
    "difference_vs_adjusted_db",
    "signal_power",
    "noise_power",
    "step",
]
with csv_path.open("w", encoding="utf-8", newline="") as handle:
    handle.write(",".join(headers) + "\n")
    for row in rows:
        values = [
            str(row["Q"]),
            f"{row['theory_sqnr_db']:.4f}",
            f"{row['measured_sqnr_db']:.4f}",
            f"{row['difference_db']:.4f}",
            f"{row['theory_amplitude_adjusted_db']:.4f}",
            f"{row['difference_vs_adjusted_db']:.4f}",
            f"{row['signal_power']:.8f}",
            f"{row['noise_power']:.12e}",
            f"{row['step']:.10f}",
        ]
        handle.write(",".join(values) + "\n")

conclusion = (
    "实验表明，8至16位均匀量化的实测SQNR随位数增加近似按每比特6dB提升，"
    "并与量化噪声方差Δ²/12的预测吻合。输入幅度为0.8而非满幅1.0，"
    "因此实测值比满幅正弦理论式低约1.9dB；计入幅度修正后，两者差异较小。"
)

md_lines = [
    "# 均匀量化与量化噪声的信噪比验证",
    "",
    "## SQNR 对比表",
    "",
    "| Q | 理论 SQNR (dB) | 实测 SQNR (dB) | 差值 (dB) |",
    "|---:|---:|---:|---:|",
]
for row in rows:
    md_lines.append(
        f"| {row['Q']} | {row['theory_sqnr_db']:.2f} | "
        f"{row['measured_sqnr_db']:.2f} | {row['difference_db']:+.2f} |"
    )
md_lines.extend(
    [
        "",
        "注：理论值采用满幅正弦公式 `SQNR ≈ 6.02Q + 1.76 dB`。本次输入幅度为 0.8，"
        "因此理论值应再叠加 `20log10(0.8) ≈ -1.94 dB`；修正后的对比见 CSV。",
        "",
        "## 中文结论",
        "",
        conclusion,
        "",
        "## 输出文件",
        "",
        "- `quantization_waveform.png`：前 20 ms 原始波形与 8 位阶梯波形",
        "- `quantization_error.png`：8 位量化误差及 ±Δ/2 理论界限",
        "- `sqnr_comparison.png`：理论、幅度修正理论与实测 SQNR 曲线",
        "- `sqnr_results.csv`：完整数值结果",
        "- `conclusion.txt`：中文结论",
    ]
)
(OUTPUT_DIR / "sqnr_results.md").write_text("\n".join(md_lines) + "\n", encoding="utf-8")
(OUTPUT_DIR / "conclusion.txt").write_text(conclusion + "\n", encoding="utf-8")

print("Experiment completed.")
print(f"Output directory: {OUTPUT_DIR}")
for row in rows:
    print(
        f"Q={row['Q']:2d} | theory={row['theory_sqnr_db']:7.3f} dB | "
        f"measured={row['measured_sqnr_db']:7.3f} dB | diff={row['difference_db']:+.3f} dB | "
        f"adjusted diff={row['difference_vs_adjusted_db']:+.3f} dB"
    )
print(f"Conclusion: {conclusion}")
