"""画像補正の処理本体。

画像はすべて uint8 の RGB 配列 (H, W, 3) で受け渡す。
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional

import cv2
import numpy as np

MODEL_PATH = Path(__file__).resolve().parent.parent / "models" / "realesr-general-x4v3.onnx"

# 出力画像の長辺の上限。巨大な画像でメモリを使い切らないための安全弁
MAX_OUTPUT_EDGE = 10000


@dataclass
class Options:
    mode: str = "classic"  # "classic"（高速補正） or "ai"（AI超解像）
    scale: int = 3  # 拡大倍率 1〜4
    denoise: int = 1  # 0: なし, 1: 弱, 2: 強
    sharpen: float = 1.0  # アンシャープマスクの強さ 0〜2
    contrast: bool = True  # レベル補正（白を白く・黒を黒く）
    ai_strength: float = 0.6  # AI出力と通常拡大の混合比 0〜1（小さい文字の字形崩れを抑える）

    @classmethod
    def from_form(cls, form) -> "Options":
        return cls(
            mode="ai" if form.get("mode") == "ai" else "classic",
            scale=min(max(int(form.get("scale", 3)), 1), 4),
            denoise=min(max(int(form.get("denoise", 1)), 0), 2),
            sharpen=min(max(float(form.get("sharpen", 1.0)), 0.0), 2.0),
            contrast=form.get("contrast", "1") in ("1", "true", "on"),
            ai_strength=min(max(float(form.get("ai_strength", 0.6)), 0.0), 1.0),
        )


ProgressFn = Callable[[float], None]


def effective_scale(width: int, height: int, scale: int) -> int:
    """出力が MAX_OUTPUT_EDGE を超えない範囲で倍率を下げる。"""
    while scale > 1 and max(width, height) * scale > MAX_OUTPUT_EDGE:
        scale -= 1
    return scale


def enhance(img: np.ndarray, opts: Options, progress: Optional[ProgressFn] = None) -> np.ndarray:
    h, w = img.shape[:2]
    scale = effective_scale(w, h, opts.scale)

    if opts.denoise:
        img = _denoise(img, opts.denoise)

    out = cv2.resize(img, (w * scale, h * scale), interpolation=cv2.INTER_LANCZOS4)
    if opts.mode == "ai" and opts.ai_strength > 0:
        ai = _ai_upscale(img, progress)
        if scale != 4:
            ai = cv2.resize(ai, (w * scale, h * scale), interpolation=cv2.INTER_AREA)
        out = cv2.addWeighted(ai, opts.ai_strength, out, 1.0 - opts.ai_strength, 0)
    elif progress:
        progress(1.0)

    if opts.sharpen > 0:
        out = _unsharp(out, opts.sharpen, sigma=0.5 + 0.35 * scale)
    if opts.contrast:
        out = _auto_levels(out)
    return out


def _denoise(img: np.ndarray, level: int) -> np.ndarray:
    # JPEG圧縮由来のブロックノイズ・色ノイズを、拡大前に軽く取り除く
    strength = 3 if level == 1 else 7
    return cv2.fastNlMeansDenoisingColored(img, None, strength, strength, 5, 15)


def _unsharp(img: np.ndarray, amount: float, sigma: float) -> np.ndarray:
    f = img.astype(np.float32)
    blurred = cv2.GaussianBlur(f, (0, 0), sigma)
    return np.clip(f + amount * (f - blurred), 0, 255).astype(np.uint8)


def _auto_levels(img: np.ndarray, low_pct: float = 0.5, high_pct: float = 99.5) -> np.ndarray:
    # 明るさの分布の両端を少し切り詰めて、紙の白と文字の黒をはっきりさせる。
    # 色相が変わらないよう、全チャンネルに同じ変換をかける。
    gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    lo, hi = np.percentile(gray, (low_pct, high_pct))
    if hi - lo < 32:  # ほぼ単色の画像は触らない
        return img
    lut = np.clip((np.arange(256, dtype=np.float32) - lo) * 255.0 / (hi - lo), 0, 255).astype(np.uint8)
    return cv2.LUT(img, lut)


_session = None


def _get_session():
    global _session
    if _session is None:
        import onnxruntime as ort

        if not MODEL_PATH.exists():
            raise FileNotFoundError(f"AIモデルが見つかりません: {MODEL_PATH}")
        _session = ort.InferenceSession(str(MODEL_PATH), providers=["CPUExecutionProvider"])
    return _session


def _ai_upscale(img: np.ndarray, progress: Optional[ProgressFn], tile: int = 256, pad: int = 12) -> np.ndarray:
    """Real-ESRGAN (realesr-general-x4v3) で4倍に拡大する。

    メモリ使用量を抑えるためタイルに分割して推論し、継ぎ目が出ないよう
    周囲 pad ピクセルを余分に推論してから切り捨てる。
    """
    session = _get_session()
    h, w = img.shape[:2]
    x = img.astype(np.float32).transpose(2, 0, 1)[None] / 255.0
    out = np.zeros((3, h * 4, w * 4), dtype=np.float32)

    tiles = [(ty, tx) for ty in range(0, h, tile) for tx in range(0, w, tile)]
    for i, (ty, tx) in enumerate(tiles):
        y0, y1 = max(ty - pad, 0), min(ty + tile + pad, h)
        x0, x1 = max(tx - pad, 0), min(tx + tile + pad, w)
        result = session.run(None, {"input": x[:, :, y0:y1, x0:x1]})[0][0]
        th, tw = min(tile, h - ty), min(tile, w - tx)
        oy, ox = (ty - y0) * 4, (tx - x0) * 4
        out[:, ty * 4:(ty + th) * 4, tx * 4:(tx + tw) * 4] = result[:, oy:oy + th * 4, ox:ox + tw * 4]
        if progress:
            progress((i + 1) / len(tiles))

    return (np.clip(out, 0, 1) * 255).round().astype(np.uint8).transpose(1, 2, 0)
