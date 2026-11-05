"""Athens NO2 + water vapor: animated plot with a synced two-voice sonification.

Usage:  python sonify_athens.py [athens_no2_waterVapor_clean.csv]
Needs:  pip install numpy pandas matplotlib      (ffmpeg must be on PATH)
Output: athens_sonification.mp4 (+ athens_sonification.wav)

Mapping (one calendar day = SEC_PER_DAY seconds, so gaps in the data are real silence):
  water vapor, 14-day mean -> pitch of a soft sustained voice (A minor pentatonic, left)
  NO2, daily mean          -> pitch + loudness of a plucked voice (higher register, right)
"""
import sys, subprocess, wave
import numpy as np, pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

CSV = sys.argv[1] if len(sys.argv) > 1 else "athens_no2_waterVapor_clean.csv"
NO2, WV = "no2_tropospheric_col_molm2", "water_vapor_tropospheric_col_molm2"
SEC_PER_DAY, SR, FPS = 0.16, 44100, 12
W, H, DPI = 1280, 720, 100
BLUE, ORANGE = "#2a78d6", "#eb6834"
INK, MUTED, GRID, BG = "#0b0b0b", "#52514e", "#e6e5e1", "#fcfcfb"

# ---------- data ----------
df = pd.read_csv(CSV, parse_dates=["timestamp_utc", "date"])
daily = df.groupby("date")[[NO2, WV]].mean()
roll = daily.rolling(14, center=True, min_periods=5).mean()
days = pd.date_range(daily.index.min(), daily.index.max(), freq="D")
daily, roll = daily.reindex(days), roll.reindex(days)          # NaN on days with no data
has = daily[NO2].notna().to_numpy()
n = len(days)

# ---------- audio (RAW: continuous pitch, no scale, real measurement times) ----------
def log_map(x, lo, hi): return lo * (hi / lo) ** np.clip(x, 0, 1)   # equal ratio per step, like real pitch perception
total = int(n * SEC_PER_DAY * SR) + SR
pos = np.arange(total) / SR / SEC_PER_DAY                            # fractional day index at every sample
valid = ~np.isnan(wv_n_raw := ((roll[WV] - roll[WV].min()) / (roll[WV].max() - roll[WV].min())).to_numpy())
idx = np.where(valid)[0]
gate = valid[np.clip(np.round(pos).astype(int), 0, n - 1)].astype(float)
k = int(0.05 * SR); gate = np.convolve(gate, np.ones(k) / k, mode="same")      # 50 ms smoothing, no clicks

# voice 1: gliding sine, frequency follows the 14-day water-vapor mean continuously
f = np.interp(pos, idx, log_map(wv_n_raw[idx], 110, 440))
tone = np.sin(2 * np.pi * np.cumsum(f) / SR) * gate * 0.25

# voice 2: one short sine blip per real measurement, placed at its actual time of day
no_all = df[NO2].clip(lower=0); no_all = np.sqrt(no_all / no_all.max()).to_numpy()
day_i = ((df["timestamp_utc"].dt.normalize() - days[0]).dt.days).to_numpy()
frac = (df["timestamp_utc"].dt.hour + df["timestamp_utc"].dt.minute / 60).to_numpy() / 24
blip_n = int(0.03 * SR); tb = np.arange(blip_n) / SR
ramp = np.minimum(1, np.minimum(np.arange(blip_n), blip_n - np.arange(blip_n)) / (0.003 * SR))
blips = np.zeros(total)
for d_, fr_, x in zip(day_i, frac, no_all):
    s0 = int((d_ + fr_) * SEC_PER_DAY * SR)
    if s0 + blip_n < total:
        blips[s0:s0 + blip_n] += np.sin(2 * np.pi * log_map(x, 220, 1760) * tb) * ramp * (0.03 + 0.4 * x)

