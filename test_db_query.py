import asyncio
from google.cloud import firestore

async def test_firestore():
    db = firestore.AsyncClient(project="run-run-rest", database="run-run-rest-local-db")
    # fake insert
    doc_ref = db.collection("test_col").document("1")
    await doc_ref.set({"text": "hello", "time": 1})
    doc_ref = db.collection("test_col").document("2")
    await doc_ref.set({"text": "world", "time": 2})

    query = db.collection("test_col").order_by("time", direction=firestore.Query.DESCENDING).limit(1)
    
    # method 1: get()
    docs = await query.get()
    print("get() type:", type(docs))
    for d in docs:
        print(d.to_dict())
        
    # method 2: stream()
    print("stream() type:", type(query.stream()))
    async for d in query.stream():
        print(d.to_dict())

if __name__ == "__main__":
    asyncio.run(test_firestore())
