FROM python:3.10-slim

ENV PYTHONUNBUFFERED 1
ENV VIRTUAL_ENV=/opt/venv

RUN pip install --upgrade pip && pip install semgrep

RUN python3 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"
WORKDIR /app
COPY requirements.txt /app/
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt
COPY . /app
EXPOSE 8080
CMD ["python", "main.py"]