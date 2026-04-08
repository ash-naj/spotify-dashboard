FROM python:3.12-slim

# creating a folder named app
WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# copying the folders except for those that were ignored in '.dockerignore'
COPY . .

# exposes port 8501 (streamlit)
EXPOSE 8501

CMD ["streamlit", "run", "visualize.py", "--server.port=8501", "--server.address=0.0.0.0"]