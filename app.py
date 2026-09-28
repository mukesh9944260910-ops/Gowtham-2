import io
import numpy as np
import requests
import streamlit as st
from PIL import Image

st.set_page_config(page_title="Fit Check", page_icon="👗", layout="centered")
st.title("👗 Fit Check")
st.caption("Unga photo + dress photo/link. Buy panna munnadi fit paathukalaam.")

try:
    from rembg import remove  # optional: better background removal
except Exception:
    remove = None


def dress_from_url(url):
    r = requests.get(url, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
    r.raise_for_status()
    return Image.open(io.BytesIO(r.content)).convert("RGBA")


def cut_white(img, th):
    a = np.array(img)
    mask = (a[..., 0] > th) & (a[..., 1] > th) & (a[..., 2] > th)
    a[mask, 3] = 0
    return Image.fromarray(a)


st.header("1. Photos")
me_file = st.file_uploader("Unga photo", type=["jpg", "jpeg", "png", "webp"])
d_file = st.file_uploader("Dress photo", type=["jpg", "jpeg", "png", "webp"])
d_url = st.text_input("...illa dress image link (direct image URL)")

me = Image.open(me_file).convert("RGBA") if me_file else None
dress = None
try:
    if d_file:
        dress = Image.open(d_file).convert("RGBA")
    elif d_url:
        dress = dress_from_url(d_url)
except Exception as e:
    st.error(f"Dress load aagala: {e}. Direct image link (.jpg/.png) kudunga.")

st.header("2. Try on")
if me and dress:
    mode = st.radio("Background remove", ["White background", "AI (rembg)", "None"],
                    horizontal=True, index=0)
    if mode == "White background":
        dress = cut_white(dress, st.slider("White threshold", 200, 255, 240))
    elif mode == "AI (rembg)":
        if remove:
            dress = remove(dress)
        else:
            st.warning("rembg install aagala. requirements.txt-la rembg add pannunga.")

    c1, c2 = st.columns(2)
    scale = c1.slider("Size %", 10, 250, 80)
    rot = c2.slider("Rotate", -45, 45, 0)
    px = c1.slider("Left / Right %", 0, 100, 50)
    py = c2.slider("Up / Down %", 0, 100, 50)
    op = st.slider("Opacity %", 30, 100, 92)

    w = int(me.width * scale / 100)
    d = dress.resize((w, int(dress.height * w / dress.width)))
    d = d.rotate(-rot, expand=True, resample=Image.BICUBIC)
    alpha = d.getchannel("A").point(lambda v: int(v * op / 100))
    d.putalpha(alpha)
    out = me.copy()
    out.paste(d, (int(me.width * px / 100 - d.width / 2),
                  int(me.height * py / 100 - d.height / 2)), d)
    st.image(out, use_container_width=True)
    buf = io.BytesIO()
    out.convert("RGB").save(buf, "PNG")
    st.download_button("Save image", buf.getvalue(), "tryon.png", "image/png")
else:
    st.info("Rendu photos-um upload pannunga.")

st.header("3. Size recommend")
SIZES = ["XS", "S", "M", "L", "XL", "XXL"]
LIM = {"bust": [82, 86, 91, 97, 103, 109],
       "waist": [64, 68, 73, 79, 85, 91],
       "hips": [88, 92, 97, 103, 109, 115]}
c1, c2, c3 = st.columns(3)
vals = {"bust": c1.number_input("Bust (cm)", 0.0, 200.0, 0.0),
        "waist": c2.number_input("Waist (cm)", 0.0, 200.0, 0.0),
        "hips": c3.number_input("Hips (cm)", 0.0, 200.0, 0.0)}
if st.button("Find my size", type="primary"):
    idx = []
    for k, v in vals.items():
        if v > 0:
            idx.append(next((i for i, m in enumerate(LIM[k]) if v <= m), 5))
    if not idx:
        st.warning("Ethavathu oru measurement enter pannunga.")
    else:
        best = max(idx)
        st.success(f"Recommended size: {SIZES[best]}")
        if max(idx) - min(idx) >= 2:
            st.info("Measurements size-la vera vera irukku. Stretch fabric paathu select pannunga.")
        elif best < 5:
            st.caption(f"Loose fit venumna {SIZES[best + 1]} edukkalaam.")
st.caption("General size chart. Shop-oda chart-oda compare pannunga.")
