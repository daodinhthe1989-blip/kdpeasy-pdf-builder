import io
import hashlib
from typing import List, Dict, Tuple

import streamlit as st
from PIL import Image, ImageOps
import img2pdf

# ═══════════════════════════════════════════════════════════════════
# 🔐 SECURITY SETTINGS — Edit these values to customize your app
# ═══════════════════════════════════════════════════════════════════
APP_PASSWORD = "KDPPDF2026"
BRAND_NAME = "KDPEasy Studio"
TOOL_NAME = "PDF Builder"
WELCOME_MESSAGE = "Welcome, VIP Customer!"
# ═══════════════════════════════════════════════════════════════════

# Maximum images per build (keeps memory and UI responsive)
MAX_IMAGES = 200

# Recommended minimum DPI for KDP print
KDP_MIN_DPI = 300

# KDP page-size presets — (width_inch, height_inch)
KDP_SIZES: Dict[str, Tuple[float, float]] = {
    "6 × 9 in  (Standard book)":            (6.0, 9.0),
    "6.14 × 9.21 in (Royal)":               (6.14, 9.21),
    "5 × 8 in  (Novel)":                    (5.0, 8.0),
    "5.5 × 8.5 in (Digest)":                (5.5, 8.5),
    "7 × 10 in (Workbook)":                 (7.0, 10.0),
    "8 × 10 in (Photo book)":               (8.0, 10.0),
    "8.5 × 8.5 in (Square — kids coloring)": (8.5, 8.5),
    "8.5 × 11 in (Letter)":                 (8.5, 11.0),
    "A4 (210 × 297 mm)":                    (8.27, 11.69),
    "A5 (148 × 210 mm)":                    (5.83, 8.27),
}

FIT_MODES = {
    "Fit  — preserve ratio, may have white margin":  "fit",
    "Fill — cover entire page, may crop edges":      "fill",
    "Center — keep original size, place at center":  "center",
}

st.set_page_config(
    page_title=f"{BRAND_NAME} — {TOOL_NAME}",
    page_icon="📄",
    layout="wide",
)

CUSTOM_CSS = """
<style>
    .main > div { padding-top: 2rem; }
    .stApp { background: linear-gradient(135deg, #f5f7fa 0%, #e8ecf3 100%); }
    .block-container { max-width: 1200px; }
    h1 { color: #1f2937; font-weight: 700; }
    h2, h3 { color: #1f2937; }
    .stButton>button {
        background-color: #4f46e5;
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.5rem 1rem;
        font-weight: 600;
        transition: background-color 0.2s ease;
    }
    .stButton>button:hover { background-color: #4338ca; color: white; }
    .stDownloadButton>button {
        background-color: #10b981;
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.6rem 1.4rem;
        font-weight: 700;
    }
    .stDownloadButton>button:hover { background-color: #059669; color: white; }
    div[data-testid="stFileUploader"] {
        background-color: white;
        border-radius: 12px;
        padding: 1rem;
        border: 2px dashed #cbd5e1;
    }
    .info-card {
        background: white;
        padding: 1rem 1.2rem;
        border-radius: 10px;
        border-left: 4px solid #4f46e5;
        margin-bottom: 1rem;
    }
    .warn-card {
        background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
        padding: 1rem 1.2rem;
        border-radius: 10px;
        border-left: 4px solid #f59e0b;
        margin-bottom: 1rem;
        color: #78350f;
    }
    .login-card {
        background: white;
        padding: 2.5rem 2rem;
        border-radius: 16px;
        box-shadow: 0 10px 40px rgba(0,0,0,0.08);
        max-width: 480px;
        margin: 3rem auto;
        text-align: center;
    }
    .login-card h2 { color: #1f2937; margin-bottom: 0.5rem; }
    .login-card .brand {
        color: #4f46e5;
        font-weight: 700;
        letter-spacing: 0.5px;
        text-transform: uppercase;
        font-size: 0.85rem;
        margin-bottom: 1rem;
    }
    .row {
        background: white;
        border-radius: 10px;
        padding: 0.6rem 0.8rem;
        margin-bottom: 0.5rem;
        border: 1px solid #e5e7eb;
    }
    .pos-badge {
        display: inline-block;
        background: #4f46e5;
        color: white;
        font-weight: 700;
        border-radius: 6px;
        padding: 2px 10px;
        font-size: 0.9rem;
        min-width: 36px;
        text-align: center;
    }
    .dpi-ok    { color: #047857; font-weight: 600; }
    .dpi-warn  { color: #b45309; font-weight: 600; }
    .dpi-bad   { color: #b91c1c; font-weight: 700; }
    .filename  { color: #374151; font-weight: 500; word-break: break-all; }
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════
# 🔐 Password gate
# ═══════════════════════════════════════════════════════════════════
def check_password() -> bool:
    if st.session_state.get("auth_ok"):
        return True

    st.markdown(
        f"""
        <div class="login-card">
            <div class="brand">{BRAND_NAME}</div>
            <h2>📄 {TOOL_NAME}</h2>
            <p style="color:#6b7280;margin-bottom:1.5rem;">
                Enter your VIP password to continue.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.form("login_form", clear_on_submit=False):
        pw = st.text_input("Password", type="password", label_visibility="collapsed",
                           placeholder="Enter password…")
        ok = st.form_submit_button("🔓 Unlock", use_container_width=True)

    if ok:
        if pw == APP_PASSWORD:
            st.session_state.auth_ok = True
            st.rerun()
        else:
            st.error("❌ Wrong password. Please try again.")
    return False


