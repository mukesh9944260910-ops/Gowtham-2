# Fit Check Gemini (Streamlit + Google AI Studio key)
1. Push app.py and requirements.txt to GitHub.
2. share.streamlit.io -> New app -> pick repo -> Advanced settings -> Secrets:
   GEMINI_API_KEY = "your_key"
3. Deploy.
Local: export GEMINI_API_KEY=your_key && pip install -r requirements.txt && streamlit run app.py
Never commit the key to GitHub.
