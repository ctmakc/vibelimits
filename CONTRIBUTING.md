# Contributing

Contributions are welcome, especially provider adapters, parsers, source collectors and tests.

Principles:

1. Keep sensor reports limited to quota state required for correlation.
2. Prefer documented interfaces over brittle UI scraping.
3. Missing telemetry must produce no signal rather than guessed data.
4. A scheduled personal reset must not become a provider-wide alert.
5. New provider logic should include parser and false-positive tests.

Local setup:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
pytest -q
```

For a new provider, start with `vibelimits/providers.py`, then add only the source or normalization code that provider actually needs.