# hiss: louder when the water-vapor retrieval is less certain (daily mean uncertainty)
unc = daily.index.to_series().map(df.groupby("date")["water_vapor_uncertainty_molm2"].mean()).to_numpy()
un = (unc - np.nanmin(unc)) / (np.nanmax(unc) - np.nanmin(unc))
hiss = np.random.default_rng(0).standard_normal(total) * np.interp(pos, idx, un[idx]) * gate * 0.18

mono = tone + blips + hiss
mono = mono / np.abs(mono).max() * 0.9
pcm = (np.stack([mono, mono], 1) * 32767).astype("<i2")
with wave.open("athens_sonification_raw.wav", "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())
dur = n * SEC_PER_DAY
print("audio rms %.3f, peak %.3f" % (np.sqrt((mono**2).mean()), np.abs(mono).max()))

# ---------- video ----------
plt.rcParams.update({"figure.facecolor": BG, "axes.facecolor": BG, "axes.edgecolor": GRID,
    "axes.labelcolor": MUTED, "xtick.color": MUTED, "ytick.color": MUTED, "text.color": INK,
    "axes.spines.top": False, "axes.spines.right": False, "axes.grid": True,
    "grid.color": GRID, "grid.linewidth": 0.8, "font.size": 11})
fig, axs = plt.subplots(2, 1, figsize=(W/DPI, H/DPI), dpi=DPI, sharex=True)
fig.subplots_adjust(left=0.09, right=0.98, top=0.93, bottom=0.08, hspace=0.18)
specs = [(axs[0], NO2, BLUE, "Tropospheric NO₂ (mol/m²)", "blip per measurement: pitch + loudness"),
         (axs[1], WV, ORANGE, "Water vapor (mol/m²)", "gliding tone: pitch  |  hiss: uncertainty")]
dots = df.copy()
revealed = []
for ax, col, c, lab, how in specs:
    ax.scatter(dots["timestamp_utc"], dots[col], s=3, color=c, alpha=0.08, linewidths=0)   # faint full context
    ax.set_xlim(days[0], days[-1]); ax.set_ylabel(lab)
    ax.set_title(f"{lab}  —  {how}", loc="left", fontsize=11, color=INK)
    sc = ax.scatter([], [], s=4, color=c, alpha=0.45, linewidths=0)
    (ln,) = ax.plot([], [], color=c, lw=2.2)
    (ph,) = ax.plot([], [], marker="o", ms=8, color=c, mec=BG, mew=2, ls="")
    vl = ax.axvline(days[0], color=MUTED, lw=1, alpha=0.7)
    revealed.append((ax, col, sc, ln, ph, vl))
axs[0].set_ylim(-0.0001, 0.0012)
fig.canvas.draw()
bgs = [fig.canvas.copy_from_bbox(a.bbox) for a, *_ in revealed]

ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgba",
    "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-i", "athens_sonification_raw.wav",
    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "23", "-preset", "veryfast",
    "-c:a", "aac", "-b:a", "160k", "-shortest", "athens_sonification_raw.mp4"], stdin=subprocess.PIPE)
ts = df["timestamp_utc"].to_numpy()
for k in range(int(dur * FPS)):
    d = min(int(k / FPS / SEC_PER_DAY), n - 1)
    cut = np.datetime64(days[d] + pd.Timedelta(days=1))
    mask = ts < cut
    for (ax, col, sc, ln, ph, vl), bgr in zip(revealed, bgs):
        fig.canvas.restore_region(bgr)
        sub = dots[mask]
        sc.set_offsets(np.c_[matplotlib.dates.date2num(sub["timestamp_utc"]), sub[col].to_numpy()])
        r = roll[col].iloc[: d + 1].dropna()
        ln.set_data(r.index, r.to_numpy())
        if len(r): ph.set_data([r.index[-1]], [r.iloc[-1]])
        vl.set_xdata([days[d], days[d]])
        for a in (sc, ln, vl, ph): ax.draw_artist(a)
        fig.canvas.blit(ax.bbox)
    ff.stdin.write(fig.canvas.buffer_rgba().tobytes())
ff.stdin.close(); ff.wait()
print("done:", dur, "seconds,", n, "days,", int(has.sum()), "with data")
