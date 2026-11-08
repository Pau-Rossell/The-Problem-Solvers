"""Tiny experiment: candidate vs baseline on 10 positions, each played with both colors.

Runs main.py once per game (with the visual interface), editing config.json before
each run. Depth and rules are whatever config.json already says and stay fixed.
Score for the candidate: win = 1, draw = 0.5, loss = 0.
Writes results/experiment_<timestamp>.csv and .md. config.json is restored at the end.
"""
import csv
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CONFIG = ROOT / "config.json"
CANDIDATE = "algorithm_alpha-beta.py"
BASELINE = "algorithm_bot.py"
FIRST_SEED = 1000  # Game n uses seed FIRST_SEED + n - 1.

POSITIONS = [
    ("Start position", "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"),
    ("Italian Game", "r1bqkbnr/pppp1ppp/2n5/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R b KQkq - 3 3"),
    ("Ruy Lopez", "r1bqkbnr/pppp1ppp/2n5/1B2p3/4P3/5N2/PPPP1PPP/RNBQK2R b KQkq - 3 3"),
    ("Sicilian Defence", "rnbqkbnr/pp1ppppp/8/2p5/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 2"),
    ("French Defence", "rnbqkbnr/pppp1ppp/4p3/8/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 2"),
    ("Caro-Kann Defence", "rnbqkbnr/pp1ppppp/2p5/8/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 2"),
    ("Scandinavian Defence", "rnbqkbnr/ppp1pppp/8/3p4/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 2"),
    ("Queen's Gambit", "rnbqkbnr/ppp1pppp/8/3p4/2PP4/8/PP2PPPP/RNBQKBNR b KQkq - 0 2"),
    ("King's Indian Defence", "rnbqkb1r/pppppp1p/5np1/8/2PP4/8/PP2PPPP/RNBQKBNR w KQkq - 0 3"),
    ("English Opening", "rnbqkbnr/pppppppp/8/8/2P5/8/PP1PPPPP/RNBQKBNR b KQkq - 0 1"),
]
WHITE_POINTS = {"1-0": 1.0, "0-1": 0.0, "1/2-1/2": 0.5}


def write_reports(rows, config):
    out = ROOT / "results"
    out.mkdir(exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    columns = ["game", "position", "candidate_color", "white", "black", "seed",
               "result", "candidate_score", "reason", "fen"]

    with open(out / f"experiment_{stamp}.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)

    scores = [r["candidate_score"] for r in rows if r["candidate_score"] != ""]
    lines = [
        "# Experiment results", "",
        f"- Date: {datetime.now():%Y-%m-%d %H:%M}",
        f"- Candidate: `{CANDIDATE}`  vs  Baseline: `{BASELINE}`",
        f"- Depth: {config['search_depth']}, rules: {config['rules']['profile']}, "
        f"auto_claim_draws_for_ai: {config['rules']['auto_claim_draws_for_ai']}",
        f"- Seeds: {FIRST_SEED} to {FIRST_SEED + len(rows) - 1}", "",
        f"**Candidate score: {sum(scores)} / {len(scores)}** "
        f"(W {scores.count(1.0)}, D {scores.count(0.5)}, L {scores.count(0.0)})", "",
        "| # | Position | Candidate color | Seed | Result | Candidate score | Reason |",
        "|---|---|---|---|---|---|---|",
    ]
    for r in rows:
        lines.append(f"| {r['game']} | {r['position']} | {r['candidate_color']} | {r['seed']} "
                     f"| {r['result']} | {r['candidate_score']} | {r['reason']} |")
    (out / f"experiment_{stamp}.md").write_text("\n".join(lines) + "\n")
    print(f"Saved results/experiment_{stamp}.csv and .md")


original_text = CONFIG.read_text()
config = json.loads(original_text)
rows = []
try:
    for name, fen in POSITIONS:
        for candidate_color in ("white", "black"):
            game = len(rows) + 1
            seed = FIRST_SEED + game - 1
            white, black = ((CANDIDATE, BASELINE) if candidate_color == "white"
                            else (BASELINE, CANDIDATE))
            config.update(mode="ai_vs_ai", initial_fen=fen, white_algorithm=white,
                          black_algorithm=black, seed=seed, exit_on_finish=True)
            CONFIG.write_text(json.dumps(config, indent=2))

            print(f"Game {game}/{2 * len(POSITIONS)}: {name}, candidate is {candidate_color}, seed {seed}")
            output = subprocess.run([sys.executable, "main.py"], cwd=ROOT,
                                    stdout=subprocess.PIPE, text=True).stdout
            line = next((l for l in output.splitlines() if l.startswith("RESULT")), "RESULT error | no result")
            result, reason = line[len("RESULT "):].split(" | ", 1)

            score = ""
            if result in WHITE_POINTS:
                score = WHITE_POINTS[result] if candidate_color == "white" else 1 - WHITE_POINTS[result]
            print(f"  -> {result} ({reason}), candidate score: {score}")
            rows.append(dict(game=game, position=name, candidate_color=candidate_color,
                             white=white, black=black, seed=seed, result=result,
                             candidate_score=score, reason=reason, fen=fen))
finally:
    CONFIG.write_text(original_text)  # Put config.json back as it was.
    if rows:
        write_reports(rows, config)
