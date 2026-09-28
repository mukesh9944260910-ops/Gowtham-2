import io
import os

import requests
import streamlit as st
from google import genai
from google.genai import types
from PIL import Image

MODELS = ["gemini-3.1-flash-image-preview",
          "gemini-3-pro-image-preview",
          "gemini-2.5-flash-image"]

st.set_page_config(page_title="Fit Check Gemini", page_icon="👗", layout="centered")
st.title("👗 Fit Check (Gemini)")
st.caption("Unga photo + shirt/dress photo. Gemini body-la potta maari image create pannum.")

key = st.secrets.get("GEMINI_API_KEY", os.getenv("GEMINI_API_KEY", ""))
if not key:
    key = st.text_input("Gemini API key", type="password",
                        help="aistudio.google.com/apikey-la irundhu edunga")
if not key:
    st.stop()

model = st.selectbox("Model", MODELS,
                     help="Oru model fail aana matha model try pannunga.")

PROMPT = (
    "Image 1 is a photo of a person. Image 2 is a garment ({kind}: {desc}). "
    "Edit image 1 so the person is wearing the garment from image 2. "
    "Keep the person's face, hair, skin tone, body shape, pose, hands and the "
    "background exactly the same. Only replace the clothing. Make the garment fit "
    "naturally with realistic folds, sleeves and drape. Keep the garment's exact "
    "color, pattern and details. Output one photorealistic image."
)


def shrink(img, side=1024):
    img = img.convert("RGB")
    img.thumbnail((side, side))
    return img


def tryon(person, garment, kind, desc):
    client = genai.Client(api_key=key)
    resp = client.models.generate_content(
        model=model,
        contents=[PROMPT.format(kind=kind, desc=desc), shrink(person), shrink(garment)],
        config=types.GenerateContentConfig(response_modalities=["TEXT", "IMAGE"]),
    )
    for cand in resp.candidates or []:
        for part in cand.content.parts or []:
            if part.inline_data and part.inline_data.data:
                return part.inline_data.data
    raise RuntimeError("Image varala. Model text mattum thirumbi anuppuchu. Vera photo try pannunga.")


st.header("1. Photos")
me_file = st.file_uploader("Unga photo (clear, nerula paatha maari)",
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

c1, c2 = st.columns(2)
kind = c1.selectbox("Type", ["shirt / top", "dress", "pant / skirt", "jacket"])
desc = c2.text_input("Short description", "blue cotton shirt")

d1, d2 = st.columns(2)
if me_file:
    d1.image(me_file, caption="Unga photo")
if garment:
    d2.image(garment, caption="Garment")

if st.button("Try it on", type="primary", disabled=not (me_file and garment)):
    with st.spinner("Gemini try-on nadakkuthu... 10-30 seconds"):
        try:
            st.session_state["result"] = tryon(Image.open(me_file), garment, kind, desc)
        except Exception as e:
            st.error(f"Fail aachu: {e}")
            st.caption("Quota / 429 error-na, ungal free key-la image models enable illa. "
                       "Vera model select pannunga illa konjam neram kazhichu try pannunga.")

if "result" in st.session_state:
    st.header("2. Result")
    st.image(st.session_state["result"], use_container_width=True)
    st.download_button("Save image", st.session_state["result"], "tryon.png", "image/png")
    st.caption("AI preview mattum. Actual fit konjam vera irukkalaam.")

st.header("3. Size recommend")
SIZES = ["XS", "S", "M", "L", "XL", "XXL"]
LIM = {"bust": [82, 86, 91, 97, 103, 109],
       "waist": [64, 68, 73, 79, 85, 91],
       "hips": [88, 92, 97, 103, 109, 115]}
s1, s2, s3 = st.columns(3)
vals = {"bust": s1.number_input("Bust / chest (cm)", 0.0, 200.0, 0.0),
        "waist": s2.number_input("Waist (cm)", 0.0, 200.0, 0.0),
        "hips": s3.number_input("Hips (cm)", 0.0, 200.0, 0.0)}
if st.button("Find my size"):
    idx = [next((i for i, m in enumerate(LIM[k]) if v <= m), 5)
           for k, v in vals.items() if v > 0]
    if not idx:
        st.warning("Ethavathu oru measurement enter pannunga.")
    else:
        best = max(idx)
        st.success(f"Recommended size: {SIZES[best]}")
        if max(idx) - min(idx) >= 2:
            st.info("Measurements size-la vera vera irukku. Stretch fabric paathu select pannunga.")
        elif best < 5:
            st.caption(f"Loose fit venumna {SIZES[best + 1]} edukkalaam.")
st.caption("General size chart. Shop-oda size chart-oda compare pannunga.")
