from elasticsearch import Elasticsearch

# Koneksi ke Elasticsearch
es = Elasticsearch(['http://localhost:9200'])

# Definisikan mapping untuk indeks
index_mapping = {
    "mappings": {
        "properties": {
            "title": {"type": "text"},
            "description": {"type": "text"},
            "timestamp": {"type": "date"}
        }
    }
}

# Buat indeks dengan mapping
es.indices.create(index='my_index2', body=index_mapping)

# Data yang akan dimasukkan ke Elasticsearch
data = [
    {"title": "Article 1", "description": "This is the first article.", "timestamp": "2022-01-01T10:00:00"},
    {"title": "Article 2", "description": "This is the second article.", "timestamp": "2022-01-02T12:00:00"},
    {"title": "Article 3", "description": "This is the third article.", "timestamp": "2022-01-03T15:00:00"}
]

# Memasukkan data ke Elasticsearch
for item in data:
    es.index(index='my_index', body=item)

# Melakukan pencarian
search_query = {
    "query": {
        "match": {
            "description": "article"
        }
    }
}

# Mengeksekusi pencarian
search_results = es.search(index='my_index', body=search_query)

# Menampilkan hasil pencarian
for hit in search_results['hits']['hits']:
    print(f"Title: {hit['_source']['title']}, Description: {hit['_source']['description']}, Timestamp: {hit['_source']['timestamp']}")
