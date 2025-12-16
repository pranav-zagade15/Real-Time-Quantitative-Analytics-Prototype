FROM python:3.12-slim
WORKDIR /app
COPY . /app
# install site-specific deps
RUN python -m pip install --upgrade pip && \
    pip install -r requirements.txt
# Expose Streamlit port
EXPOSE 8501
CMD ["streamlit", "run", "site_app.py", "--server.port", "8501", "--server.headless", "true"]
