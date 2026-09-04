import logging
import sys
from app.core.paths import get_data_dir

def setup_logging():
    log_file = get_data_dir() / "logs" / "vicentra.log"
    handlers = [
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(log_file, encoding="utf-8", mode="a"),
    ]
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=handlers,
        force=True,
    )
    # Reduce noise from some libraries if needed
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)

logger = logging.getLogger("ibvap")
