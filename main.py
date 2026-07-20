import logging
import setup_project
from core.pipeline import Pipeline

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    logger.info("Telugu AI Reel Factory V6 - Initializing...")
    setup_project.check_dependencies()
    setup_project.setup_directories()
    
    pipeline = Pipeline()
    pipeline.run()

if __name__ == "__main__":
    main()
