
**A year of air-quality data from a NASA/ESA-backed Pandora instrument in Athens, turned into an animated chart with a synced soundtrack.**

> **TL;DR** — I took one year (25 Oct 2025 → 24 Oct 2026) of nitrogen dioxide (NO₂) and water vapor measurements from Pandora instrument #119 at the National Observatory of Athens, and mapped them to sound: water vapor becomes a slowly gliding tone, NO₂ becomes short notes whose loudness follows the pollution level. Two versions: a **musical** one and a **raw** one.



---

## Contents

1. [Why this project](#why-this-project)
2. [The data](#the-data)
3. [What the data looks like](#what-the-data-looks-like)
4. [How the sonification works](#how-the-sonification-works)
5. [Two versions: musical vs raw](#two-versions-musical-vs-raw)
6. [Run it yourself](#run-it-yourself)
7. [Repository contents](#repository-contents)
8. [Limitations and honest caveats](#limitations-and-honest-caveats)
9. [Ideas for next steps](#ideas-for-next-steps)
10. [Acknowledgments and citation](#acknowledgments-and-citation)

---

## Why this project

On 22 October I attended a talk by NASA scientists about the **Pandora Project**, a global network of ground-based instruments that measure air quality and atmospheric composition, with the data distributed openly. I wanted to try the data for myself, and a chart felt too ordinary, so I asked: *what does a year of Athens' atmosphere sound like?*

This is a small **data sonification** project: choosing a mapping from data columns to sound properties (pitch, loudness, timing, stereo position) and rendering it alongside a visualization.

## The data

| | |
|---|---|
| **Network** | Pandora Project / Pandonia Global Network (PGN) |
| **Instrument** | Pandora #119, spectrometer 1 |
| **Location** | National Observatory of Athens, Thiseio, Greece (37.9878° N, 23.7750° E, 130 m) |
| **Data version** | `rnvh3p1-8`, processed with BlickP v1.8.75 |
| **Product level** | Level 2 (retrieved quantities) |
| **Status** | NO₂ and water vapor data flagged as *official* in the file header |
| **Dataset DOI** | [10.48596/pgn.rnvh3p1-8.Athens-NOA.P119s1](https://doi.org/10.48596/pgn.rnvh3p1-8.Athens-NOA.P119s1) |
| **Local PI** | Stelios Kazadzis |
| **Network PI** | Alexander Cede |

Pandora is a **ground-based** spectrometer: it looks at the Sun (direct-sun mode) and measures how much light is absorbed by gases along the path, then retrieves column amounts. So each data point is a *measurement from the ground*, not a satellite overpass.

### Variables used

From the raw Level 2 file I used the **tropospheric vertical column** of each gas, plus its independent uncertainty:

| CSV column | Raw file column | Meaning | Unit |
|---|---|---|---|
| `timestamp_utc` | 1 | Time of measurement (UTC) | ISO 8601 |
| `no2_tropospheric_col_molm2` | 62 | NO₂ tropospheric column | mol/m² |
| `no2_uncertainty_molm2` | 63 | Independent uncertainty of the NO₂ column | mol/m² |
| `water_vapor_tropospheric_col_molm2` | 49 | Water vapor tropospheric column | mol/m² |
| `water_vapor_uncertainty_molm2` | 50 | Independent uncertainty of the water vapor column | mol/m² |
| `date`, `hour_utc` | derived | Convenience columns | |

**Making the units intuitive**
- NO₂: 1 mol/m² ≈ 6.022 × 10¹⁹ molecules/cm², so a typical value here of 1.6 × 10⁻⁴ mol/m² ≈ 9.6 × 10¹⁵ molecules/cm².
- Water vapor: 1 mol/m² of water ≈ 0.018 mm of precipitable water, so the average of ~850 mol/m² here is roughly 15 mm.

### The cleaned file

`athens_no2_waterVapor_clean.csv` holds **2,586 measurements** covering **257 of 365 days**, with no missing values. It is a subset of the raw file, which has ~6.8 MB of text and begins in June 2016.

## What the data looks like

I explored the data visually *before* deciding on a sound mapping, because the plots show which features are worth hearing.

- **Water vapor has a clear seasonal arc.** The monthly mean falls from about 1,090 mol/m² in November 2025 to a low near 370 in March 2026, then climbs to a peak near 1,230 in August 2026.
- **NO₂ is noisy and mostly flat** with occasional spikes. It averages about 1.6 × 10⁻⁴ mol/m², with a maximum near 1.1 × 10⁻³. The highest daily means were on 18–19 December 2025.
- **The two are barely correlated** (Pearson r ≈ −0.11).
- **NO₂ has a daily pattern:** higher in the early morning (about 2 × 10⁻⁴ near 05:00 UTC) and lower in the afternoon (about 1 × 10⁻⁴ near 14:00 UTC).
- **There are gaps.** Most dates are consecutive, but there are two gaps of roughly three weeks each.
- **5 NO₂ values are slightly negative.** That is normal retrieval noise near zero, and they are clamped to zero before being turned into sound.

## How the sonification works

Every sonification is a **mapping** from data to sound. Here, one calendar day lasts **0.16 seconds**, so the year plays in about **58 seconds**. Days without data are real silence, so the gaps are audible.

| Data | Sound property |
|---|---|
| Water vapor (14-day centered rolling mean) | Pitch of a sustained tone |
| NO₂ | Pitch and loudness of short notes |
| Water vapor measurement uncertainty *(raw version only)* | Amount of background hiss |
| Time | Position in the soundtrack; also the moving playhead in the video |

Values are min-max normalized to 0–1 before mapping. For NO₂ loudness, a **square-root** scale is used so the quiet baseline stays audible while spikes still stand out.

The video shows the NO₂ panel above the water vapor panel, with each line drawing in as time passes, a vertical playhead, and a faint ghost of the full dataset behind it.

## Two versions: musical vs raw

I made two versions to show how much of the "music" comes from design choices rather than from the data itself.

### 1. Musical version (`athens_sonification.mp4`)

- **Notes snapped to the A minor pentatonic scale**, so any combination of notes sounds pleasant. Water vapor picks from 15 notes (A2 upward, 3 octaves) and NO₂ from 10 notes (A4 upward, 2 octaves).
- **One note per day**, using the daily mean.
- **Water vapor** is a soft tone with a faint second harmonic, slightly longer than a step so neighbouring notes blend into a pad.
- **NO₂** is a short pluck with an exponential decay.
- **Stereo split:** water vapor sits mostly left, NO₂ mostly right.

### 2. Raw version (`athens_sonification_raw.mp4`)

- **Continuous pitch, no scale.** Water vapor glides smoothly between 110 and 440 Hz on a logarithmic scale (equal ratios per step, matching how we hear pitch).
- **Real timing.** One 30 ms sine blip per *actual measurement*, placed at its real time of day, with pitch 220–1760 Hz and loudness from the NO₂ value.
- **Uncertainty hiss.** Background noise gets louder on days when the water vapor retrieval is less certain.
- **Plain sine waves and mono sound.** No harmonics, no decay shaping and no stereo split.

### The trade-off

Snapping to a scale throws away detail: with only 15 possible water vapor notes, small changes are flattened into the same note. The musical version is easier to listen to but less faithful to the data. The raw version preserves more of the real shape and timing, but is harder to listen to. Neither is "correct"; it depends on whether the goal is communication or fidelity.

## Run it yourself

**Requirements:** Python 3, [ffmpeg](https://ffmpeg.org/) on your PATH, and:

```bash
pip install numpy pandas matplotlib
```

**Render the musical version:**

```bash
python sonify_athens.py athens_no2_waterVapor_clean.csv
```

**Render the raw version:**

```bash
python sonify_athens_raw.py athens_no2_waterVapor_clean.csv
```

Each run writes a `.wav` and an `.mp4` into the current folder and takes roughly a minute.

**Tweaking the sound.** The settings are at the top of each script:
- `SEC_PER_DAY` sets the playback speed (default 0.16 s per day).
- `penta`, `wv_notes` and `no_notes` set the scale and registers in the musical version.
- The frequency ranges passed to `log_map(...)` set the pitch ranges in the raw version.

## Repository contents

```
.
├── README.md
├── athens_no2_waterVapor_clean.csv              # cleaned data used for the project
├── Pandora119s1_Athens-NOA_L2_rnvh3p1-8_*.txt   # original Level 2 file from the network
├── sonify_athens.py                             # musical version: audio + video
├── sonify_athens_raw.py                         # raw version: audio + video
├── athens_sonification.mp4 / .wav               # musical version outputs
├── athens_sonification_raw.mp4 / .wav           # raw version outputs
└── athens.ipynb                                 # scratch notebook
```

## Limitations and honest caveats

- **This is a sonification, not an analysis.** It is meant to make patterns *audible* and to be an interesting way to experience the data, not to prove anything about Athens' air.
- **One instrument, one year, one location.** Nothing here generalizes to the whole city.
- **Uneven sampling.** The number of measurements per month varies a lot (59 in March 2026, 570 in September 2026), so monthly averages are not equally reliable, and apparent shifts in level may partly reflect how often the instrument measured.
- **Ground-based direct-sun measurements** only happen when the Sun is up and unobstructed, so there is no nighttime data and cloudy periods are underrepresented.
- **Pitch is not a perfectly honest channel.** Quantizing to a musical scale, smoothing with a 14-day mean and the square-root loudness curve are all design choices that change what you hear.
- **Known cosmetic issue:** a faint dotted line shows along the top edge of the NO₂ panel in the video.

## Acknowledgments and citation

- Thank you to the NASA scientists who gave the 22 October talk on the Pandora Project: Thomas Hanisco and Apoorva Pandey.
- Built with Python, NumPy, pandas, Matplotlib and ffmpeg, with help from Claude.

