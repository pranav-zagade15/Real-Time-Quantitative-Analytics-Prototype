.PHONY: install test demo

install:
	python -m pip install -r requirements.txt

test:
	pytest -q

demo:
	python tools/gen_synthetic_ticks.py --out demo_ticks.csv --symbols SYM1 SYM2 --n 120
	streamlit run app.py
