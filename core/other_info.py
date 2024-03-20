import os
import pathlib
import random
from loguru import logger
from config import shuffle_keys, amount_wallets_in_batch


def get_path(file, folder=''):
    BASE_DIR = pathlib.Path(__file__).resolve().parent.parent
    your_path = os.path.join(BASE_DIR, folder)
    path = os.path.join(your_path, file)
    return path


with open(get_path('keys.txt', 'wallets_data'), "r") as f:
    keys = [row.strip() for row in f]

with open(get_path('proxies.txt', 'wallets_data'), "r") as f:
    proxies = [row.strip() for row in f]


def shuffle_wallets(keys_):
    if shuffle_keys:
        random.shuffle(keys_)
    return keys_


def connect_keys():
    key_pairs = []
    shuffle_wallets(keys)
    for n, key in enumerate(keys):
        pair = key.split(';')
        if len(pair) == 2:
            key_pairs.append(f'{n + 1};{pair[0]};{pair[1]}')
        else:
            key_pairs.append(f'{n + 1};{pair[0]};')
    return key_pairs


def get_batches():
    if not keys:
        logger.warning('НЕ ВСТАВЛЕНЫ КЛЮЧИ В КЕЙС.ТХТ')
    keys_info = connect_keys()
    if proxies:
        proxies_ = proxies
        while len(proxies) < len(keys_info):
            for i in range(len(proxies_)):
                proxies.append(proxies_[i])
                if len(proxies) == len(keys_info):
                    break
        keys_ = zip(keys_info, proxies)
        keys_with_proxy = [f'{key};{proxy}' for key, proxy in keys_]
        return [keys_with_proxy[i:i + amount_wallets_in_batch] for i in
                range(0, len(keys_with_proxy), amount_wallets_in_batch)]

    else:
        keys_ = [f'{key};' for key in keys_info]
        return [keys_[i:i + amount_wallets_in_batch] for i in range(0, len(keys_), amount_wallets_in_batch)]
