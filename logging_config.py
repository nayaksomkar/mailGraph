# Logging setup — writes to both stdout and mailgraph.log

import logging
import sys

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler("mailgraph.log"),
        ],
    )
    return logging.getLogger("mailgraph")

logger = setup_logging()
