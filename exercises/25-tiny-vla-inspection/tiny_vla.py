"""TinyVLA — a structural stand-in for OpenVLA / RT-2 / pi_0.

Same three-block architecture as a real Vision-Language-Action model:

    image (H, W, 3) ──► vision encoder ──► v ∈ R^d_v
                                                    \\
    instruction str ─► text encoder   ──► t ∈ R^d_t  ─► fuse ─► action head ─► action (7,)
                                                    /

Real VLAs use a giant pretrained ViT for the vision side, a giant
pretrained language model for the text side, and a thin MLP head for
the action side. Ours uses a tiny CNN, a tiny embedding+linear, and
a tiny MLP. Same shape, ~10 000 parameters total.

The model is **randomly initialised and never trained.** The numbers
it produces are not predictions you should believe — they only
illustrate the input/output shape of a VLA. Real VLAs are trained on
~1 M robot trajectories (Open X-Embodiment for OpenVLA).
"""

from __future__ import annotations

import numpy as np
import torch
from torch import nn

from vocab import MAX_LEN, VOCAB_SIZE
from scene import IMAGE_HW


# Action channel order — this matches OpenVLA's 7-DoF action space.
ACTION_NAMES: tuple[str, ...] = (
    "dx",       # end-effector translation in metres, base frame
    "dy",
    "dz",
    "droll",    # end-effector rotation delta in radians (Euler)
    "dpitch",
    "dyaw",
    "gripper",  # 0.0 = closed, 1.0 = open (normalised)
)
ACTION_DIM: int = len(ACTION_NAMES)


class TinyVisionEncoder(nn.Module):
    """Three conv layers + global pool → 32-dim image embedding."""

    def __init__(self, embed_dim: int = 32) -> None:
        super().__init__()
        self.net = nn.Sequential(
            nn.Conv2d(3, 8, kernel_size=5, stride=2, padding=2),
            nn.ReLU(),
            nn.Conv2d(8, 16, kernel_size=3, stride=2, padding=1),
            nn.ReLU(),
            nn.Conv2d(16, embed_dim, kernel_size=3, stride=2, padding=1),
            nn.ReLU(),
            nn.AdaptiveAvgPool2d(1),
            nn.Flatten(),
        )

    def forward(self, img: torch.Tensor) -> torch.Tensor:
        return self.net(img)


class TinyTextEncoder(nn.Module):
    """Token embedding + mean-pool → 16-dim instruction embedding."""

    def __init__(self, embed_dim: int = 16) -> None:
        super().__init__()
        self.emb = nn.Embedding(VOCAB_SIZE, embed_dim)
        self.proj = nn.Linear(embed_dim, embed_dim)

    def forward(self, token_ids: torch.Tensor) -> torch.Tensor:
        # mean-pool across the sequence dimension
        return self.proj(self.emb(token_ids).mean(dim=1))


class TinyActionHead(nn.Module):
    """Two-layer MLP from fused embedding to 7-DoF action."""

    def __init__(self, in_dim: int, hidden: int = 64, out_dim: int = ACTION_DIM) -> None:
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(in_dim, hidden),
            nn.ReLU(),
            nn.Linear(hidden, out_dim),
        )

    def forward(self, fused: torch.Tensor) -> torch.Tensor:
        return self.net(fused)


class TinyVLA(nn.Module):
    """Vision + Text → 7-DoF action. ~10k parameters."""

    def __init__(self) -> None:
        super().__init__()
        self.vision = TinyVisionEncoder(embed_dim=32)
        self.text = TinyTextEncoder(embed_dim=16)
        self.head = TinyActionHead(in_dim=32 + 16)

    def forward(
        self, image_chw: torch.Tensor, token_ids: torch.Tensor
    ) -> torch.Tensor:
        v = self.vision(image_chw)
        t = self.text(token_ids)
        fused = torch.cat([v, t], dim=-1)
        raw = self.head(fused)
        # squash translation to ±5 cm, rotation to ±0.3 rad, gripper to [0, 1]
        action = torch.empty_like(raw)
        action[..., 0:3] = torch.tanh(raw[..., 0:3]) * 0.05      # dx, dy, dz
        action[..., 3:6] = torch.tanh(raw[..., 3:6]) * 0.3       # droll, dpitch, dyaw
        action[..., 6] = torch.sigmoid(raw[..., 6])               # gripper
        return action


def build_model(seed: int = 0) -> TinyVLA:
    """Build a fresh TinyVLA with deterministic weights."""
    torch.manual_seed(seed)
    return TinyVLA().eval()


def preprocess_image(rgb: np.ndarray) -> torch.Tensor:
    """(H, W, 3) uint8 → (1, 3, H, W) float in [0, 1]."""
    assert rgb.shape == (IMAGE_HW, IMAGE_HW, 3) and rgb.dtype == np.uint8
    chw = rgb.astype(np.float32).transpose(2, 0, 1) / 255.0
    return torch.from_numpy(chw).unsqueeze(0)


def preprocess_text(token_ids: list[int]) -> torch.Tensor:
    assert len(token_ids) == MAX_LEN
    return torch.tensor(token_ids, dtype=torch.long).unsqueeze(0)


def count_parameters(model: nn.Module) -> int:
    return sum(p.numel() for p in model.parameters())
