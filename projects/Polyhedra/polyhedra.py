from eth_utils import to_hex

from loguru import logger

from core.info import scans, BaseProject
from core.utils import Account
from projects.Polyhedra.info import (
    claim_address, claim_abi, zk_address
)


class Polyhedra(Account, BaseProject):
    def __init__(self, key, id, address_to=None, proxy=None, chain=None):
        super().__init__(key, id=id, address_to=address_to, proxy=proxy, chain=chain)
        self.contract = self.get_contract(claim_address, claim_abi)

    async def get_proof(self):
        claim_info = {}
        for chain in ['eth', 'bsc']:
            try:
                data = await self.send_request(
                    f'https://pub-88646eee386a4ddb840cfb05e7a8d8a5.r2.dev/{chain}_data/{self.address.lower()[2:5]}.json',
                    'GET')
                if not data:
                    continue

                data = data[self.address]
                claim_info[chain] = [int(data['amount'], 16), int(data['index']), data['proof']]
            except Exception as e:
                continue

        return claim_info

    async def get_claimable_amount(self):
        data = await self.get_proof()
        if not data:
            logger.error(f'{self.acc_info} - не элиджбл для клейма ZK')
            return 0

        for chain in data:
            amount = data[chain][0] / 10 ** 18
            logger.success(f'{self.address}:{chain} - элидбжл {amount} ZK')
            return amount

    async def claim(self):
        data = await self.get_proof()
        if not data:
            return
        if self.chain not in data:
            return

        amount, index, proof = data[self.chain]
        tx = await self.build_tx(self.contract, 'claim', args=(index, self.address, amount, proof))
        if not tx: return
        data = await self.sign_and_send(tx)
        if not data: return
        status, hash_ = data
        if status:
            logger.success(
                f'{self.acc_info} - успешно заклеймил {amount / 10 ** 18} ZK\ntx: {scans[self.chain]}{to_hex(hash_)}')
            await self.sleep_indicator(f'{self.acc_info}:')
            return True
        else:
            logger.error(f'{self.acc_info} - транзакция не успешна...')
            return False

    async def transfer(self):
        return await self.transfer_token(zk_address, 'zk')