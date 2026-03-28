from rov_app.ai.openrouter_provider import OpenRouterProvider
from rov_app.ai.openai_provider import OpenAIProvider
from rov_app.ai.anthropic_provider import AnthropicProvider

PROVIDERS = {
    "openrouter": OpenRouterProvider,
    "openai": OpenAIProvider,
    "anthropic": AnthropicProvider,
}

def get_provider(name):
    cls = PROVIDERS.get(name)
    if cls is None:
        raise ValueError(f"Unknown provider: {name}. Choose from: {list(PROVIDERS.keys())}")
    return cls()
