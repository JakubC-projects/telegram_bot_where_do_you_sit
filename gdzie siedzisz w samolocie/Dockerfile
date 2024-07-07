FROM python:3.9.19-slim-bullseye AS base

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt ./
RUN python -m pip install -r requirements.txt

COPY main.py ./

CMD ["python3", "main.py"]