if not check_password():
    st.stop()


# ═══════════════════════════════════════════════════════════════════
# Header + logout
# ═══════════════════════════════════════════════════════════════════
header_left, header_right = st.columns([5, 1])
with header_left:
    st.markdown(
        f"<h1>📄 {TOOL_NAME}</h1>"
        f"<p style='color:#6b7280;margin-top:-0.5rem;'>{BRAND_NAME} — {WELCOME_MESSAGE}</p>",
        unsafe_allow_html=True,
    )
with header_right:
    st.write("")
    if st.button("Logout", use_container_width=True):
        for k in list(st.session_state.keys()):
            del st.session_state[k]
        st.rerun()


# ═══════════════════════════════════════════════════════════════════
# Sidebar — PDF settings
# ═══════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("### ⚙️ PDF settings")

    auto_fit_size = st.checkbox(
        "🪄 Auto-fit page size to first image",
        value=True,
        help="When ON, the PDF page size matches your uploaded images "
             "(px ÷ DPI). Great if your images already include KDP bleed "
             "or come from another tool. Turn OFF to force a specific "
             "size below.",
    )

    size_label = st.selectbox(
        "KDP page size", list(KDP_SIZES.keys()), index=0,
        disabled=auto_fit_size,
        help="Ignored when Auto-fit is on.",
    )
    page_w_in, page_h_in = KDP_SIZES[size_label]

    fit_label = st.selectbox(
        "Image fit mode", list(FIT_MODES.keys()), index=0,
        disabled=auto_fit_size,
        help="Ignored when Auto-fit is on (images are placed as-is).",
    )
    fit_mode = FIT_MODES[fit_label]

    bg_color_hex = st.color_picker("Page background color", "#FFFFFF")

    target_dpi = st.number_input(
        "Output DPI (KDP recommends 300)",
        min_value=150, max_value=600, value=300, step=50,
    )

    jpeg_quality = st.slider(
        "JPEG quality (higher = bigger file)",
        min_value=70, max_value=98, value=92,
    )

    output_filename = st.text_input("Output filename", value="kdp-book.pdf")
    if not output_filename.lower().endswith(".pdf"):
        output_filename += ".pdf"

    st.markdown("---")
    st.markdown(
        '<div class="info-card" style="font-size:0.85rem;">'
        '💡 <b>Tip:</b> If any image shows a low-DPI warning, '
        'run it through the <b>KDPEasy AI Upscaler</b> first '
        'to get crisp print quality.'
        "</div>",
        unsafe_allow_html=True,
    )


# ═══════════════════════════════════════════════════════════════════
# Upload
# ═══════════════════════════════════════════════════════════════════
st.markdown("### 1️⃣ Upload your images")

uploaded = st.file_uploader(
    "Drag & drop images here (PNG, JPG, JPEG, WEBP, TIFF). "
    f"Up to {MAX_IMAGES} files.",
    type=["png", "jpg", "jpeg", "webp", "tiff", "tif"],
    accept_multiple_files=True,
)

# Persistent ordered list of images across reruns.
# Each entry: {"id": str, "name": str, "bytes": bytes}
if "image_order" not in st.session_state:
    st.session_state.image_order = []


