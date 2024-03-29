

def write_eligble(path, key):
    with open(path, 'a') as f:
        f.write(f'{key.hex()}\n')