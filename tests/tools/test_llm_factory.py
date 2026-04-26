"""Tests for LLM factory. Verifies correct LangChain class is returned per provider."""

import pytest
from unittest.mock import patch


def test_get_writer_llm_returns_anthropic(mocker):
    mocker.patch("src.tools.llm_factory.settings.llm_provider", "anthropic")
    from src.tools.llm_factory import get_writer_llm
    from langchain_anthropic import ChatAnthropic

    llm = get_writer_llm()
    assert isinstance(llm, ChatAnthropic)


def test_get_writer_llm_returns_openai(mocker):
    mocker.patch("src.tools.llm_factory.settings.llm_provider", "openai")
    from importlib import reload
    import src.tools.llm_factory as factory_module
    reload(factory_module)

    from langchain_openai import ChatOpenAI
    llm = factory_module.get_writer_llm()
    assert isinstance(llm, ChatOpenAI)


def test_get_router_llm_returns_ollama(mocker):
    mocker.patch("src.tools.llm_factory.settings.llm_provider", "ollama")
    from importlib import reload
    import src.tools.llm_factory as factory_module
    reload(factory_module)

    from langchain_ollama import ChatOllama
    llm = factory_module.get_router_llm()
    assert isinstance(llm, ChatOllama)


def test_unknown_provider_raises_value_error(mocker):
    mocker.patch("src.tools.llm_factory.settings.llm_provider", "unknown_provider")
    from importlib import reload
    import src.tools.llm_factory as factory_module
    reload(factory_module)

    with pytest.raises(ValueError, match="Unknown LLM provider"):
        factory_module.get_writer_llm()