def _hash_bytes(b: bytes) -> str:
    return hashlib.md5(b).hexdigest()[:12]


# Sync uploaded → session state (dedupe by content hash)
if uploaded:
    existing_ids = {item["id"] for item in st.session_state.image_order}
    seen_in_upload = set()
    for f in uploaded:
        data = f.getvalue()
        item_id = _hash_bytes(data)
        seen_in_upload.add(item_id)
        if item_id not in existing_ids:
            if len(st.session_state.image_order) >= MAX_IMAGES:
                st.warning(
                    f"⚠️ Limit is {MAX_IMAGES} images. Extra files were ignored."
                )
                break
            st.session_state.image_order.append({
                "id": item_id,
                "name": f.name,
                "bytes": data,
            })
    # Drop entries the user removed from the uploader widget
    st.session_state.image_order = [
        x for x in st.session_state.image_order if x["id"] in seen_in_upload
    ]
else:
    if st.session_state.image_order:
        st.session_state.image_order = []


N = len(st.session_state.image_order)


# ═══════════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════════
@st.cache_data(show_spinner=False, max_entries=400)
def make_thumbnail(image_bytes: bytes, max_size: int = 90) -> bytes:
    img = Image.open(io.BytesIO(image_bytes))
    img = ImageOps.exif_transpose(img)
    img.thumbnail((max_size, max_size))
    if img.mode in ("RGBA", "P", "LA"):
        bg = Image.new("RGB", img.size, (255, 255, 255))
        if img.mode != "RGBA":
            img = img.convert("RGBA")
        bg.paste(img, mask=img.split()[-1])
        img = bg
    else:
        img = img.convert("RGB")
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=80)
    return buf.getvalue()


@st.cache_data(show_spinner=False, max_entries=400)
def image_dimensions(image_bytes: bytes) -> Tuple[int, int]:
    img = Image.open(io.BytesIO(image_bytes))
    img = ImageOps.exif_transpose(img)
    return img.size  # (w, h)


def effective_dpi(img_w: int, img_h: int, page_w_in: float, page_h_in: float) -> int:
    """How many pixels per inch we'd get if this image filled the page."""
    return int(min(img_w / page_w_in, img_h / page_h_in))


def dpi_badge_html(dpi: int) -> str:
    if dpi >= KDP_MIN_DPI:
        return f'<span class="dpi-ok">✅ {dpi} DPI</span>'
    elif dpi >= 200:
        return f'<span class="dpi-warn">⚠️ {dpi} DPI (low)</span>'
    else:
        return f'<span class="dpi-bad">❌ {dpi} DPI (too low)</span>'


def hex_to_rgb(hex_str: str) -> Tuple[int, int, int]:
    h = hex_str.lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))


def _move(idx: int, delta: int):
    order = st.session_state.image_order
    new_idx = idx + delta
    if 0 <= new_idx < len(order):
        order[idx], order[new_idx] = order[new_idx], order[idx]


def _remove(idx: int):
    if 0 <= idx < len(st.session_state.image_order):
        st.session_state.image_order.pop(idx)


def _jump_to(idx: int, new_pos_1based: int):
    order = st.session_state.image_order
    new_idx = max(0, min(len(order) - 1, new_pos_1based - 1))
    if new_idx != idx:
        item = order.pop(idx)
        order.insert(new_idx, item)


# ═══════════════════════════════════════════════════════════════════
# Image list with reorder controls
# ═══════════════════════════════════════════════════════════════════
if N == 0:
    st.info("👆 Upload at least one image to get started.")
