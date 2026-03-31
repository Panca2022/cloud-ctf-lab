FROM python:3.10
WORKDIR /app
COPY app.py .
RUN pip install --no-cache-dir --default-timeout=100 flask requests
CMD ["python", "app.py"]

