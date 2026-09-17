import re
from collections import defaultdict
from matplotlib.colors import LinearSegmentedColormap
import numpy as np
import pandas as pd

def parse_games(raw: str) -> list[tuple[str, str, dict]]:
    lines = [l.strip() for l in raw.strip().split("\n") if l.strip()]
    games = []
    for i in range(0, len(lines), 2):
        m = re.match(r"white=(\w+), black=(\w+)", lines[i])
        white, black = m.group(1), m.group(2)
        counts = {k: int(v) for k, v in re.findall(r"'(\w+)': (\d+)", lines[i + 1])}
        games.append((white, black, counts))
    return games


def build_decisive_win_matrix(games, agents) -> pd.DataFrame:
    mat = pd.DataFrame(index=agents, columns=agents, dtype=float)
    for white, black, c in games:
        if white not in agents or black not in agents:
            continue
        ww, bw = c.get("white_win", 0), c.get("black_win", 0)
        decisive_total = ww + bw

        mat.loc[white, black] = (ww / decisive_total * 100) if decisive_total > 0 else 50.0
    return mat


def build_overall_decisive_scores(games) -> pd.DataFrame:
    stats = defaultdict(lambda: {"win": 0, "loss": 0, "games": 0})
    for white, black, c in games:
        ww, bw = c.get("white_win", 0), c.get("black_win", 0)

        stats[white]["win"] += ww
        stats[white]["loss"] += bw
        stats[white]["games"] += (ww + bw)

        stats[black]["win"] += bw
        stats[black]["loss"] += ww
        stats[black]["games"] += (ww + bw)

    rows = []
    for agent, s in stats.items():
        if s["games"] == 0:
            continue
        rows.append({
            "agent": agent,
            "games": s["games"],
            "score_pct": s["win"] / s["games"] * 100,
        })
    return pd.DataFrame(rows).sort_values("score_pct", ascending=False).reset_index(drop=True)


def build_same_impl_draw_scores(games, agents) -> pd.DataFrame:
    stats = []
    for agent in agents:
        match = [c for w, b, c in games if w == agent and b == agent]
        if match:
            c = match[0]
            total = c.get("white_win", 0) + c.get("black_win", 0) + c.get("draw", 0)
            draw_pct = (c.get("draw", 0) / total * 100) if total > 0 else 0.0
        else:
            draw_pct = 0.0

        stats.append({"agent": agent, "draw_pct": draw_pct})

    return pd.DataFrame(stats).sort_values("draw_pct", ascending=True).reset_index(drop=True)


def plot_heatmap(ax, matrix: pd.DataFrame, title: str, agent_labels: dict):
    labels = [agent_labels.get(a, a) for a in matrix.index]
    data = matrix.to_numpy(dtype=float)

    highlight_cmap = LinearSegmentedColormap.from_list(
        "custom_highlight", ["#f2f7f4", "#95c2a5", "#245C3A"]
    )

    im = ax.imshow(data, cmap=highlight_cmap, vmin=0, vmax=100)

    ax.set_xticks(range(len(labels)))
    ax.set_xticklabels(labels, rotation=30, ha="right", fontsize=9)
    ax.set_yticks(range(len(labels)))
    ax.set_yticklabels(labels, fontsize=9)
    ax.set_xlabel("Black", fontsize=9, fontweight="bold")
    ax.set_ylabel("White", fontsize=9, fontweight="bold")
    ax.set_title(title, fontsize=11, pad=10)

    for i in range(len(labels)):
        for j in range(len(labels)):
            val = data[i, j]
            if np.isnan(val):
                text = "\u2014"
                color = "gray"
            else:
                text = f"{val:.0f}"
                color = "white" if val > 60 else "black"

            ax.text(j, i, text, ha="center", va="center", fontsize=9, color=color, fontweight="bold")

    return im


def plot_ranking(ax, scores: pd.DataFrame, agent_labels: dict):
    scores = scores.sort_values("score_pct")
    labels = [agent_labels.get(a, a) for a in scores["agent"]]

    bars = ax.barh(labels, scores["score_pct"], color="#245C3A")
    ax.set_xlim(0, 100)
    ax.set_xlabel("Decisive Score % (win / (win + loss), both seats combined)")
    ax.set_title("Overall ranking", fontsize=11)
    ax.grid(axis="x", color="#e1e0d9", linewidth=0.8)
    ax.set_axisbelow(True)

    for bar, val in zip(bars, scores["score_pct"]):
        ax.text(val + 1, bar.get_y() + bar.get_height() / 2, f"{val:.1f}",
                va="center", fontsize=9)


def plot_same_impl_draw_ranking(ax, same_impl_scores: pd.DataFrame, agent_labels: dict):
    scores = same_impl_scores.sort_values("draw_pct", ascending=False)
    labels = [agent_labels.get(a, a) for a in scores["agent"]]

    bars = ax.barh(labels, scores["draw_pct"], color="#245C3A")
    ax.set_xlim(0, 100)
    ax.set_xlabel("Draw Rate % in Same-Implementation Matches (lower = more decisive)", fontsize=9)
    ax.set_title("Same-Implementation Match Decisiveness Ranking", fontsize=11)
    ax.grid(axis="x", color="#e1e0d9", linewidth=0.8)
    ax.set_axisbelow(True)

    for bar, val in zip(bars, scores["draw_pct"]):
        ax.text(val + 1, bar.get_y() + bar.get_height() / 2, f"{val:.1f}%",
                va="center", fontsize=9)
        