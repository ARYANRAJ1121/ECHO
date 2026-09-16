"""Generate PROGRESS_REPORT.pdf — practical implementation only (60% / 40%)."""
from pathlib import Path
from fpdf import FPDF

OUT = Path(__file__).with_name("PROGRESS_REPORT.pdf")


class Report(FPDF):
    def header(self):
        if self.page_no() == 1:
            return
        self.set_font("Helvetica", "I", 9)
        self.set_text_color(100, 100, 100)
        self.cell(0, 8, "ECHO Progress Report  |  Practical Implementation 60%", align="C")
        self.ln(4)
        self.set_draw_color(200, 200, 200)
        self.line(15, self.get_y(), 195, self.get_y())
        self.ln(6)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(120, 120, 120)
        self.cell(0, 10, f"Page {self.page_no()}/{{nb}}", align="C")


pdf = Report()
pdf.alias_nb_pages()
pdf.set_auto_page_break(auto=True, margin=18)
pdf.add_page()

pdf.set_fill_color(20, 40, 60)
pdf.rect(0, 0, 210, 44, "F")
pdf.set_y(11)
pdf.set_text_color(255, 255, 255)
pdf.set_font("Helvetica", "B", 22)
pdf.cell(0, 10, "ECHO", align="C", new_x="LMARGIN", new_y="NEXT")
pdf.set_font("Helvetica", "", 11)
pdf.cell(
    0,
    6,
    "Emergent Collusion in Heterogeneous Oligopolies",
    align="C",
    new_x="LMARGIN",
    new_y="NEXT",
)
pdf.set_font("Helvetica", "B", 12)
pdf.cell(
    0,
    8,
    "Progress Report  -  Practical Coding 60% Done / 40% Left",
    align="C",
    new_x="LMARGIN",
    new_y="NEXT",
)

pdf.set_y(52)
pdf.set_text_color(30, 30, 30)


def h1(t: str) -> None:
    pdf.ln(3)
    pdf.set_font("Helvetica", "B", 13)
    pdf.set_text_color(20, 40, 60)
    pdf.cell(0, 8, t, new_x="LMARGIN", new_y="NEXT")
    pdf.set_draw_color(20, 40, 60)
    pdf.line(15, pdf.get_y(), 85, pdf.get_y())
    pdf.ln(3)
    pdf.set_text_color(30, 30, 30)


def h2(t: str) -> None:
    pdf.ln(2)
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(40, 70, 100)
    pdf.cell(0, 7, t, new_x="LMARGIN", new_y="NEXT")
    pdf.set_text_color(30, 30, 30)


def body(t: str) -> None:
    pdf.set_font("Helvetica", "", 10)
    pdf.multi_cell(0, 5.4, t)
    pdf.ln(1)


def bullet(t: str) -> None:
    pdf.set_font("Helvetica", "", 10)
    pdf.set_x(18)
    pdf.multi_cell(0, 5.3, "-  " + t)


def meta_row(k: str, v: str) -> None:
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(52, 6, k)
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 6, v, new_x="LMARGIN", new_y="NEXT")


def table_header(cols: list[tuple[str, float]]) -> None:
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_fill_color(230, 236, 245)
    for name, w in cols:
        pdf.cell(w, 7, name, border=1, fill=True, align="C")
    pdf.ln()


def table_rows(rows: list[tuple], widths: list[float]) -> None:
    pdf.set_font("Helvetica", "", 9)
    fill = False
    for row in rows:
        pdf.set_fill_color(248, 248, 248) if fill else pdf.set_fill_color(255, 255, 255)
        for i, cell in enumerate(row):
            pdf.cell(widths[i], 6.4, cell, border=1, fill=True)
        pdf.ln()
        fill = not fill


h1("1. Project Information")
meta_row("Student:", "Aryan Raj")
meta_row("Project:", "ECHO - Algorithmic Collusion Simulation")
meta_row("Repository:", "github.com/ARYANRAJ1121/ECHO")
meta_row("Live Demo:", "echo-green-pi.vercel.app")
meta_row("Report Date:", "August 2026")
meta_row("Overall Progress:", "60% practical implementation done")

h1("2. Status (coding only)")
body(
    "This report covers software implementation only. "
    "60% = major practical coding finished and working in the repo. "
    "40% = remaining coding / major features still to build. "
    "No viva, theory, or documentation tasks are counted here."
)

# Progress bar visual
pdf.set_font("Helvetica", "B", 10)
pdf.cell(0, 7, "Progress bar", new_x="LMARGIN", new_y="NEXT")
pdf.set_fill_color(40, 120, 80)
pdf.rect(15, pdf.get_y(), 108, 8, "F")  # 60% of 180
pdf.set_fill_color(220, 220, 220)
pdf.rect(123, pdf.get_y(), 72, 8, "F")  # 40%
pdf.ln(10)
pdf.set_font("Helvetica", "", 9)
pdf.cell(108, 5, "DONE 60%  (core product)", align="C")
pdf.cell(72, 5, "LEFT 40%  (more code)", align="C", new_x="LMARGIN", new_y="NEXT")
pdf.ln(3)

