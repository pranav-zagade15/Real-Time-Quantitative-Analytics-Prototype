# Streamlit Professional Site (streamlit_site)

This folder contains a polished Streamlit presentation layer for the Realtime Quant
prototype. It is intentionally self-contained and imports analytics from the
main repo without changing anything in `main`.

Quick start (local):

```bash
python -m venv .venv-site
source .venv-site/bin/activate
pip install -r requirements.txt
streamlit run site_app.py
```

Docker:

```bash
docker build -t realtime-quant-site:latest .
docker run -p 8501:8501 realtime-quant-site:latest
```

Notes:
- The site is built for demonstration; it keeps processing in-memory and is not
  intended for production-grade throughput.
- Add a screenshot `assets/dashboard-demo.png` for the PR.
