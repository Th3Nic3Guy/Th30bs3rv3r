"""FREE WILL simulation engine.

Tensor-native agent-based simulation implementing the FREE WILL formal model.
See docs/FREE_WILL_PRD.md for the system design and docs/adr/0001-gcp-tech-stack.md
for the GCP infrastructure this package targets.

Sub-packages:
    engine       — state tensors and the per-tick loop (PRD Section 4.1, 4.2)
    mechanisms   — one module per draft section, per PRD Section 4.3
    config       — run-time parameter schema and loading (PRD Section 5)
    storage      — Cloud Storage / Cloud SQL / Redis clients (PRD Section 6)
    validation   — slow iterative reference oracle (PRD Section 4.4)
    metrics      — run-summary metric computation (PRD Section 4.7 / 6.4)
"""

__version__ = "0.1.0"