table_header([("Block", 110), ("Share", 30), ("Status", 40)])
table_rows(
    [
        ("Core engine + agents + regulator + UI + loaders", "60%", "Done"),
        ("Live streaming, batch runs, GNN/XAI, richer markets", "40%", "Left to code"),
    ],
    [110, 30, 40],
)

h1("3. Completed 60%  (practical work done)")

h2("3.1 Market engine")
bullet("MNL demand, Nash/monopoly solvers, Lambda index")
bullet("Bertrand loop + scale-invariant price bands")

h2("3.2 Agents (5 architectures)")
table_header([("Agent", 55), ("Module", 70), ("Status", 55)])
table_rows(
    [
        ("Heuristic control", "heuristic_agent.py", "Working ~0.15 L"),
        ("Q-Learning", "rl_agent.py", "Working"),
        ("DQN (NumPy NN)", "dqn_agent.py", "Working ~0.61-0.85"),
        ("LLM Groq Allam 2", "llm_agent.py", "Working"),
        ("RAG + pgvector", "rag_agent.py", "Working"),
    ],
    [55, 70, 55],
)

h2("3.3 Detection pipeline")
bullet("Lambda monitor, NLP clustering, sentiment, demand shock")
bullet("Random Forest strategy classifier + price forecaster")

h2("3.4 Data loaders")
table_header([("Dataset", 40), ("Source", 90), ("Type", 50)])
table_rows(
    [
        ("Gasoline", "BLS via FRED", "Live"),
        ("Crypto", "CoinGecko BTC history", "Live"),
        ("Amazon", "Local listings CSV", "Real file"),
        ("Airlines", "DEL-BOM estimates", "Static code"),
        ("Rideshare", "Uber/Lyft estimates", "Static code"),
    ],
    [40, 90, 50],
)

h2("3.5 Backend, DB, UI, automation")
bullet("FastAPI WebSocket server, PostgreSQL + pgvector, Docker Compose")
bullet("n8n webhooks, start_echo.ps1, Chart.js dashboard + Vercel demo")
bullet("analysis plots / real_data / CLI run_simulation.py")

h2("3.6 Verified")
bullet("Gasoline / crypto / Amazon load with fallback=False")
bullet("End-to-end simulation + API import OK")

h1("4. Remaining 40%  (coding / major work left)")
body("All items below are software to implement - not report writing.")

h2("A. Stronger live-data pipeline (~8%)")
bullet("Richer live feeds beyond current FRED + CoinGecko")
bullet("Stream live prices into dashboard beside the simulation")
bullet("Continuous live Lambda vs simulated Lambda + market alerts")

h2("B. Experiment automation (~7%)")
bullet("JSON/YAML configs, seeded batch runner, result datasets")
bullet("Docker one-command full reproduce + CI tests")
bullet("Extra metrics: welfare loss, consumer surplus, Gini")

h2("C. Advanced detection GNN / XAI (~8%)")
bullet("Graph Neural Network over firm interaction graph")
bullet("Temporal collusion graph, ringleader attention, autoencoders")
bullet("SHAP explainability + auto NL detection reports")

h2("D. Richer market simulation (~10%)")
bullet("Multi-LLM backends in one market; capacity / entry-exit")
bullet("Multi-product bundling; agent communication channels")
bullet("Dynamic demand shocks; regulatory intervention module")
bullet("Multi-market simulation with cross-market spillover")

h2("E. Product polish code (~7%)")
bullet("Wire n8n to Slack/email/Discord nodes")
bullet("Responsive/PWA dashboard + push alerts")
bullet("Deeper automated RAG long-run A/B runner")

h1("5. Run what is already built")
body("cd antitrust_sim")
body(".\\start_echo.ps1 quick")
body("Open http://127.0.0.1:8000  ->  Gasoline/Crypto/Amazon  ->  Heuristic or DQN")

h1("6. Sign-off")
meta_row("Practical major work done:", "60%")
meta_row("Coding / major work left:", "40%")
meta_row("Demoable today:", "Yes")
meta_row("Live/real data now:", "Yes (gasoline, crypto, Amazon)")

pdf.ln(6)
pdf.set_font("Helvetica", "I", 9)
pdf.set_text_color(100, 100, 100)
pdf.multi_cell(
    0,
    5,
    "Covers practical software implementation only (August 2026).",
)

pdf.output(str(OUT))
print(f"Wrote {OUT.resolve()}")
print(f"Size {OUT.stat().st_size} bytes")
