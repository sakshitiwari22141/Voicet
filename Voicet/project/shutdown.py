import os
import signal
import sys
import logging
import glob

logger = logging.getLogger(__name__)

def cleanup():
    """Clean up temporary files and logs shutdown."""
    logger.info("Starting graceful shutdown...")
    
    patterns = [
        "temp_*.wav",
        "output.wav",
        "output.mp4"
    ]
    
    # Flask runs inside the Voicet directory if using run.sh
    current_dir = os.getcwd()
    logger.info(f"Cleaning up temporary files in {current_dir}")
    
    for pattern in patterns:
        files = glob.glob(os.path.join(current_dir, pattern))
        for f in files:
            try:
                os.remove(f)
                logger.info(f"Deleted temporary file: {f}")
            except Exception as e:
                logger.error(f"Failed to delete {f}: {e}")

    logger.info("Graceful shutdown complete.")

def register_signal_handlers():
    """Registers handlers for SIGINT and SIGTERM."""
    def signal_handler(sig, frame):
        cleanup()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    logger.info("Signal handlers registered (SIGINT, SIGTERM).")