else:
    st.markdown(f"### 2️⃣ Arrange the {N} images in order")
    st.caption(
        "Use ⬆️ / ⬇️ to move one step, or type a position number to jump. "
        "❌ removes the image from this PDF (it stays in the uploader)."
    )

    bg_rgb = hex_to_rgb(bg_color_hex)
    low_dpi_count = 0

    # Header row
    h1, h2, h3, h4, h5, h6, h7 = st.columns([0.5, 1, 4, 1.5, 0.7, 0.7, 0.7])
    h1.markdown("**#**")
    h2.markdown("**Preview**")
    h3.markdown("**File**")
    h4.markdown("**Quality**")
    h5.markdown("**Up**")
    h6.markdown("**Down**")
    h7.markdown("**Remove**")

    for i, item in enumerate(list(st.session_state.image_order)):
        c1, c2, c3, c4, c5, c6, c7 = st.columns([0.5, 1, 4, 1.5, 0.7, 0.7, 0.7])

        with c1:
            new_pos = st.number_input(
                "pos",
                min_value=1, max_value=N, value=i + 1, step=1,
                key=f"pos_{item['id']}",
                label_visibility="collapsed",
            )
            if new_pos != i + 1:
                _jump_to(i, int(new_pos))
                st.rerun()

        with c2:
            try:
                c2.image(make_thumbnail(item["bytes"]), width=70)
            except Exception:
                c2.markdown("⚠️")

        with c3:
            try:
                w, h = image_dimensions(item["bytes"])
                size_str = f"{w} × {h} px"
            except Exception:
                w, h, size_str = 0, 0, "unreadable"
            st.markdown(
                f'<div class="filename">{item["name"]}</div>'
                f'<div style="color:#9ca3af;font-size:0.8rem;">{size_str}</div>',
                unsafe_allow_html=True,
            )

        with c4:
            if w and h:
                if auto_fit_size:
                    # Page size will match the PNG so effective DPI = target.
                    dpi = int(target_dpi)
                else:
                    dpi = effective_dpi(w, h, page_w_in, page_h_in)
                if dpi < KDP_MIN_DPI:
                    low_dpi_count += 1
                st.markdown(dpi_badge_html(dpi), unsafe_allow_html=True)
            else:
                st.markdown("—")

        with c5:
            if st.button("⬆️", key=f"up_{item['id']}", disabled=(i == 0),
                         use_container_width=True):
                _move(i, -1)
                st.rerun()
        with c6:
            if st.button("⬇️", key=f"dn_{item['id']}", disabled=(i == N - 1),
                         use_container_width=True):
                _move(i, +1)
                st.rerun()
        with c7:
            if st.button("❌", key=f"rm_{item['id']}", use_container_width=True):
                _remove(i)
                st.rerun()

    if low_dpi_count > 0:
        st.markdown(
            f'<div class="warn-card">'
            f'⚠️ <b>{low_dpi_count}</b> of your images will be below '
            f'{KDP_MIN_DPI} DPI at the chosen page size '
            f'({page_w_in}" × {page_h_in}"). '
            "KDP print may look soft or pixelated. "
            "Consider running them through the "
            "<b>KDPEasy AI Upscaler</b> first."
            "</div>",
            unsafe_allow_html=True,
        )


# ═══════════════════════════════════════════════════════════════════
# PDF generation
# ═══════════════════════════════════════════════════════════════════
def composite_page(image_bytes: bytes,
                   page_w_in: float, page_h_in: float,
                   dpi: int, fit_mode: str,
                   bg_rgb: Tuple[int, int, int],
                   jpeg_quality: int) -> bytes:
    """Render one image onto a page-sized RGB canvas, return JPEG bytes."""
    page_w_px = int(round(page_w_in * dpi))
    page_h_px = int(round(page_h_in * dpi))

    src = Image.open(io.BytesIO(image_bytes))
    src = ImageOps.exif_transpose(src)
    if src.mode in ("RGBA", "P", "LA"):
        src_rgba = src.convert("RGBA")
    else:
        src_rgba = src.convert("RGB").convert("RGBA")

    canvas = Image.new("RGB", (page_w_px, page_h_px), bg_rgb)
    sw, sh = src_rgba.size

    if fit_mode == "fit":
        scale = min(page_w_px / sw, page_h_px / sh)
        new_w = max(1, int(round(sw * scale)))
        new_h = max(1, int(round(sh * scale)))
        resized = src_rgba.resize((new_w, new_h), Image.LANCZOS)
        x = (page_w_px - new_w) // 2
        y = (page_h_px - new_h) // 2
        canvas.paste(resized, (x, y), resized)

    elif fit_mode == "fill":
        scale = max(page_w_px / sw, page_h_px / sh)
        new_w = max(1, int(round(sw * scale)))
        new_h = max(1, int(round(sh * scale)))
        resized = src_rgba.resize((new_w, new_h), Image.LANCZOS)
        x = (page_w_px - new_w) // 2
        y = (page_h_px - new_h) // 2
        canvas.paste(resized, (x, y), resized)

    else:  # center — no resize, but if image is bigger than page, shrink to fit
        if sw > page_w_px or sh > page_h_px:
            scale = min(page_w_px / sw, page_h_px / sh)
            new_w = max(1, int(round(sw * scale)))
            new_h = max(1, int(round(sh * scale)))
            resized = src_rgba.resize((new_w, new_h), Image.LANCZOS)
        else:
            resized = src_rgba
        new_w, new_h = resized.size
        x = (page_w_px - new_w) // 2
        y = (page_h_px - new_h) // 2
        canvas.paste(resized, (x, y), resized)

    buf = io.BytesIO()
    canvas.save(buf, format="JPEG", quality=int(jpeg_quality),
                dpi=(dpi, dpi), optimize=True)
    return buf.getvalue()


