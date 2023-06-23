from elasticsearch import Elasticsearch

# Koneksi ke Elasticsearch
es = Elasticsearch(['http://localhost:9200'])

# Query pencarian
search_query = {
    "query": {
        "match": {
            "title": {
                "query": "article",
                "operator": "and"
            }
        }
    },
    "size": 10000
}

for i in range(100):
    # Mengeksekusi pencarian
    search_results = es.search(index='my_index3', body=search_query, profile=True)

    # Menampilkan hasil pencarian
    for hit in search_results['hits']['hits']:
        print(f"Title: {hit['_source']['title']}, Description: {hit['_source']['description']}, Timestamp: {hit['_source']['timestamp']}")
    print(f"Found {len(search_results['hits']['hits'])} results in {search_results['took']}ms")