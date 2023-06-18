import time

# Nama file yang akan ditulis
file_path = 'data.txt'

# Fungsi untuk menulis ke file secara terus-menerus
def write_to_file():
    count = 1
    while True:
        data = f'Data {count}\n'
        with open(file_path, 'a') as file:
            file.write(data)
        print(f'Wrote: {data.strip()}')
        count += 1
        time.sleep(1)

# Menjalankan fungsi write_to_file()
write_to_file()
