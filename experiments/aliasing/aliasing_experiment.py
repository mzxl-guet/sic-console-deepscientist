# -*- coding: utf-8 -*-
"""
采样定理与混叠现象的量化验证
--------------------------------
信号   : x(t) = sin(2*pi*f0*t + phi),  f0 = 3000 Hz, phi = pi/4
采样率 : fs = 8000 / 4000 / 3000 / 2000 / 1200 Hz
时长   : T = 0.2 s  ->  N = fs*T 点,  频率分辨率 df = fs/N = 5 Hz

理论   : f_alias = |f0 - k*fs|,  k = round(f0/fs),  落在 [0, fs/2]

说明：加入初相 phi = pi/4 是为了让 fs = f0 = 3000 Hz 这一组
      不至于每个采样点都落在正弦的零点上（那样会得到全零序列，
      混叠到直流这件事就观察不到了）。

输出   : outputs/ 下的 3 张 PNG + results.csv + results.md
"""
import csv
import json
import os

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

plt.rcParams["axes.unicode_minus"] = False
plt.rcParams["font.size"] = 9

F0 = 3000.0
PHI = np.pi / 4
DURATION = 0.2
FS_LIST = [8000, 4000, 3000, 2000, 1200]
OUT = os.path.dirname(os.path.abspath(__file__))
os.makedirs(OUT, exist_ok=True)


def theoretical_alias(f0, fs):
    k = int(np.round(f0 / fs))
    return abs(f0 - k * fs), k


def analyze(fs):
    n = int(round(fs * DURATION))
    t = np.arange(n) / fs
    x = np.sin(2 * np.pi * F0 * t + PHI)

    spec = np.fft.rfft(x)
    mag = np.abs(spec) / n * 2.0
    freqs = np.fft.rfftfreq(n, d=1.0 / fs)
    mag_db = 20 * np.log10(np.maximum(mag, 1e-12) / max(mag.max(), 1e-12))

    peak_bin = int(np.argmax(mag))
    peak_f = float(freqs[peak_bin])
    f_alias, k = theoretical_alias(F0, fs)

    return {
        "fs": fs,
        "n": n,
        "t": t,
        "x": x,
        "freqs": freqs,
        "mag": mag,
        "mag_db": mag_db,
        "nyquist": fs / 2.0,
        "satisfies": fs / 2.0 > F0,
        "f_alias": f_alias,
        "k": k,
        "peak_f": peak_f,
        "err": abs(peak_f - f_alias),
        "peak_amp": float(mag[peak_bin]),
        "df": fs / n,
    }


rows = [analyze(fs) for fs in FS_LIST]

# ---------------- 图 1：时域 ----------------
fig, axes = plt.subplots(2, 3, figsize=(13, 6.4))
for ax, r in zip(axes.flat, rows):
    t_fine = np.linspace(0, 0.005, 2000)
    ax.plot(t_fine * 1e3, np.sin(2 * np.pi * F0 * t_fine + PHI),
            color="#0b4a8f", lw=1.2, label="continuous x(t)")
    mask = r["t"] <= 0.005
    ax.stem(r["t"][mask] * 1e3, r["x"][mask], linefmt="#00a9b5",
            markerfmt="o", basefmt=" ", label="samples")
    ax.set_title("fs = %d Hz   (fs/2 = %d Hz)  %s"
                 % (r["fs"], r["nyquist"], "OK" if r["satisfies"] else "ALIASED"),
                 color="#0b4a8f" if r["satisfies"] else "#c0392b")
    ax.set_xlabel("time (ms)")
    ax.set_ylabel("amplitude")
    ax.grid(alpha=0.25)
axes.flat[0].legend(fontsize=8, loc="lower right")
for ax in axes.flat[len(rows):]:
    ax.axis("off")
fig.suptitle("Sampling theorem: time domain (f0 = 3000 Hz)", fontsize=12)
fig.tight_layout()
fig.savefig(os.path.join(OUT, "fig1_time_domain.png"), dpi=160)
plt.close(fig)

