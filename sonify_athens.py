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

# ---------- audio ----------
penta = [0, 3, 5, 7, 10]                                         # A minor pentatonic
def scale_notes(root, octaves): return [root + 12 * o + s for o in range(octaves) for s in penta]
def midi_hz(m): return 440.0 * 2 ** ((m - 69) / 12)
def pick(norm, notes): return notes[int(np.clip(norm, 0, 1) * (len(notes) - 1))]

wv_notes, no_notes = scale_notes(45, 3), scale_notes(69, 2)      # A2.. and A4..
wv_n = ((roll[WV] - roll[WV].min()) / (roll[WV].max() - roll[WV].min())).to_numpy()
no_c = daily[NO2].clip(lower=0)
no_n = (np.sqrt(no_c / no_c.max())).to_numpy()                   # sqrt: spikes stand out, floor stays audible

total = int(n * SEC_PER_DAY * SR) + SR
L, R = np.zeros(total), np.zeros(total)
dl = int(SEC_PER_DAY * SR)
for i in range(n):
    if not has[i]: continue
    s = int(i * SEC_PER_DAY * SR)
    # voice 1: soft tone, slightly longer than a step so neighbours blend
    f = midi_hz(pick(wv_n[i], wv_notes)); m = int(dl * 1.6); t = np.arange(m) / SR
    env = np.minimum(1, np.arange(m) / (0.02 * SR)) * np.minimum(1, (m - np.arange(m)) / (0.06 * SR))
    tone = (np.sin(2*np.pi*f*t) + 0.3*np.sin(2*np.pi*2*f*t)) * env * 0.16
    L[s:s+m] += tone[:total-s] * 0.9;  R[s:s+m] += tone[:total-s] * 0.45
    # voice 2: pluck, loudness and pitch follow NO2
    f2 = midi_hz(pick(no_n[i], no_notes)); m2 = int(0.45 * SR); t2 = np.arange(m2) / SR
    amp = 0.04 + 0.30 * no_n[i]
    pl = np.sin(2*np.pi*f2*t2) * np.exp(-t2 * 9) * amp
    pl[:int(0.003*SR)] *= np.linspace(0, 1, int(0.003*SR))
    L[s:s+m2] += pl[:total-s] * 0.45;  R[s:s+m2] += pl[:total-s] * 0.9
peak = max(np.abs(L).max(), np.abs(R).max()); L, R = L / peak * 0.9, R / peak * 0.9
pcm = (np.stack([L, R], 1) * 32767).astype("<i2")
with wave.open("athens_sonification.wav", "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())
dur = n * SEC_PER_DAY

# ---------- video ----------
plt.rcParams.update({"figure.facecolor": BG, "axes.facecolor": BG, "axes.edgecolor": GRID,
    "axes.labelcolor": MUTED, "xtick.color": MUTED, "ytick.color": MUTED, "text.color": INK,
    "axes.spines.top": False, "axes.spines.right": False, "axes.grid": True,
    "grid.color": GRID, "grid.linewidth": 0.8, "font.size": 11})
fig, axs = plt.subplots(2, 1, figsize=(W/DPI, H/DPI), dpi=DPI, sharex=True)
fig.subplots_adjust(left=0.09, right=0.98, top=0.93, bottom=0.08, hspace=0.18)
specs = [(axs[0], NO2, BLUE, "Tropospheric NO₂ (mol/m²)", "pluck: loudness + pitch"),
         (axs[1], WV, ORANGE, "Water vapor (mol/m²)", "tone: pitch")]
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
    "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-i", "athens_sonification.wav",
    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "23", "-preset", "veryfast",
    "-c:a", "aac", "-b:a", "160k", "-shortest", "athens_sonification.mp4"], stdin=subprocess.PIPE)
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
