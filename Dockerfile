FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml README.md ./
COPY vibelimits ./vibelimits
RUN pip install --no-cache-dir .
ENV DATABASE_URL=sqlite:////data/vibelimits.db
VOLUME ["/data"]
EXPOSE 8080
CMD ["vibelimits", "--host", "0.0.0.0", "--port", "8080"]
