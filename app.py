import io
import os
import tempfile
import time

import requests
import streamlit as st
from gradio_client import Client, handle_file
from PIL import Image

SPACE = "yisol/IDM-VTON"  # free public Hugging Face Space

st.set_page_config(page_title="Fit Check Free", page_icon="👗", layout="centered")
st.title("👗 Fit Check (Free AI)")
st.caption("Unga photo + shirt/dress photo. AI body-la potta maari image create pannum.")
st.info("Free service, so queue irukkum. 1-3 minutes aagalaam. Konjam porumaiya irunga.")


def save_tmp(img, max_side=1024):
    img = img.convert("RGB")
    img.thumbnail((max_side, max_side))
    f = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
    img.save(f, "JPEG", quality=92)
    f.close()
    return f.name


def get_client():
    token = st.secrets.get("HF_TOKEN", os.getenv("HF_TOKEN"))  # optional
    try:
        return Client(SPACE, hf_token=token) if token else Client(SPACE)
    except TypeError:
        return Client(SPACE)


def run_tryon(person, garment, desc, auto_mask, steps, seed):
    p, g = save_tmp(person), save_tmp(garment)
    last = None
    for attempt in range(1, 4):
        try:
            res = get_client().predict(
                dict={"background": handle_file(p), "layers": [], "composite": None},
                garm_img=handle_file(g),
                garment_des=desc,
                is_checked=auto_mask,
                is_checked_crop=False,
                denoise_steps=steps,
                seed=seed,
                api_name="/tryon",
            )
            with open(res[0], "rb") as f:
                return f.read()
        except Exception as e:
            last = e
            time.sleep(5 * attempt)
    raise last


st.header("1. Photos")
me_file = st.file_uploader("Unga photo (nerula paatha maari, clear-a)",
                           type=["jpg", "jpeg", "png", "webp"])
g_file = st.file_uploader("Shirt / dress photo", type=["jpg", "jpeg", "png", "webp"])
g_url = st.text_input("...illa direct image link")

garment = None
try:
    if g_file:
        garment = Image.open(g_file)
    elif g_url:
        r = requests.get(g_url, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
        r.raise_for_status()
        garment = Image.open(io.BytesIO(r.content))
except Exception as e:
    st.error(f"Garment load aagala: {e}")

desc = st.text_input("Short description", "blue cotton shirt")
with st.expander("Advanced"):
    steps = st.slider("Quality steps", 20, 40, 30)
    seed = st.number_input("Seed", 0, 9999, 42)
    auto_mask = st.checkbox("Auto mask", True)

c1, c2 = st.columns(2)
if me_file:
    c1.image(me_file, caption="Unga photo")
if garment:
    c2.image(garment, caption="Garment")

if st.button("Try it on", type="primary", disabled=not (me_file and garment)):
    with st.spinner("AI try-on nadakkuthu..."):
        try:
            st.session_state["result"] = run_tryon(
                Image.open(me_file), garment, desc, auto_mask, steps, int(seed))
        except Exception as e:
            st.error(f"Fail aachu: {e}\n\nSpace busy-a irukkalaam. Konjam neram kazhichu try pannunga.")

if "result" in st.session_state:
    st.header("2. Result")
    st.image(st.session_state["result"], use_container_width=True)
    st.download_button("Save image", st.session_state["result"], "tryon.png", "image/png")
    st.caption("AI preview mattum. Actual fit konjam vera irukkalaam.")
