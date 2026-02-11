#!/usr/bin/env python3
"""Gopher server for a Mellea-inspired site.

This server exposes a small documentation tree over the Gopher protocol,
with pages inspired by the Mellea tutorial and rewrite documentation.
"""

from __future__ import annotations

import argparse
import socketserver
from dataclasses import dataclass

CRLF = "\r\n"


@dataclass(frozen=True)
class MenuItem:
    item_type: str
    display: str
    selector: str


def text_page(*lines: str) -> str:
    """Build a Gopher text response payload."""
    return CRLF.join(lines) + CRLF


def menu_page(*items: MenuItem, host_placeholder: str = "{host}", port_placeholder: str = "{port}") -> str:
    """Build a Gopher menu response payload."""
    rendered = []
    for item in items:
        rendered.append(
            f"{item.item_type}{item.display}\t{item.selector}\t{host_placeholder}\t{port_placeholder}"
        )
    return CRLF.join(rendered) + CRLF


PAGES: dict[str, str] = {
    "": menu_page(
        MenuItem("i", "Welcome to the Mellea Gopher Capsule", "fake"),
        MenuItem("i", "A compact learning path for model-centered development.", "fake"),
        MenuItem("1", "Start with the tutorial", "/tutorial"),
        MenuItem("1", "Rewrite guide: overview", "/rewrite"),
        MenuItem("1", "Rewrite guide: strategy", "/rewrite/strategy"),
        MenuItem("1", "Rewrite guide: iterative workflow", "/rewrite/iteration"),
        MenuItem("1", "Rewrite guide: evaluation", "/rewrite/evaluation"),
        MenuItem("0", "About this capsule", "/about"),
    ),
    "/about": text_page(
        "Mellea Gopher Capsule",
        "",
        "This capsule is inspired by Mellea tutorial and rewrite docs.",
        "It focuses on practical habits for building with language models:",
        "- design with explicit intent",
        "- keep context and prompts structured",
        "- iterate with measurable quality checks",
        "",
        "Navigate back to selector / for the main menu.",
    ),
    "/tutorial": menu_page(
        MenuItem("i", "Tutorial Path", "fake"),
        MenuItem("0", "1) Define the outcome and user experience", "/tutorial/outcome"),
        MenuItem("0", "2) Model the task as constrained generation", "/tutorial/constrained-generation"),
        MenuItem("0", "3) Add tools and retrieval where certainty matters", "/tutorial/tooling"),
        MenuItem("0", "4) Close the loop with evaluation and revision", "/tutorial/evaluation-loop"),
        MenuItem("1", "Return to home", "/"),
    ),
    "/tutorial/outcome": text_page(
        "Tutorial Step 1: Define the outcome",
        "",
        "Begin with a concrete artifact and a quality bar.",
        "Examples: a migration plan, a product brief, or a code patch.",
        "",
        "State what the user needs in explicit terms:",
        "- audience and constraints",
        "- acceptable format",
        "- what 'done' means",
        "",
        "Good prompts start with sharp intent, not verbose prose.",
    ),
    "/tutorial/constrained-generation": text_page(
        "Tutorial Step 2: Constrained generation",
        "",
        "Treat prompting as interface design.",
        "Give the model a frame that narrows ambiguity:",
        "- role and scope",
        "- required structure and fields",
        "- boundaries (what to avoid)",
        "",
        "Use small, testable output contracts to keep results stable.",
    ),
    "/tutorial/tooling": text_page(
        "Tutorial Step 3: Tools and retrieval",
        "",
        "Use models for synthesis, tools for facts.",
        "When precision matters, provide grounded context from:",
        "- local code and docs",
        "- APIs or databases",
        "- deterministic scripts",
        "",
        "This split reduces hallucinations and improves reproducibility.",
    ),
    "/tutorial/evaluation-loop": text_page(
        "Tutorial Step 4: Evaluation loop",
        "",
        "Every generation should be followed by an explicit check:",
        "- does it satisfy required structure?",
        "- does it pass tests or policy checks?",
        "- does it remain understandable to humans?",
        "",
        "Use failures as signals to improve prompts, data, or tooling.",
    ),
    "/rewrite": menu_page(
        MenuItem("i", "Rewrite Guide", "fake"),
        MenuItem("0", "Overview: what rewriting is for", "/rewrite/overview"),
        MenuItem("0", "Strategy: preserve intent, improve expression", "/rewrite/strategy"),
        MenuItem("0", "Iteration: draft, critique, refine", "/rewrite/iteration"),
        MenuItem("0", "Evaluation: style, meaning, and risk checks", "/rewrite/evaluation"),
        MenuItem("1", "Return to home", "/"),
    ),
    "/rewrite/overview": text_page(
        "Rewrite Overview",
        "",
        "Rewriting is a controlled transformation.",
        "The goal is not novelty; the goal is clarity, fit, and fidelity.",
        "",
        "A useful rewrite process separates:",
        "- intent (must keep)",
        "- tone/format (may adapt)",
        "- constraints (must obey)",
    ),
    "/rewrite/strategy": text_page(
        "Rewrite Strategy",
        "",
        "Before editing text, extract a rewrite brief:",
        "- source purpose",
        "- target audience",
        "- hard constraints",
        "- preferred voice",
        "",
        "Then rewrite with traceability:",
        "- preserve key claims",
        "- compress redundancy",
        "- improve structure and flow",
        "",
        "If constraints conflict, ask for prioritization.",
    ),
    "/rewrite/iteration": text_page(
        "Rewrite Iteration",
        "",
        "Use short cycles:",
        "1. Produce a focused draft.",
        "2. Critique against explicit criteria.",
        "3. Apply only justified revisions.",
        "",
        "Iteration beats one-shot perfection for complex writing tasks.",
    ),
    "/rewrite/evaluation": text_page(
        "Rewrite Evaluation",
        "",
        "Evaluate rewrites on three axes:",
        "- Fidelity: did core meaning stay intact?",
        "- Readability: is it easier to parse and act on?",
        "- Compliance: does it meet style and policy requirements?",
        "",
        "Prefer lightweight rubrics with pass/fail thresholds.",
    ),
}


class GopherRequestHandler(socketserver.BaseRequestHandler):
    """Serve Gopher responses from the in-memory page map."""

    def handle(self) -> None:
        data = self.request.recv(1024)
        selector = data.decode("utf-8", errors="replace").strip()

        if selector in ("", "/"):
            selector = ""

        payload = PAGES.get(selector)
        if payload is None:
            payload = text_page(
                "404 - selector not found",
                "",
                f"Requested selector: {selector or '/'}",
                "Return to '/' for the main menu.",
            )

        host, port = self.server.server_address
        body = payload.format(host=host, port=port)
        if not body.endswith(f".{CRLF}"):
            body = f"{body}.{CRLF}"

        self.request.sendall(body.encode("utf-8"))


class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    allow_reuse_address = True


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Serve a Mellea-inspired Gopher capsule.")
    parser.add_argument("--host", default="0.0.0.0", help="Host interface to bind.")
    parser.add_argument("--port", default=7070, type=int, help="Port to bind.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    with ThreadedTCPServer((args.host, args.port), GopherRequestHandler) as server:
        print(f"Serving Mellea Gopher capsule on {args.host}:{args.port}")
        server.serve_forever()


if __name__ == "__main__":
    main()
