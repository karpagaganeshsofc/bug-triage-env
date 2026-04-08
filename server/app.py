"""Root-level server entry point for openenv validate compatibility."""
import uvicorn
from bug_triage_env.server import app  # noqa: F401


def main():
    uvicorn.run(app, host="0.0.0.0", port=7860)


if __name__ == "__main__":
    main()
