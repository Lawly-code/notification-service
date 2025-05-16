import logging
import os

logging.basicConfig(level=logging.INFO)
__log__ = logging.getLogger(__name__)

SERVICE_ACCOUNT_PATH = "notification/data/lawly-cb472-de9fe3fd67d4.json"
PROJECT_ID = os.getenv("project_id")
