"""Train a tiny MLP that maps (state -> next action).

This is plain supervised learning on the demo dataset. No reward, no
exploration. The model learns to imitate the expert's joint velocities.
"""

from __future__ import annotations

from pathlib import Path

import joblib
import numpy as np
from sklearn.neural_network import MLPRegressor


def train(states: np.ndarray, actions: np.ndarray) -> MLPRegressor:
    """Fit a small two-hidden-layer MLP. ~7k parameters."""
    model = MLPRegressor(
        hidden_layer_sizes=(64, 64),
        activation="tanh",
        solver="adam",
        learning_rate_init=1e-3,
        max_iter=400,
        random_state=0,
        early_stopping=True,
        validation_fraction=0.1,
        n_iter_no_change=10,
        verbose=False,
    )
    model.fit(states, actions)
    return model


if __name__ == "__main__":
    here = Path(__file__).parent
    data = np.load(here / "output" / "demo.npz")
    model = train(data["states"], data["actions"])
    joblib.dump(model, here / "output" / "bc_policy.joblib")
    print(
        f"[train] final training loss: {model.loss_:.6f} "
        f"({model.n_iter_} epochs)"
    )
