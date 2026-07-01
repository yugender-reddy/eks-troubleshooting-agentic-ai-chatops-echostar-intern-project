"""Configuration settings for the EKS ChatOps Troubleshooting Agent."""

import os


class Config:
    """Configuration class for the Strands Google Chat Agent."""
    
    def validate(self) -> None:
        """Validate required configuration based on active chat platform."""
        mock_mode = os.getenv('MOCK_MODE', 'true').lower() == 'true'
        chat_platform = os.getenv('CHAT_PLATFORM', 'slack').lower()

        if mock_mode:
            import logging
            logging.getLogger(__name__).info(
                "MOCK_MODE=true — skipping credential validation. "
                "Set MOCK_MODE=false once real credentials are available."
            )
            return

        missing = []

        if chat_platform == 'slack':
            if not os.getenv('SLACK_BOT_TOKEN', ''):
                missing.append('SLACK_BOT_TOKEN')
            if not os.getenv('SLACK_APP_TOKEN', ''):
                missing.append('SLACK_APP_TOKEN')
            if not os.getenv('SLACK_SIGNING_SECRET', ''):
                missing.append('SLACK_SIGNING_SECRET')
        elif chat_platform == 'gchat':
            if not os.getenv('GOOGLE_APPLICATION_CREDENTIALS', ''):
                missing.append('GOOGLE_APPLICATION_CREDENTIALS')
            if not os.getenv('GCHAT_PROJECT_NUMBER', ''):
                missing.append('GCHAT_PROJECT_NUMBER')

        if missing:
            raise ValueError(
                f"Missing required {chat_platform.upper()} credentials: {', '.join(missing)}. "
                "Set MOCK_MODE=true for local development without credentials."
            )
    
    # Platform Selector
    @property
    def CHAT_PLATFORM(self) -> str:
        """Active chat platform: 'slack' or 'gchat'."""
        return os.getenv('CHAT_PLATFORM', 'slack').lower()

    # Infrastructure & Core Platform Properties
    @property
    def CLUSTER_NAME(self) -> str:
        return os.getenv('CLUSTER_NAME', 'eks-cluster')
    
    @property
    def MEMORY_AGENT_SERVER_URL(self) -> str:
        return os.getenv('MEMORY_AGENT_SERVER_URL', 'http://127.0.0.1:9000')
    
    @property
    def AWS_REGION(self) -> str:
        return os.getenv('AWS_REGION', 'us-east-1')
    
    @property
    def BEDROCK_MODEL_ID(self) -> str:
        return os.getenv('BEDROCK_MODEL_ID', 'us.amazon.nova-micro-v1:0')

    @property
    def ORCHESTRATOR_MODEL_ID(self) -> str:
        return os.getenv('ORCHESTRATOR_MODEL_ID', 'us.amazon.nova-micro-v1:0')

    @property
    def REASONING_MODEL_ID(self) -> str:
        return os.getenv('REASONING_MODEL_ID', 'us.anthropic.claude-sonnet-4-20250514-v1:0')
    
    # Slack Properties (Active integration)
    @property
    def SLACK_BOT_TOKEN(self) -> str:
        return os.getenv('SLACK_BOT_TOKEN', '')

    @property
    def SLACK_APP_TOKEN(self) -> str:
        return os.getenv('SLACK_APP_TOKEN', '')

    @property
    def SLACK_SIGNING_SECRET(self) -> str:
        return os.getenv('SLACK_SIGNING_SECRET', '')

    @property
    def RESPONSE_DELAY_SECONDS(self) -> float:
        return float(os.getenv('RESPONSE_DELAY_SECONDS', '0'))

    @property
    def ENABLE_THREAD_CONTEXT(self) -> bool:
        return os.getenv('ENABLE_THREAD_CONTEXT', 'true').lower() == 'true'

    # Google Chat Properties (Retained for future use)
    @property
    def GOOGLE_APPLICATION_CREDENTIALS(self) -> str:
        """Path to the Service Account JSON key file."""
        return os.getenv('GOOGLE_APPLICATION_CREDENTIALS', '')

    @property
    def GCHAT_PROJECT_ID(self) -> str:
        """Your Google Cloud Project ID."""
        return os.getenv('GCHAT_PROJECT_ID', '')

    @property
    def GCHAT_PROJECT_NUMBER(self) -> str:
        """Your GCP project number (for JWT audience verification)."""
        return os.getenv('GCHAT_PROJECT_NUMBER', '')

    @property
    def MOCK_MODE(self) -> bool:
        """When True, bypasses Google Chat auth and uses mock orchestrator.
        Set to 'false' once real credentials are available."""
        return os.getenv('MOCK_MODE', 'true').lower() == 'true'
        
    # Agent Branding Metadata
    @property
    def AGENT_NAME(self) -> str:
        return os.getenv('AGENT_NAME', 'strands-gchat-agent')
    
    @property
    def AGENT_DESCRIPTION(self) -> str:
        return os.getenv(
            'AGENT_DESCRIPTION', 
            'An Agentic AI workflow for real-time EKS cluster discovery and troubleshooting.'
        )
    
    # Runtime Behaviours & Logging
    @property
    def LOG_LEVEL(self) -> str:
        return os.getenv('LOG_LEVEL', 'DEBUG')
    
    @property
    def LOG_FORMAT(self) -> str:
        return os.getenv('LOG_FORMAT', 'json')
    
    @property
    def RESPONSE_THRESHOLD(self) -> float:
        return float(os.getenv('RESPONSE_THRESHOLD', '0.7'))
    
    @property
    def MAX_CONTEXT_MESSAGES(self) -> int:
        return int(os.getenv('MAX_CONTEXT_MESSAGES', '10'))

    # Core Integrations
    @property
    def ENABLE_EKS_MCP(self) -> bool:
        return os.getenv('ENABLE_EKS_MCP', 'false').lower() == 'true'

    @property
    def ALLOW_WRITE(self) -> bool:
        return os.getenv('ALLOW_WRITE', 'true').lower() == 'true'

    # Langfuse Properties
    @property
    def ENABLE_LANGFUSE(self) -> bool:
        return os.getenv('ENABLE_LANGFUSE', 'false').lower() == 'true'

    @property
    def LANGFUSE_SECRET_KEY(self) -> str:
        return os.getenv('LANGFUSE_SECRET_KEY', '')

    @property
    def LANGFUSE_PUBLIC_KEY(self) -> str:
        return os.getenv('LANGFUSE_PUBLIC_KEY', '')

    @property
    def LANGFUSE_HOST(self) -> str:
        return os.getenv('LANGFUSE_HOST', 'http://localhost:3000')

# Create a singleton instance for use throughout the app
config_instance = Config()
Config = config_instance