"""Entrypoint for Slack Socket Mode integration.

Run: python main_slack.py

Requires:
  SLACK_BOT_TOKEN=xoxb-...
  SLACK_APP_TOKEN=xapp-...
  SLACK_SIGNING_SECRET=...
  MOCK_MODE=false (for live Bedrock + K8s)
"""

import logging
import sys
from dotenv import load_dotenv

load_dotenv()

from src.config.settings import Config

logging.basicConfig(
    level=getattr(logging, Config.LOG_LEVEL, logging.INFO),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


def main():
    Config.validate()
    logger.info("Configuration validated. Starting Slack bot...")

    from src.slack_handler import SlackHandler

    handler = SlackHandler()
    handler.start()


if __name__ == "__main__":
    main()