# ---------------- 图 2：频谱 ----------------
fig, axes = plt.subplots(2, 3, figsize=(13, 6.4))
for ax, r in zip(axes.flat, rows):
    ax.plot(r["freqs"], r["mag_db"], color="#0b4a8f", lw=1.0)
    ax.axvline(F0, color="#c0392b", ls="--", lw=0.9,
               label="true f0 = %d Hz" % F0)
    ax.axvline(r["f_alias"], color="#1d9e75", ls=":", lw=1.4,
               label="theory alias = %d Hz" % r["f_alias"])
    ax.set_xlim(-r["df"] * 4, r["nyquist"] * 1.05)
    ax.set_ylim(-80, 5)
    ax.plot([r["peak_f"]], [0], "o", ms=5, mfc="none", mec="#c0392b", mew=1.2)
    ax.set_title("fs = %d Hz   peak @ %.0f Hz" % (r["fs"], r["peak_f"]),
                 color="#0b4a8f" if r["satisfies"] else "#c0392b")
    ax.set_xlabel("frequency (Hz)")
    ax.set_ylabel("magnitude (dB)")
    ax.grid(alpha=0.25)
    ax.legend(fontsize=7, loc="lower right")
for ax in axes.flat[len(rows):]:
    ax.axis("off")
fig.suptitle("Spectrum of the sampled signal (rectangular window)", fontsize=12)
fig.tight_layout()
fig.savefig(os.path.join(OUT, "fig2_spectrum.png"), dpi=160)
plt.close(fig)

# ---------------- 图 3：汇总对照 ----------------
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12.5, 4.4))
fs_arr = np.array([r["fs"] for r in rows], dtype=float)
ax1.plot(fs_arr, fs_arr / 2, "o-", color="#0b4a8f", label="Nyquist frequency fs/2")
ax1.axhline(F0, color="#c0392b", ls="--", lw=1.1, label="signal frequency f0 = 3000 Hz")
ax1.fill_between(fs_arr, 0, fs_arr / 2, color="#00a9b5", alpha=0.12)
ax1.set_xlabel("sampling rate fs (Hz)")
ax1.set_ylabel("frequency (Hz)")
ax1.set_title("Nyquist frequency vs signal frequency")
ax1.grid(alpha=0.25)
ax1.legend(fontsize=8)

ax2.plot(fs_arr, [r["f_alias"] for r in rows], "s--", color="#1d9e75",
         label="theoretical alias")
ax2.plot(fs_arr, [r["peak_f"] for r in rows], "o", color="#0b4a8f",
         ms=8, mfc="none", mew=1.6, label="measured peak")
ax2.set_xlabel("sampling rate fs (Hz)")
ax2.set_ylabel("frequency (Hz)")
ax2.set_title("Aliased frequency: theory vs measurement")
ax2.grid(alpha=0.25)
ax2.legend(fontsize=8)
fig.tight_layout()
fig.savefig(os.path.join(OUT, "fig3_alias_summary.png"), dpi=160)
plt.close(fig)

# ---------------- 表格 ----------------
header = ["fs(Hz)", "Nyquist(Hz)", "Satisfies theorem", "Theory alias(Hz)",
          "Measured peak(Hz)", "Abs error(Hz)", "Peak amplitude"]
with open(os.path.join(OUT, "results.csv"), "w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f)
    w.writerow(header)
    for r in rows:
        w.writerow([r["fs"], int(r["nyquist"]), "yes" if r["satisfies"] else "no",
                    r["f_alias"], r["peak_f"], r["err"], round(r["peak_amp"], 4)])

lines = ["| fs (Hz) | Nyquist (Hz) | 满足采样定理 | 理论混叠 (Hz) | 实测峰值 (Hz) | 绝对误差 (Hz) |",
         "|---:|---:|:---:|---:|---:|---:|"]
for r in rows:
    lines.append("| %d | %d | %s | %d | %.0f | %.0f |"
                 % (r["fs"], r["nyquist"], "是" if r["satisfies"] else "否",
                    r["f_alias"], r["peak_f"], r["err"]))
open(os.path.join(OUT, "results.md"), "w", encoding="utf-8").write("\n".join(lines) + "\n")

print("\n".join(lines))
print("\n频率分辨率 df = 5 Hz（每组相同：fs/N = 1/T）")
print("所有误差 = %.1f Hz" % max(r["err"] for r in rows))
json.dump([{k: (v if not isinstance(v, np.ndarray) else None) for k, v in r.items()}
           for r in rows], open(os.path.join(OUT, "results.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
print("产物目录:", OUT)
