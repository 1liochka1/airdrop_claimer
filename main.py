import asyncio
import sys
from typing import Type

import questionary
from questionary import Choice
from loguru import logger

from config import claim_chain_polyhedra
from projects import (
    Polyhedra, Memeland
)
from core.other_info import get_batches
from core.info import BaseProject


class Projects:
    poly = Polyhedra
    meme = Memeland

async def main(project: Type[BaseProject], module):

    match project:
        case Projects.poly:
            token = 'zk'
            chain = claim_chain_polyhedra
        case Projects.meme:
            token = 'meme'
            chain = 'eth'
        case _:
            token = ''
            chain = ''

    total_amount = 0
    for batch in get_batches():
        tasks = []
        for key in batch:
            key_data = key.split(';')
            address_to_send = key_data[2] if key_data[2] != '' else ''
            proxy = key_data[3] if key_data[3] != '' else ''
            worker: BaseProject = project.__call__(key=key_data[1], id=key_data[0], address_to=address_to_send, proxy=proxy, chain=chain)
            match module:
                case 'claim':
                    tasks.append(worker.claim())
                case 'transfer':
                    tasks.append(worker.transfer())
                case _:
                    tasks.append(worker.get_claimable_amount())

        reses = await asyncio.gather(*tasks)
        if module == 'check':
            for res in reses: total_amount += res

    if module == 'check':
        logger.success(f'ЭЛИДБЖЛ {total_amount} {token}, записал элиджбл кошельки в wallets_data')


if __name__ == '__main__':
    print(f'\n{" " * 32}автор - https://t.me/iliocka{" " * 32}\n')
    print(f'\n{" " * 32}donate - EVM 0xFD6594D11b13C6b1756E328cc13aC26742dBa868{" " * 32}\n')
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    while True:
        project = questionary.select(
            "Выберите проект для работы...",
            choices=[
                Choice(" 1) POLYHEDRA🐸", Projects.poly),
                Choice(" 2) MEMELAND🥩", Projects.meme),
                Choice(" 3) ВЫХОД", 'exit'),
            ],
            qmark="",
            pointer="⟹",
        ).ask()
        if project == 'exit':
            loop.close()
            sys.exit()

        module = questionary.select(
            "Выберите модуль для работы...",
            choices=[
                Choice(" 1) Клейм", 'claim'),
                Choice(" 2) Трансфер", 'transfer'),
                Choice(" 3) Чекер", 'check'),
                Choice(" 4) ВЫХОД", 'exit'),
            ],
            qmark="",
            pointer="⟹",
        ).ask()
        if module == 'exit':
            loop.close()
            sys.exit()
        loop.run_until_complete(main(project, module))



