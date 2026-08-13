FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml README.md ./
COPY vibelimits ./vibelimits
RUN pip install --no-cache-dir .
ENV STATE_FILE=/data/vibelimits-state.json
VOLUME ["/data"]
EXPOSE 8080
CMD ["vibelimits"]
