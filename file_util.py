
def read_file(file_path: str):
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            yield line.strip()
