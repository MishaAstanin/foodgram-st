FROM python:3.10
WORKDIR /app
COPY foodgram/requirements.txt .
RUN pip install -r requirements.txt --no-cache-dir
COPY foodgram/ .
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "foodgram.wsgi"] 