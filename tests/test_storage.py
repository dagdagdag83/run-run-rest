import pytest
from storage import Storage, InMemoryStorage

@pytest.fixture
def storage():
    return InMemoryStorage()

@pytest.mark.asyncio
async def test_get_nonexistent_returns_none(storage: Storage):
    result = await storage.get("users", "user1")
    assert result is None

@pytest.mark.asyncio
async def test_put_and_get(storage: Storage):
    data = {"name": "Test User"}
    await storage.put("users", "user1", data)
    
    result = await storage.get("users", "user1")
    assert result == data
    
    # Ensure distinct objects (good practice in memory mocks)
    assert result is not data

@pytest.mark.asyncio
async def test_delete(storage: Storage):
    data = {"name": "Test User"}
    await storage.put("users", "user1", data)
    await storage.delete("users", "user1")
    
    result = await storage.get("users", "user1")
    assert result is None

@pytest.mark.asyncio
async def test_delete_nonexistent(storage: Storage):
    # Should not raise
    await storage.delete("users", "nonexistent")
    assert True

@pytest.mark.asyncio
async def test_put_merge(storage: Storage):
    # Initial put
    await storage.put("users", "user1", {"name": "Test User", "selected_persona": "Sarcastic Coach"})
    
    # Merge put
    await storage.put("users", "user1", {"name": "Updated Name", "new_field": True}, merge=True)
    
    result = await storage.get("users", "user1")
    assert result == {
        "name": "Updated Name",
        "selected_persona": "Sarcastic Coach",
        "new_field": True
    }

@pytest.mark.asyncio
async def test_put_no_merge(storage: Storage):
    # Initial put
    await storage.put("users", "user1", {"name": "Test User", "selected_persona": "Sarcastic Coach"})
    
    # Non-merge put
    await storage.put("users", "user1", {"name": "Updated Name", "new_field": True})
    
    result = await storage.get("users", "user1")
    assert result == {
        "name": "Updated Name",
        "new_field": True
    }
