
import asyncio
import sys

import questionary
from questionary import Choice
from loguru import logger

from config import claim_chain
from utils import Account


async def main(module):
    with open('keys.txt', "r") as f:
        keys = [row.strip() for row in f]
        if not keys:
            logger.warning('НЕ ВСТАВЛЕНЫ КЛЮЧИ В КЕЙС.ТХТ')

    total_amount = 0
    for id, pair in enumerate(keys):
        key_pair = pair.split(':')
        if len(key_pair) == 2:
            key, address = key_pair
        else:
            key, address = *key_pair, None
        account = Account(key, id=id+1, address_to=address, chain=claim_chain)
        match module:
            case 'claim':
                await account.claim()
            case 'check':
                total_amount+=await account.get_amount()
            case _:
                await account.transfer()

    if module == 'check':
        logger.success(f'ЭЛИДБЖЛ {total_amount} ZK')
        return

if __name__ == '__main__':
    modules = questionary.select(
        "Выберите модули для работы...",
        choices=[
            Choice(" 1) КЛЕЙМ", 'claim'),
            Choice(" 2) ТРАНСФЕР", 't'),
            Choice(" 3) ЧЕКЕР", 'check'),
            Choice(" 4) ВЫХОД", 'e'),
        ],
        qmark="",
        pointer="⟹",
    ).ask()
    if modules == 'e':
        sys.exit()
    asyncio.run(main(modules))
