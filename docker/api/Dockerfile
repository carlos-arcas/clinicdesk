FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN useradd --create-home --shell /usr/sbin/nologin clinicdesk

COPY requirements.txt ./requirements.txt
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

COPY clinicdesk ./clinicdesk

RUN chown -R clinicdesk:clinicdesk /app

USER clinicdesk

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/healthz', timeout=3)"

CMD ["python", "-m", "clinicdesk.web.api.serve"]
