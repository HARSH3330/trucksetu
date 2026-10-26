FROM clamav/clamav@sha256:e19130cdebaeacc71fa46eab3ed6f69941f2f22aa5e08d55e9197f8edf43ce5e
USER root
RUN apk add --no-cache python3 py3-pip && python3 -m venv /opt/venv && /opt/venv/bin/pip install --no-cache-dir boto3==1.42.72 Pillow==13.0.0 pypdf==6.21.2
COPY ops/clamav/clamd.conf /opt/scanner/clamd.conf
COPY backend/scan_worker.py /opt/scanner/scan_worker.py
COPY backend/app/services/scan_contract.py /opt/scanner/app/services/scan_contract.py
ENV PATH="/opt/venv/bin:$PATH" PYTHONUNBUFFERED=1 LC_ALL=C
WORKDIR /opt/scanner
USER clamav
ENTRYPOINT ["python3", "scan_worker.py"]
