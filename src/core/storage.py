from typing import Protocol, Any, Dict, Optional, List

class Storage(Protocol):
    async def get(self, collection: str, doc_id: str) -> Optional[Dict[str, Any]]: ...
    async def put(self, collection: str, doc_id: str, data: Dict[str, Any], merge: bool = False) -> None: ...
    async def delete(self, collection: str, doc_id: str) -> None: ...
    async def list(self, collection: str, limit: Optional[int] = None, order_by: Optional[str] = None, descending: bool = False) -> List[Dict[str, Any]]: ...

class InMemoryStorage:
    def __init__(self):
        self._data: Dict[str, Dict[str, Dict[str, Any]]] = {}

    async def get(self, collection: str, doc_id: str) -> Optional[Dict[str, Any]]:
        return self._data.get(collection, {}).get(doc_id)

    async def put(self, collection: str, doc_id: str, data: Dict[str, Any], merge: bool = False) -> None:
        if collection not in self._data:
            self._data[collection] = {}
        # Store a copy of the data to mimic serialization/deserialization behavior of a real DB
        # and prevent accidental state mutation in memory
        if merge and doc_id in self._data[collection]:
            self._data[collection][doc_id].update(data.copy())
        else:
            self._data[collection][doc_id] = data.copy()

    async def delete(self, collection: str, doc_id: str) -> None:
        if collection in self._data and doc_id in self._data[collection]:
            del self._data[collection][doc_id]

    async def list(self, collection: str, limit: Optional[int] = None, order_by: Optional[str] = None, descending: bool = False) -> List[Dict[str, Any]]:
        if collection not in self._data:
            return []
        
        items = list(self._data[collection].values())
        if order_by:
            # We assume order_by field exists and can be compared, or default to None and None sorts cleanly
            items.sort(key=lambda x: str(x.get(order_by, "")), reverse=descending)
        if limit is not None:
            items = items[:limit]
        return [item.copy() for item in items]

class FirestoreStorage:
    def __init__(self, project: str = "run-run-rest", database: str = "run-run-rest-main-db"):
        from google.cloud import firestore
        self._db = firestore.AsyncClient(project=project, database=database)

    async def get(self, collection: str, doc_id: str) -> Optional[Dict[str, Any]]:
        doc_ref = self._db.collection(collection).document(doc_id)
        doc = await doc_ref.get()
        if doc.exists:
            return doc.to_dict()
        return None

    async def put(self, collection: str, doc_id: str, data: Dict[str, Any], merge: bool = False) -> None:
        doc_ref = self._db.collection(collection).document(doc_id)
        await doc_ref.set(data, merge=merge)
        
    async def delete(self, collection: str, doc_id: str) -> None:
        doc_ref = self._db.collection(collection).document(doc_id)
        await doc_ref.delete()

    async def list(self, collection: str, limit: Optional[int] = None, order_by: Optional[str] = None, descending: bool = False) -> List[Dict[str, Any]]:
        from google.cloud import firestore
        query = self._db.collection(collection)
        if order_by:
            direction = firestore.Query.DESCENDING if descending else firestore.Query.ASCENDING
            query = query.order_by(order_by, direction=direction)
        if limit is not None:
            query = query.limit(limit)
            
        docs = await query.get()
        return [doc.to_dict() for doc in docs]
