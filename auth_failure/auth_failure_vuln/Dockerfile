FROM python:3.10-slim
WORKDIR /app

COPY . /app

RUN pip install --no-cache-dir Flask

EXPOSE 8082

ENV FLASK_APP=app.py

CMD ["python", "app.py"]
