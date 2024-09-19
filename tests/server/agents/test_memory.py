import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from server.agent import AgentConfig
from server.agents import Memory
from shared.mixins import ResponseMixin


@pytest.fixture
def redis_mock():
    redis = MagicMock()
    # Mock the redis methods used in the Memory class
    redis.lrange = MagicMock()
    redis.lpush = MagicMock()
    redis.set = MagicMock()
    redis.exists = MagicMock()
    redis.delete = MagicMock()
    redis.get = MagicMock()
    redis.type = MagicMock()
    redis.keys = MagicMock()
    return redis


@pytest.fixture
def llm_ctx_mock():
    llm_ctx = MagicMock()
    llm_ctx.intent_llm = MagicMock()
    llm_ctx.intent_llm.ainvoke = AsyncMock()
    return llm_ctx


@pytest.fixture
def agent_config_mock(redis_mock, llm_ctx_mock):
    config = AgentConfig(redis=redis_mock, llm_ctx=llm_ctx_mock)
    return config


@pytest.fixture
def memory_agent(agent_config_mock):
    return Memory(agent_config_mock)


@pytest.mark.asyncio
async def test_store_string(memory_agent, redis_mock):
    key = "test_key"
    memory = "test_memory"
    value_type = "str"

    # Mock ensure_key to return the key as is
    memory_agent.ensure_key = AsyncMock(return_value=key)

    # Mock _store_memory_key_to_memories
    memory_agent._store_memory_key_to_memories = MagicMock()

    await memory_agent.store(key, memory, value_type)

    # Check that redis.set was called with the correct key and memory
    redis_mock.set.assert_called_with(f"memory|{key.lower()}", memory)

    # Check that _store_memory_key_to_memories was called with the key
    memory_agent._store_memory_key_to_memories.assert_called_with(key)


@pytest.mark.asyncio
async def test_store_list(memory_agent, redis_mock):
    key = "test_key"
    memory = ["item1", "item2"]
    value_type = "list"

    # Mock ensure_key to return the key as is
    memory_agent.ensure_key = AsyncMock(return_value=key)

    # Mock existing data in redis.lrange
    existing_data = ["item1"]
    redis_mock.lrange.return_value = existing_data

    # Mock _store_memory_key_to_memories
    memory_agent._store_memory_key_to_memories = MagicMock()

    await memory_agent.store(key, memory, value_type)

    # Check that redis.lrange was called
    redis_mock.lrange.assert_called_with(name=key, start=0, end=-1)

    # Check that redis.lpush was called for 'item2' only
    redis_mock.lpush.assert_called_once_with(key, "item2")

    # Check that _store_memory_key_to_memories was called with the key
    memory_agent._store_memory_key_to_memories.assert_called_with(key)


@pytest.mark.asyncio
async def test_store_list_invalid_memory(memory_agent, redis_mock):
    key = "test_key"
    memory = "not_a_list"
    value_type = "list"

    # Mock ensure_key to return the key as is
    memory_agent.ensure_key = AsyncMock(return_value=key)

    response = await memory_agent.store(key, memory, value_type)

    # Check that redis methods were not called
    redis_mock.lrange.assert_not_called()
    redis_mock.lpush.assert_not_called()

    # Check that the response indicates failure
    assert isinstance(response, ResponseMixin)
    assert response.retry is True
    assert "Could not convert memory to the type specified" in response.response


def test_forget(memory_agent, redis_mock):
    key = "test_key"

    # Mock redis.delete to return 1 (number of keys deleted)
    redis_mock.delete.return_value = 1

    response = memory_agent.forget(key)

    # Check that redis.delete was called with the key
    redis_mock.delete.assert_called_with(key)

    # Check that response indicates success
    assert response.completed is True
    assert response.response is True


@pytest.mark.asyncio
async def test_ensure_key_exists(memory_agent, redis_mock):
    potential_key = "existing_key"

    # Mock redis.exists to return True
    redis_mock.exists.return_value = True

    # Mock _to_memory_key
    memory_agent._to_memory_key = MagicMock(return_value=f"memory|{potential_key}")

    key = await memory_agent.ensure_key(potential_key)

    # Check that redis.exists was called with the key
    redis_mock.exists.assert_called_with(f"memory|{potential_key}")

    # Check that the returned key is as expected
    assert key == f"memory|{potential_key}"


@pytest.mark.asyncio
async def test_ensure_key_not_exists(memory_agent, redis_mock):
    potential_key = "non_existing_key"
    similar_key = "similar_key"

    # Mock redis.exists to return False
    redis_mock.exists.return_value = False

    # Mock _to_memory_key
    memory_agent._to_memory_key = MagicMock(side_effect=lambda k: f"memory|{k}")

    # Mock _determine_key_via_llm to return a similar key
    memory_agent._determine_key_via_llm = AsyncMock(return_value=similar_key)

    key = await memory_agent.ensure_key(potential_key)

    # Check that redis.exists was called with the potential key
    redis_mock.exists.assert_called_with(f"memory|{potential_key}")

    # Check that _determine_key_via_llm was called
    memory_agent._determine_key_via_llm.assert_called_with(potential_key)

    # Check that the returned key is the similar key converted to memory key
    assert key == f"memory|{similar_key}"


