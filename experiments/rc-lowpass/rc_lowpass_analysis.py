from __future__ import annotations

import csv
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

R = 1_000.0          # ohm
C = 100e-9           # F
F_MIN = 10.0         # Hz
F_MAX = 100_000.0    # Hz
N_POINTS = 5_001
DB_3 = -3.010299956639812  # 20*log10(1/sqrt(2))

out_dir = Path(__file__).resolve().parent
out_dir.mkdir(parents=True, exist_ok=True)

tau = R * C
f_c = 1.0 / (2.0 * np.pi * tau)
omega_c = 1.0 / tau

f = np.logspace(np.log10(F_MIN), np.log10(F_MAX), N_POINTS)
s = 1j * 2.0 * np.pi * f
H = 1.0 / (1.0 + s * tau)
mag = np.abs(H)
mag_db = 20.0 * np.log10(mag)
phase_deg = np.angle(H, deg=True)

# Locate the -3 dB crossing with interpolation in log-frequency.
mag_db_asc = mag_db[::-1]
f_asc = f[::-1]
measured_fc = float(np.interp(DB_3, mag_db_asc, np.log10(f_asc)))
measured_fc = 10.0 ** measured_fc
measured_mag_db = float(np.interp(np.log10(measured_fc), np.log10(f), mag_db))
measured_phase_deg = float(np.interp(np.log10(measured_fc), np.log10(f), phase_deg))
abs_error_hz = measured_fc - f_c
relative_error_pct = 100.0 * abs_error_hz / f_c

# -20 dB/decade slope check away from the transition band.
f1, f2 = 10.0 * f_c, 100.0 * f_c
mag_db1 = 20.0 * np.log10(abs(1.0 / (1.0 + 1j * f1 / f_c)))
mag_db2 = 20.0 * np.log10(abs(1.0 / (1.0 + 1j * f2 / f_c)))
slope_db_per_dec = (mag_db2 - mag_db1) / (np.log10(f2) - np.log10(f1))

with (out_dir / "frequency_response.csv").open("w", newline="", encoding="utf-8") as fh:
    writer = csv.writer(fh)
    writer.writerow(["frequency_hz", "magnitude_linear", "magnitude_db", "phase_deg"])
    for row in zip(f, mag, mag_db, phase_deg):
        writer.writerow([f"{value:.10g}" for value in row])

def style_bode_axis(ax: plt.Axes) -> None:
    ax.set_xscale("log")
    ax.grid(True, which="both", color="#d9d9d9", linewidth=0.65, alpha=0.75)
    ax.axvline(f_c, color="#555555", linestyle="--", linewidth=1.2)
    ax.tick_params(axis="both", labelsize=10)

fig, (ax_mag, ax_phase) = plt.subplots(
    2, 1, figsize=(9.2, 7.0), sharex=True,
    gridspec_kw={"height_ratios": [1.25, 1.0], "hspace": 0.10},
)
fig.patch.set_facecolor("white")

ax_mag.semilogx(f, mag_db, color="#1f77b4", linewidth=2.1, label="RC low-pass response")
ax_mag.axhline(DB_3, color="#d62728", linestyle=":", linewidth=1.3, label="-3 dB level")
ax_mag.plot([measured_fc], [measured_mag_db], marker="o", markersize=7,
            markerfacecolor="white", markeredgecolor="#d62728", markeredgewidth=1.8,
            linestyle="none", label="Numerical -3 dB point", zorder=5)
ax_mag.annotate(
    f"-3 dB: {measured_fc:,.1f} Hz\n({measured_mag_db:.3f} dB)",
    xy=(measured_fc, measured_mag_db), xytext=(13_000, -1.25),
    fontsize=10.5, color="#b22222",
    arrowprops=dict(arrowstyle="->", color="#b22222", lw=1.1),
)
ax_mag.set_ylim(-48, 3.5)
ax_mag.set_ylabel("Magnitude (dB)", fontsize=12)
ax_mag.set_title("RC First-Order Low-Pass Filter: Bode Response\n"
                 r"$R=1\,\mathrm{k}\Omega,\ C=100\,\mathrm{nF},\ f_c=1/(2\pi RC)$",
                 fontsize=14, pad=12)
ax_mag.legend(loc="lower left", frameon=True, fontsize=9.5)
style_bode_axis(ax_mag)

ax_phase.semilogx(f, phase_deg, color="#2ca02c", linewidth=2.1, label="Phase response")
ax_phase.axhline(-45.0, color="#ff7f0e", linestyle=":", linewidth=1.1)
ax_phase.plot([measured_fc], [measured_phase_deg], marker="o", markersize=6,
              markerfacecolor="white", markeredgecolor="#2ca02c", markeredgewidth=1.6,
              linestyle="none", zorder=5)
