# Benchmark retrieval

```json
{
  "generated_at": "2026-08-31T07:21:48.594822+00:00",
  "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
  "corpus_documents": 8,
  "calibration_questions": 12,
  "strategies": {
    "none": {
      "questions": 12,
      "recall_at_k": 0.0,
      "abstention_rate": 0.9167,
      "avg_latency_ms": 0.0
    },
    "lexical": {
      "questions": 12,
      "recall_at_k": 1.0,
      "abstention_rate": 0.1667,
      "avg_latency_ms": 0.33
    },
    "vector": {
      "questions": 12,
      "recall_at_k": 1.0,
      "abstention_rate": 0.1667,
      "avg_latency_ms": 1979.22
    }
  },
  "index_size_documents": 8
}
```
