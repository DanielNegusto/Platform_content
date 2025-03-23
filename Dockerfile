FROM python:3.12-slim

WORKDIR /app

RUN apt-get update \
  && apt-get install -y gcc libpq-dev \
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/\*

COPY req.txt .

RUN pip install --no-cache-dir -r req.txt

COPY . .


EXPOSE 8000