ax_phase.annotate(
    f"{measured_phase_deg:.2f}° at $f_c$",
    xy=(measured_fc, measured_phase_deg), xytext=(13_000, -30.0),
    fontsize=10, color="#1f6f1f",
    arrowprops=dict(arrowstyle="->", color="#1f6f1f", lw=1.0),
)
ax_phase.set_ylim(-96, 4)
ax_phase.set_yticks([0, -45, -90])
ax_phase.set_xlabel("Frequency (Hz)", fontsize=12)
ax_phase.set_ylabel("Phase (deg)", fontsize=12)
ax_phase.legend(loc="lower left", frameon=True, fontsize=9.5)
style_bode_axis(ax_phase)

for ax in (ax_mag, ax_phase):
    ax.set_xlim(F_MIN, F_MAX)

fig.tight_layout()
fig.savefig(out_dir / "bode_response.png", dpi=300, bbox_inches="tight")
plt.close(fig)

# Individual panels for reuse in reports.
fig_mag, ax = plt.subplots(figsize=(9.2, 4.5))
fig_mag.patch.set_facecolor("white")
ax.semilogx(f, mag_db, color="#1f77b4", linewidth=2.0)
ax.axhline(DB_3, color="#d62728", linestyle=":", linewidth=1.2)
ax.axvline(measured_fc, color="#555555", linestyle="--", linewidth=1.1)
ax.plot(measured_fc, measured_mag_db, "o", ms=7, mfc="white", mec="#d62728", mew=1.8)
ax.annotate(f"{measured_fc:,.1f} Hz, {measured_mag_db:.3f} dB",
            xy=(measured_fc, measured_mag_db), xytext=(12_000, -1.3),
            fontsize=10, arrowprops=dict(arrowstyle="->", lw=1.0))
ax.set_xlim(F_MIN, F_MAX); ax.set_ylim(-48, 3.5)
ax.set_xlabel("Frequency (Hz)"); ax.set_ylabel("Magnitude (dB)")
ax.set_title("Magnitude Response")
ax.grid(True, which="both", color="#d9d9d9", linewidth=0.65, alpha=0.75)
fig_mag.tight_layout(); fig_mag.savefig(out_dir / "magnitude_response.png", dpi=300, bbox_inches="tight"); plt.close(fig_mag)

fig_phase, ax = plt.subplots(figsize=(9.2, 4.2))
fig_phase.patch.set_facecolor("white")
ax.semilogx(f, phase_deg, color="#2ca02c", linewidth=2.0)
ax.axvline(measured_fc, color="#555555", linestyle="--", linewidth=1.1)
ax.axhline(-45, color="#ff7f0e", linestyle=":", linewidth=1.1)
ax.plot(measured_fc, measured_phase_deg, "o", ms=7, mfc="white", mec="#2ca02c", mew=1.8)
ax.set_xlim(F_MIN, F_MAX); ax.set_ylim(-96, 4); ax.set_yticks([0, -45, -90])
ax.set_xlabel("Frequency (Hz)"); ax.set_ylabel("Phase (deg)")
ax.set_title("Phase Response")
ax.grid(True, which="both", color="#d9d9d9", linewidth=0.65, alpha=0.75)
fig_phase.tight_layout(); fig_phase.savefig(out_dir / "phase_response.png", dpi=300, bbox_inches="tight"); plt.close(fig_phase)

metrics = {
    "inputs": {"R_ohm": R, "C_F": C, "f_min_hz": F_MIN, "f_max_hz": F_MAX, "n_points": N_POINTS},
    "derived": {
        "tau_s": tau,
        "omega_c_rad_s": omega_c,
        "theoretical_fc_hz": f_c,
        "numerical_measured_fc_hz": measured_fc,
        "absolute_error_hz": abs_error_hz,
        "relative_error_percent": relative_error_pct,
        "magnitude_at_fc_db": measured_mag_db,
        "phase_at_fc_deg": measured_phase_deg,
        "rolloff_db_per_decade": float(slope_db_per_dec),
        "magnitude_at_10hz_db": float(mag_db[0]),
        "phase_at_10hz_deg": float(phase_deg[0]),
        "magnitude_at_100khz_db": float(mag_db[-1]),
        "phase_at_100khz_deg": float(phase_deg[-1]),
    },
}
with (out_dir / "metrics.json").open("w", encoding="utf-8") as fh:
    json.dump(metrics, fh, ensure_ascii=False, indent=2)

print(json.dumps(metrics, ensure_ascii=False, indent=2))
print(f"\nOutputs written to: {out_dir}")