def build_pdf(items: List[Dict],
              page_w_in: float, page_h_in: float,
              dpi: int, fit_mode: str,
              bg_rgb: Tuple[int, int, int],
              jpeg_quality: int,
              progress_cb=None) -> bytes:
    page_jpegs: List[bytes] = []
    for idx, item in enumerate(items):
        page_jpegs.append(
            composite_page(item["bytes"], page_w_in, page_h_in,
                           dpi, fit_mode, bg_rgb, jpeg_quality)
        )
        if progress_cb:
            progress_cb((idx + 1) / len(items))

    layout = img2pdf.get_layout_fun(
        pagesize=(img2pdf.in_to_pt(page_w_in), img2pdf.in_to_pt(page_h_in)),
        fit=img2pdf.FitMode.exact,
    )
    return img2pdf.convert(page_jpegs, layout_fun=layout)


# ═══════════════════════════════════════════════════════════════════
# Build button + download
# ═══════════════════════════════════════════════════════════════════
if N > 0:
    # When auto-fit is on, override page size with first image's dimensions
    effective_w_in, effective_h_in = page_w_in, page_h_in
    effective_fit_mode = fit_mode
    effective_size_label = size_label
    if auto_fit_size:
        try:
            first_img = Image.open(io.BytesIO(
                st.session_state.image_order[0]["bytes"]))
            first_img = ImageOps.exif_transpose(first_img)
            iw, ih = first_img.size
            effective_w_in = iw / float(target_dpi)
            effective_h_in = ih / float(target_dpi)
            effective_fit_mode = "fit"  # images at native size: identity for matching pages
            effective_size_label = (
                f"Auto {effective_w_in:.3f}\" × {effective_h_in:.3f}\""
                f"  (from {iw}×{ih} px @ {target_dpi} DPI)"
            )
        except Exception:
            pass

    st.markdown("### 3️⃣ Build your KDP PDF")
    col_a, col_b = st.columns([1, 2])
    with col_a:
        go = st.button(f"📄 Build PDF ({N} pages)", use_container_width=True)
    with col_b:
        st.caption(
            f"Page size: **{effective_size_label}**  •  "
            f"Fit: **{effective_fit_mode.title()}**  •  "
            f"DPI: **{target_dpi}**  •  "
            f"Quality: **{jpeg_quality}**"
        )

    if go:
        progress = st.progress(0.0, text="Composing pages…")
        try:
            pdf_bytes = build_pdf(
                st.session_state.image_order,
                effective_w_in, effective_h_in,
                int(target_dpi), effective_fit_mode,
                hex_to_rgb(bg_color_hex),
                int(jpeg_quality),
                progress_cb=lambda p: progress.progress(p, text=f"Composing pages… {int(p*100)}%"),
            )
            progress.progress(1.0, text="Done!")
            size_mb = len(pdf_bytes) / (1024 * 1024)
            st.success(
                f"✅ PDF ready — {N} pages, {size_mb:.1f} MB. "
                "Click below to download."
            )
            st.download_button(
                label=f"⬇️ Download {output_filename}",
                data=pdf_bytes,
                file_name=output_filename,
                mime="application/pdf",
                use_container_width=True,
            )
        except Exception as e:
            progress.empty()
            st.error(f"❌ Could not build the PDF: {e}")


# ═══════════════════════════════════════════════════════════════════
# Footer
# ═══════════════════════════════════════════════════════════════════
st.markdown("---")
st.markdown(
    f"<div style='text-align:center;color:#9ca3af;font-size:0.85rem;'>"
    f"{BRAND_NAME} — {TOOL_NAME}  •  Made with ❤️ for KDP creators"
    f"</div>",
    unsafe_allow_html=True,
)
