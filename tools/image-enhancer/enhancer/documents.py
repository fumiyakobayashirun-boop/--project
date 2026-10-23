"""PDF・画像ファイルの読み書き。

PDFはページを丸ごと画像化せず、PDF内の画像オブジェクトだけを高画質化して
差し替える。ページサイズ・レイアウト・文字データ（ベクター文字）はそのまま残る。
"""
from __future__ import annotations

import io
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, List, Optional

import cv2
import numpy as np
import pymupdf
from PIL import Image, ImageOps

from .filters import Options, enhance

# これより小さい画像（アイコン・罫線など）は補正しない
MIN_IMAGE_EDGE = 48
# プレビュー画像の長辺の上限
PREVIEW_MAX_EDGE = 2400
JPEG_QUALITY = 92

IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tif", ".tiff"}

ProgressFn = Callable[[float], None]


@dataclass
class Result:
    data: bytes
    filename: str
    before: bytes  # プレビュー用PNG（補正前）
    after: bytes  # プレビュー用PNG（補正後）
    notes: List[str] = field(default_factory=list)


def is_supported(filename: str) -> bool:
    ext = Path(filename).suffix.lower()
    return ext == ".pdf" or ext in IMAGE_EXTS


def process(data: bytes, filename: str, opts: Options, progress: Optional[ProgressFn] = None) -> Result:
    if Path(filename).suffix.lower() == ".pdf":
        return _process_pdf(data, filename, opts, progress)
    return _process_image(data, filename, opts, progress)


def _output_name(filename: str, ext: str) -> str:
    return f"{Path(filename).stem}_高画質{ext}"


def _png(img: np.ndarray) -> bytes:
    ok, buf = cv2.imencode(".png", cv2.cvtColor(img, cv2.COLOR_RGB2BGR))
    if not ok:
        raise RuntimeError("PNGへの変換に失敗しました")
    return buf.tobytes()


def _fit(img: np.ndarray, max_edge: int = PREVIEW_MAX_EDGE) -> np.ndarray:
    h, w = img.shape[:2]
    if max(h, w) <= max_edge:
        return img
    r = max_edge / max(h, w)
    return cv2.resize(img, (round(w * r), round(h * r)), interpolation=cv2.INTER_AREA)


# ---------- 画像ファイル ----------

def _process_image(data: bytes, filename: str, opts: Options, progress: Optional[ProgressFn]) -> Result:
    pil = ImageOps.exif_transpose(Image.open(io.BytesIO(data)))
    has_alpha = pil.mode in ("RGBA", "LA", "PA") or (pil.mode == "P" and "transparency" in pil.info)
    rgba = np.array(pil.convert("RGBA")) if has_alpha else None
    rgb = np.array(pil.convert("RGB"))

    out = enhance(rgb, opts, progress)
    h, w = out.shape[:2]
    if rgba is not None:
        alpha = cv2.resize(rgba[:, :, 3], (w, h), interpolation=cv2.INTER_LANCZOS4)
        encoded = _encode_png_rgba(out, alpha)
    else:
        encoded = _png(out)

    # 補正前プレビューは、元画像をビューアで拡大表示したときと同じ見え方にする
    before = cv2.resize(rgb, (w, h), interpolation=cv2.INTER_LINEAR)
    return Result(
        data=encoded,
        filename=_output_name(filename, ".png"),
        before=_png(_fit(before)),
        after=_png(_fit(out)),
        notes=[f"{rgb.shape[1]}×{rgb.shape[0]}px → {w}×{h}px"],
    )


def _encode_png_rgba(rgb: np.ndarray, alpha: np.ndarray) -> bytes:
    bgra = np.dstack([cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR), alpha])
    ok, buf = cv2.imencode(".png", bgra)
    if not ok:
        raise RuntimeError("PNGへの変換に失敗しました")
    return buf.tobytes()


# ---------- PDF ----------

