from elasticsearch import Elasticsearch
from faker import Faker

# Koneksi ke Elasticsearch
es = Elasticsearch(['http://localhost:9200'])

# Faker instance untuk menghasilkan data acak
fake = Faker()

# Jumlah data yang akan dimasukkan
num_documents = 5000

# Loop untuk memasukkan data acak ke Elasticsearch
for _ in range(num_documents):
    # Generate data acak
    title = fake.sentence()
    description = fake.paragraph()
    timestamp = fake.date_time_this_decade().isoformat()

    # Data yang akan dimasukkan ke Elasticsearch
    data = {
        "title": title,
        "description": description,
        "timestamp": timestamp
    }

    # Memasukkan data ke Elasticsearch
    es.index(index='my_index2', body=data)

print(f"Total {num_documents} documents inserted to Elasticsearch.")
