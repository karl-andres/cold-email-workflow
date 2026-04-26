"""LLM factory — returns the configured LangChain chat model."""

from langchain_core.language_models import BaseChatModel

from src.config import settings


def get_writer_llm() -> BaseChatModel:
    """Returns the writer/eval LLM based on the configured provider."""
    provider = settings.llm_provider
    if provider == "anthropic":
        from langchain_anthropic import ChatAnthropic
        return ChatAnthropic(
            model=settings.writer_model,
            api_key=settings.anthropic_api_key,  # type: ignore[arg-type]
        )
    if provider == "openai":
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            model=settings.openai_writer_model,
            api_key=settings.openai_api_key,  # type: ignore[arg-type]
        )
    if provider == "ollama":
        from langchain_ollama import ChatOllama
        return ChatOllama(
            model=settings.ollama_writer_model,
            base_url=settings.ollama_base_url,
        )
    raise ValueError(f"Unknown LLM provider: {provider!r}. Choose 'anthropic', 'openai', or 'ollama'.")


def get_router_llm() -> BaseChatModel:
    """Returns the cheap routing LLM based on the configured provider."""
    provider = settings.llm_provider
    if provider == "anthropic":
        from langchain_anthropic import ChatAnthropic
        return ChatAnthropic(
            model=settings.router_model,
            api_key=settings.anthropic_api_key,  # type: ignore[arg-type]
        )
    if provider == "openai":
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            model=settings.openai_router_model,
            api_key=settings.openai_api_key,  # type: ignore[arg-type]
        )
    if provider == "ollama":
        from langchain_ollama import ChatOllama
        return ChatOllama(
            model=settings.ollama_router_model,
            base_url=settings.ollama_base_url,
        )
    raise ValueError(f"Unknown LLM provider: {provider!r}. Choose 'anthropic', 'openai', or 'ollama'.")
