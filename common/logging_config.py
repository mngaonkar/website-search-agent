import logging

logger = logging.getLogger(__name__)

file_handler = logging.FileHandler('website_search_agent.log')
file_handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)