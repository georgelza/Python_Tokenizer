// A sample query vector, generated from a user's search for "wireless audio device"
const queryVector = [0.11, 0.22, 0.33, ...];

db.products.aggregate([
  {
    "$vectorSearch": {
      "queryVector": queryVector,
      "path": "embedding",
      "numCandidates": 100, // Number of documents to scan
      "limit": 5 // Number of results to return
    }
  },
  {
    "$project": {
      "name": 1,
      "description": 1,
      "_id": 0
    }
  }
]);