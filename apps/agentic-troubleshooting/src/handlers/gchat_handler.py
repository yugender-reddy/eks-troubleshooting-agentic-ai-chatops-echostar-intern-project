"""Google Chat webhook handler for the K8s troubleshooting agent.

When MOCK_MODE=true, uses canned responses instead of the real orchestrator.
To switch to real mode: set MOCK_MODE=false (requires AWS + Bedrock access).
"""

import os
import logging
from src.config.rate_limiter import bedrock_limiter, RATE_LIMIT_MSG

logger = logging.getLogger(__name__)

MOCK_MODE = os.getenv("MOCK_MODE", "true").lower() == "true"

# ─── MOCK ORCHESTRATOR (remove this block once credentials arrive) ───────────
_MOCK_RESPONSES = {
    "crashloopbackoff": (
        "**CrashLoopBackOff Analysis**\n\n"
        "Common causes:\n"
        "• Application error on startup (check logs with `kubectl logs <pod>`)\n"
        "• Missing ConfigMap/Secret references\n"
        "• Insufficient memory (OOMKilled)\n"
        "• Failed liveness probe\n\n"
        "Recommended: Run `kubectl describe pod <pod-name>` to inspect events."
    ),
    "oomkilled": (
        "**OOMKilled Analysis**\n\n"
        "The container exceeded its memory limit.\n"
        "• Increase `resources.limits.memory` in the pod spec\n"
        "• Check for memory leaks in the application\n"
        "• Review container metrics in Grafana"
    ),
    "imagepullbackoff": (
        "**ImagePullBackOff Analysis**\n\n"
        "• Verify image name and tag exist in the registry\n"
        "• Check ECR/registry authentication (imagePullSecrets)\n"
        "• Ensure nodes have network access to the registry"
    ),
}

_MOCK_DEFAULT = (
    "**K8s Troubleshooting Agent (Mock Mode)**\n\n"
    "I received your query and would normally analyze the cluster state via EKS MCP Server "
    "and search historical cases in the S3 Vectors knowledge base.\n\n"
    "Once connected to AWS, I will provide real-time diagnostics."
)


def _mock_response(user_prompt: str) -> str:
    """Return a canned response matching keywords in the prompt."""
    lower = user_prompt.lower()
    for keyword, response in _MOCK_RESPONSES.items():
        if keyword in lower:
            return response
    return _MOCK_DEFAULT
# ─── END MOCK BLOCK ─────────────────────────────────────────────────────────


# Lazy-initialized orchestrator singleton (only used when MOCK_MODE=false)
_orchestrator = None


def _get_orchestrator():
    """Lazy-init the orchestrator to avoid startup cost on import."""
    global _orchestrator
    if _orchestrator is None:
        from src.agents.agent_orchestrator import OrchestratorAgent
        _orchestrator = OrchestratorAgent()
    return _orchestrator


def handle_gchat_message(payload: dict) -> dict:
    """Parses Google Chat event and returns a response.

    Uses mock responses when MOCK_MODE=true, real orchestrator otherwise.
    """
    event_type = payload.get("type", "")

    # Handle bot added to space
    if event_type == "ADDED_TO_SPACE":
        return _welcome_response(payload)

    # Extract message data
    user_prompt = payload.get("message", {}).get("text", "").strip()
    space_name = payload.get("space", {}).get("name", "")
    thread_name = payload.get("message", {}).get("thread", {}).get("name", "")
    sender = payload.get("message", {}).get("sender", {}).get("displayName", "User")

    logger.info(f"Google Chat message from '{sender}' in space '{space_name}': {user_prompt[:80]}")

    if not user_prompt:
        return _text_response("Please provide a message for me to analyze.", thread_name)

    # ─── Route to mock or real orchestrator ──────────────────────────────
    if MOCK_MODE:
        response_text = _mock_response(user_prompt)
    else:
        response_text = _invoke_orchestrator(user_prompt)

    return _card_response(response_text, thread_name)


def _invoke_orchestrator(user_prompt: str) -> str:
    """Call the real orchestrator agent. Only runs when MOCK_MODE=false."""
    if not bedrock_limiter.allow():
        return RATE_LIMIT_MSG

    from src.agents.agent_orchestrator import AgentSilentException

    try:
        orchestrator = _get_orchestrator()
        orchestrator.last_user_message = user_prompt
        agent_response = orchestrator.agent(user_prompt)

        if hasattr(agent_response, 'content'):
            response_text = str(agent_response.content).strip()
        elif hasattr(agent_response, 'text'):
            response_text = str(agent_response.text).strip()
        elif isinstance(agent_response, (list, tuple)):
            response_text = ' '.join(str(part) for part in agent_response).strip()
        else:
            response_text = str(agent_response).strip()

        return response_text or "I'm here to help with Kubernetes troubleshooting. How can I assist you?"

    except AgentSilentException:
        return (
            "This doesn't appear to be a Kubernetes-related question. "
            "I'm specialized in EKS cluster troubleshooting — feel free to ask me "
            "about pod issues, deployments, services, or cluster health."
        )
    except Exception as e:
        logger.error(f"Orchestrator error: {e}", exc_info=True)
        return "I encountered an error processing your request. Please try again."


def _welcome_response(payload: dict) -> dict:
    """Response when bot is added to a space."""
    thread_name = payload.get("message", {}).get("thread", {}).get("name", "")
    return _text_response(
        "Hello! I'm the EKS ChatOps Assistant. I can help troubleshoot Kubernetes cluster issues. "
        "Ask me about pod failures, deployment problems, service connectivity, and more.",
        thread_name
    )


def _card_response(text: str, thread_name: str) -> dict:
    """Construct a Google Chat Card V2 response."""
    response = {
        "cardsV2": [{
            "cardId": "agent_response_card",
            "card": {
                "header": {
                    "title": "EKS ChatOps Assistant",
                    "subtitle": "Agentic Diagnostics Engine"
                },
                "sections": [{
                    "widgets": [{"textParagraph": {"text": text}}]
                }]
            }
        }]
    }
    if thread_name:
        response["thread"] = {"name": thread_name}
    return response


def _text_response(text: str, thread_name: str) -> dict:
    """Construct a simple text response for Google Chat."""
    response = {"text": text}
    if thread_name:
        response["thread"] = {"name": thread_name}
    return response
