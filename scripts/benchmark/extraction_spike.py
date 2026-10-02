"""Repository-root CLI for the structured synthetic comparison harness."""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "apps/api"))

from app.extraction.spike import main


if __name__ == "__main__":
    main()
