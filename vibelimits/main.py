from __future__ import annotations

import uvicorn


def cli() -> None:
    uvicorn.run("vibelimits.webapp:app", host="0.0.0.0", port=8080)


if __name__ == "__main__":
    cli()
