db.products.createSearchIndex({
  "name": "vector_index",
  "definition": {
    "mappings": {
      "dynamic": true,
      "fields": [
        {
          "type": "vector",
          "path": "embedding",
          "numDimensions": 128, 
          "similarity": "cosine"
        }
      ]
    },
  }
});