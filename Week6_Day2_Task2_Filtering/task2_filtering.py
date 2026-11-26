from qdrant_client import QdrantClient, models
from sentence_transformers import SentenceTransformer
from documents import DOCUMENTS

COLLECTION = "week6_day2_management"
client = QdrantClient(url="http://localhost:6333")
model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

if client.collection_exists(COLLECTION):
    client.delete_collection(COLLECTION)
client.create_collection(
    collection_name=COLLECTION,
    vectors_config=models.VectorParams(size=384, distance=models.Distance.COSINE),
)

texts = [text for text, _, _ in DOCUMENTS]
vectors = model.encode(texts, normalize_embeddings=True).tolist()
points = [
    models.PointStruct(
        id=i + 1, vector=vectors[i],
        payload={"text": text, "source": "company_handbook.pdf",
                 "page": page, "category": category}
    )
    for i, (text, category, page) in enumerate(DOCUMENTS)
]
client.upsert(COLLECTION, points=points, wait=True)
before = client.count(COLLECTION, exact=True).count
print(f"Points before re-upsert: {before}")

client.create_payload_index(
    collection_name=COLLECTION, field_name="category",
    field_schema=models.PayloadSchemaType.KEYWORD, wait=True
)

query_vector = model.encode(
    "employee orientation leave policy performance review grievance",
    normalize_embeddings=True
).tolist()
hr_page_filter = models.Filter(
    must=[
        models.FieldCondition(key="category", match=models.MatchValue(value="HR")),
        models.FieldCondition(key="page", range=models.Range(gte=3)),
    ]
)
hits = client.query_points(
    collection_name=COLLECTION, query=query_vector, query_filter=hr_page_filter,
    limit=10, with_payload=True
).points
print(f"Filtered search (category=HR): {len(hits)} results")
for hit in hits:
    print(f"id={hit.id} score={hit.score:.4f} payload={hit.payload}")

changed = []
for i, p in enumerate(points):
    new_text = p.payload["text"] + " (revised handbook text)"
    changed.append(models.PointStruct(
        id=p.id, vector=model.encode(new_text, normalize_embeddings=True).tolist(),
        payload={**p.payload, "text": new_text}
    ))
client.upsert(COLLECTION, points=changed, wait=True)
after = client.count(COLLECTION, exact=True).count
print(f"Points after re-upsert: {after}")
assert before == 30 and after == 30, "Upsert should update existing IDs, not add points."

client.delete(
    collection_name=COLLECTION,
    points_selector=models.FilterSelector(
        filter=models.Filter(must=[
            models.FieldCondition(key="category",
                                  match=models.MatchValue(value="Marketing"))
        ])
    ),
    wait=True,
)
remaining = client.count(COLLECTION, exact=True).count
print("Points after deleting category=Marketing:", remaining)
assert remaining == 28
