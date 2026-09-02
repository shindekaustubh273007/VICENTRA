import logging
import sys

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    # Reduce noise from some libraries if needed
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)

logger = logging.getLogger("ibvap")
