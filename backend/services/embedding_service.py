from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

# 🔥 model خفيف وسريع
model = SentenceTransformer("all-MiniLM-L6-v2")


def get_embedding(text: str):
    return model.encode(text)


def find_top_matches(query, courses, threshold=0.5):
    results = []

    query_vec = get_embedding(query)

    for c in courses:
        course_vec = get_embedding(c.name)

        score = cosine_similarity(
            [query_vec],
            [course_vec]
        )[0][0]

        if score > threshold:
            results.append((c, score))

    # ترتيب
    results = sorted(results, key=lambda x: x[1], reverse=True)

    return results