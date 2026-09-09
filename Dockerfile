# Strategy Evaluation Workbench — one process serves the UI and the API.
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8765 \
    STRATEGY_WORKSPACE_DIR=/data/workspace

WORKDIR /srv

COPY deploy/requirements-runtime.txt /srv/deploy/requirements-runtime.txt
RUN pip install --no-cache-dir -r /srv/deploy/requirements-runtime.txt

# Frozen dataset (schemas, truth, corpus, injects, eval) and the product.
COPY dataset/ /srv/dataset/
COPY app/backend/ /srv/app/backend/
COPY app/ui/ /srv/app/ui/

RUN useradd --create-home --uid 10001 workbench \
 && mkdir -p /data/workspace \
 && chown -R workbench:workbench /data /srv
USER workbench

EXPOSE 8765
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD python -c "import urllib.request,os,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:'+os.environ.get('PORT','8765')+'/api/health', timeout=4).status==200 else 1)"

CMD ["sh", "-c", "exec python -m uvicorn app.backend.main:app --host 0.0.0.0 --port ${PORT}"]
