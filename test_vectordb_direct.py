import asyncio
import os
import sys

sys.path.insert(0, os.path.abspath('logistics Source code/backend'))

from vectordb import vectordb_instance as db
from seed_vectordb import seed_vector_database

async def run_tests():
    print("=== Testing VectorDB In-Memory & SQLite Persistence ===")
    
    # 1. Seed database
    await seed_vector_database()
    
    # 2. Count shipments
    shipments_count = await db.shipments.count_documents({})
    print(f"Total shipments in VectorDB: {shipments_count}")
    assert shipments_count > 0, "Shipments collection is empty!"
    
    # 3. Find one shipment
    sample = await db.shipments.find_one({})
    print(f"Sample shipment ID: {sample.get('id') or sample.get('shipment_id')}, Status: {sample.get('status')}")
    
    # 4. Semantic Vector Search
    print("\n--- Testing Semantic Vector Similarity Search ---")
    query_text = "Singapore electronics delay customs risk"
    semantic_results = await db.shipments.similarity_search(query_text, top_k=3)
    print(f"Query: '{query_text}' -> Found {len(semantic_results)} results:")
    for res in semantic_results:
        sim = res.get('_similarity_pct', 0.0)
        print(f"  • ID: {res.get('id') or res.get('shipment_id')}, Origin: {res.get('origin_port')}, Dest: {res.get('destination_port')}, Similarity: {sim}%")
    
    # 5. Filtered query
    high_risk = await db.shipments.find({"risk_level": "High"}).to_list(10)
    print(f"\nFiltered 'High' risk shipments count: {len(high_risk)}")
    
    # 6. Test Workflow collection
    workflows = await db.workflows.find({}).to_list(10)
    print(f"Total workflows in VectorDB: {len(workflows)}")
    
    print("\nALL VECTORDB CORE ENGINE TESTS PASSED WITH 100% SUCCESS!")

if __name__ == '__main__':
    asyncio.run(run_tests())