@pytest.mark.asyncio
async def test_determine_key_via_llm_found(memory_agent, redis_mock):
    non_key = 'non_key'
    like_keys = ['key1', 'key2', 'key3']
    llm_result = 'key2'

    # Mock redis.keys to return a list of keys
    redis_mock.keys.return_value = [f"memory|{key}" for key in like_keys]

    # Create a mock response object with a 'content' attribute
    class MockResponse:
        def __init__(self, content):
            self.content = content

    # Mock the chain and its invoke method
    with patch('config.prompts.DETERMINE_SIMILAR_KEY') as mock_prompt:
        chain = MagicMock()
        chain.ainvoke = AsyncMock(return_value=MockResponse(llm_result))

        # Mock the chain building
        # DETERMINE_SIMILAR_KEY | self.llm_ctx.intent_llm returns chain
        mock_prompt.__or__.return_value = chain
        # self.llm_ctx.intent_llm | text returns chain
        memory_agent.llm_ctx.intent_llm = MagicMock()
        memory_agent.llm_ctx.intent_llm.__or__.return_value = chain
        # chain | text returns chain
        chain.__or__.return_value = chain

        result = await memory_agent._determine_key_via_llm(non_key)

        # Check that redis.keys was called
        redis_mock.keys.assert_called_with("memory|*")

        # Check that the result is the llm_result
        assert result == llm_result


@pytest.mark.asyncio
async def test_determine_key_via_llm_none(memory_agent, redis_mock):
    non_key = "non_key"
    like_keys = ["key1", "key2", "key3"]
    llm_result = "none"

    # Mock redis.keys to return a list of keys
    redis_mock.keys.return_value = [f"memory|{key}" for key in like_keys]

    with patch("config.prompts.DETERMINE_SIMILAR_KEY") as mock_determine_similar_key:
        chain = MagicMock()
        chain.ainvoke = AsyncMock(return_value={"content": llm_result})
        mock_determine_similar_key.__or__.return_value = chain

        result = await memory_agent._determine_key_via_llm(non_key)

        # Check that redis.keys was called
        redis_mock.keys.assert_called_with("memory|*")

        # Check that the result is the original non_key
        assert result == non_key


@pytest.mark.asyncio
async def test_retrieve_string(memory_agent, redis_mock):
    key = "test_key"
    stored_key = "memory|test_key"
    value = "test_value"

    # Mock ensure_key to return the stored_key
    memory_agent.ensure_key = AsyncMock(return_value=stored_key)

    # Mock redis.type to return 'string'
    redis_mock.type.return_value = "string"

    # Mock redis.get to return the value
    redis_mock.get.return_value = value

    response = await memory_agent.retrieve(key)

    # Check that ensure_key was called
    memory_agent.ensure_key.assert_called_with(key)

    # Check that redis.type was called with stored_key
    redis_mock.type.assert_called_with(stored_key)

    # Check that redis.get was called with stored_key
    redis_mock.get.assert_called_with(stored_key)

    # Check the response
    assert isinstance(response, ResponseMixin)
    assert response.completed is True
    assert response.response == value


@pytest.mark.asyncio
async def test_retrieve_list(memory_agent, redis_mock):
    key = "test_key"
    stored_key = "memory|test_key"
    value = ["item1", "item2", "item3"]
    qty = 2

    # Mock ensure_key to return the stored_key
    memory_agent.ensure_key = AsyncMock(return_value=stored_key)

    # Mock redis.type to return 'list'
    redis_mock.type.return_value = "list"

    # Mock redis.lrange to return the value
    redis_mock.lrange.return_value = value[:qty]

    response = await memory_agent.retrieve(key, qty=qty)

    # Check that ensure_key was called
    memory_agent.ensure_key.assert_called_with(key)

    # Check that redis.type was called with stored_key
    redis_mock.type.assert_called_with(stored_key)

    # Check that redis.lrange was called with stored_key, 0, qty
    redis_mock.lrange.assert_called_with(stored_key, 0, qty)

    # Check the response
    assert isinstance(response, ResponseMixin)
    assert response.completed is True
    assert response.response == value[:qty]


@pytest.mark.asyncio
async def test_understand_agent(memory_agent):
    # Mock _capture_functions
    memory_agent._capture_functions = MagicMock(return_value="list_of_methods")

    response = await memory_agent.understand_agent()

    # Check that _capture_functions was called
    memory_agent._capture_functions.assert_called_once()

    # Check the response
    assert isinstance(response, ResponseMixin)
    assert response.response == f"{Memory.__doc__} | Methods: list_of_methods"