def _process_pdf(data: bytes, filename: str, opts: Options, progress: Optional[ProgressFn]) -> Result:
    doc = pymupdf.open(stream=data, filetype="pdf")
    if doc.needs_pass:
        raise ValueError("パスワード付きのPDFは処理できません")

    # 画像xref → (それを含む最初のページ番号, smaskのxref)
    targets = {}
    for pno in range(doc.page_count):
        for info in doc[pno].get_images(full=True):
            xref, smask = info[0], info[1]
            if xref not in targets:
                targets[xref] = (pno, smask)

    notes: List[str] = []
    replaced = 0
    preview_page = 0
    sizes = []
    for i, (xref, (pno, smask)) in enumerate(targets.items()):
        def sub_progress(f: float, i: int = i) -> None:
            if progress:
                progress((i + f) / len(targets))

        try:
            rgb, alpha = _load_pdf_image(doc, xref, smask)
        except Exception:  # 特殊な形式の画像は補正せずそのまま残す
            continue
        h, w = rgb.shape[:2]
        if min(h, w) < MIN_IMAGE_EDGE:
            continue

        out = enhance(rgb, opts, sub_progress)
        _write_pdf_image(doc, xref, out, alpha)
        if replaced == 0:
            preview_page = pno
        replaced += 1
        sizes.append(f"{w}×{h}px → {out.shape[1]}×{out.shape[0]}px")

    if replaced == 0:
        notes.append("補正できる画像が含まれていないため、内容は変更していません（文字だけのPDFは元から拡大に強い形式です）")
    else:
        notes.append(f"{doc.page_count}ページ中の画像{replaced}点を高画質化")
        notes.extend(sizes[:3])
        if len(sizes) > 3:
            notes.append(f"ほか{len(sizes) - 3}点")

    out_bytes = doc.tobytes(garbage=3, deflate=True)
    before, after = _pdf_previews(data, out_bytes, preview_page, opts.scale)
    if progress:
        progress(1.0)
    return Result(data=out_bytes, filename=_output_name(filename, ".pdf"),
                  before=before, after=after, notes=notes)


def _load_pdf_image(doc: pymupdf.Document, xref: int, smask: int):
    if doc.xref_get_key(xref, "ImageMask")[1] == "true":
        raise ValueError("ステンシルマスクは対象外")
    pix = pymupdf.Pixmap(doc, xref)
    alpha = None
    if smask:
        mask = pymupdf.Pixmap(doc, smask)
        alpha = np.frombuffer(mask.samples, dtype=np.uint8).reshape(mask.height, mask.width, mask.n)[:, :, 0]
        if alpha.shape != (pix.height, pix.width):
            alpha = cv2.resize(alpha, (pix.width, pix.height), interpolation=cv2.INTER_LINEAR)
    if pix.alpha:
        pix = pymupdf.Pixmap(pix, 0)
    if pix.colorspace is None or pix.colorspace.n != 3:
        pix = pymupdf.Pixmap(pymupdf.csRGB, pix)
    rgb = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)[:, :, :3]
    return np.ascontiguousarray(rgb), alpha


def _write_pdf_image(doc: pymupdf.Document, xref: int, rgb: np.ndarray, alpha: Optional[np.ndarray]) -> None:
    """画像オブジェクトの中身を差し替える。

    同じxrefを参照している全ページに反映され、表示位置・大きさは変わらない。
    """
    h, w = rgb.shape[:2]
    if alpha is None:
        ok, buf = cv2.imencode(".jpg", cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR),
                               [cv2.IMWRITE_JPEG_QUALITY, JPEG_QUALITY])
        if not ok:
            raise RuntimeError("JPEGへの変換に失敗しました")
        doc.update_stream(xref, buf.tobytes(), compress=False)
        doc.xref_set_key(xref, "Filter", "/DCTDecode")
        doc.xref_set_key(xref, "SMask", "null")
    else:
        doc.update_stream(xref, rgb.tobytes(), compress=True)
        mask_xref = doc.get_new_xref()
        doc.update_object(mask_xref, f"<</Type/XObject/Subtype/Image/Width {w}/Height {h}"
                                     "/ColorSpace/DeviceGray/BitsPerComponent 8>>")
        alpha = cv2.resize(alpha, (w, h), interpolation=cv2.INTER_LANCZOS4)
        doc.update_stream(mask_xref, np.ascontiguousarray(alpha).tobytes(), compress=True)
        doc.xref_set_key(xref, "SMask", f"{mask_xref} 0 R")
    doc.xref_set_key(xref, "Width", str(w))
    doc.xref_set_key(xref, "Height", str(h))
    doc.xref_set_key(xref, "ColorSpace", "/DeviceRGB")
    doc.xref_set_key(xref, "BitsPerComponent", "8")
    for key in ("DecodeParms", "Decode", "Mask", "Intent"):
        doc.xref_set_key(xref, key, "null")


def _pdf_previews(before_pdf: bytes, after_pdf: bytes, pno: int, scale: int):
    """同じページを同じ解像度で描画し、見比べ用の画像を作る。"""
    imgs = []
    for data in (before_pdf, after_pdf):
        doc = pymupdf.open(stream=data, filetype="pdf")
        page = doc[pno]
        # 元の画像が約100dpi程度の想定で、拡大後の細部が見える解像度で描画する
        zoom = min(scale * 100 / 72, PREVIEW_MAX_EDGE / max(page.rect.width, page.rect.height))
        pix = page.get_pixmap(matrix=pymupdf.Matrix(zoom, zoom), alpha=False)
        arr = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)[:, :, :3]
        imgs.append(_png(np.ascontiguousarray(arr)))
    return imgs[0], imgs[1]
