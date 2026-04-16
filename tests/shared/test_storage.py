import pytest
from src.shared.storage import Storage, InMemoryStorage

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
    await storage.put("users", "user1", {"name": "Test User", "selected_persona": "supportive-realist"})
    
    # Merge put
    await storage.put("users", "user1", {"name": "Updated Name", "new_field": True}, merge=True)
    
    result = await storage.get("users", "user1")
    assert result == {
        "name": "Updated Name",
        "selected_persona": "supportive-realist",
        "new_field": True
    }

@pytest.mark.asyncio
async def test_put_no_merge(storage: Storage):
    # Initial put
    await storage.put("users", "user1", {"name": "Test User", "selected_persona": "supportive-realist"})
    
    # Non-merge put
    await storage.put("users", "user1", {"name": "Updated Name", "new_field": True})
    
    result = await storage.get("users", "user1")
    assert result == {
        "name": "Updated Name",
        "new_field": True
    }

@pytest.mark.asyncio
async def test_list_and_cap(storage: Storage):
    await storage.put("col", "1", {"time": 1, "data": "a"})
    await storage.put("col", "2", {"time": 2, "data": "b"})
    await storage.put("col", "3", {"time": 3, "data": "c"})
    
    # Test sort descending
    res = await storage.list("col", order_by="time", descending=True)
    assert len(res) == 3
    assert res[0]["data"] == "c"
    assert res[2]["data"] == "a"
    
    # Test limit
    res_limit = await storage.list("col", limit=1, order_by="time", descending=True)
    assert len(res_limit) == 1
    assert res_limit[0]["data"] == "c"
