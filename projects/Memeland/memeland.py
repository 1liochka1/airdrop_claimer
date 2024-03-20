from eth_utils import to_hex

from core.info import scans, BaseProject
from core.utils import Account
from projects.Memeland.info import claim_address, claim_abi, meme_address
from loguru import logger


class Memeland(Account, BaseProject):
    def __init__(self, key, id, address_to=None, proxy=None, chain=None):
        super().__init__(key, id=id, address_to=address_to, proxy=proxy, chain=chain)
        self.contract = self.get_contract(claim_address, claim_abi)

    async def get_proof(self):
        headers = {
            'authority': 'memestaking-api.stakeland.com',
            'accept': 'application/json',
            'accept-language': 'ru,en;q=0.9',
            'origin': 'https://www.stakeland.com',
            'sec-ch-ua': '"Not_A Brand";v="8", "Chromium";v="120", "YaBrowser";v="24.1", "Yowser";v="2.5"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-site',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 YaBrowser/24.1.0.0 Safari/537.36',
        }
        try:
            data = await self.send_request(
                f'https://memestaking-api.stakeland.com/wallet/info/{self.address}', 'GET',
                headers=headers)
            if not data:
                return
            if not data['rewards']:
                return
            data = data['rewards'][0]
            return int(data['rewardId']), data['proof'], int(data['amount'])
        except Exception as e:
            logger.error(f'{self.acc_info} - {e}')
            return

    async def get_claimable_amount(self):
        data = await self.get_proof()
        if not data:
            logger.error(f'{self.acc_info} - не элиджбл для клейма MEME')
            return 0
        else:
            amount = data[2] / 10 ** 18
            logger.success(f'{self.address} - элидбжл {amount} MEME')
            return amount

    async def claim(self):
        claim_data = await self.get_proof()
        if not claim_data:
            logger.error(f'{self.acc_info} - не элиджбл для клейма MEME')
            return
        id_, proof, amount = claim_data

        tx = await self.build_tx_with_data(self.contract.address,
                                           data=self.contract.encodeABI('unstake', [amount, [(id_, amount, proof)]]))
        if not tx:
            return
        data = await self.sign_and_send(tx)
        if not data: return
        status, hash_ = data
        if status:
            logger.success(
                f'{self.acc_info} - успешно заклеймил {amount / 10 ** 18} MEME\ntx: {scans[self.chain]}{to_hex(hash_)}')
            await self.sleep_indicator(f'{self.acc_info}:')
            return True
        else:
            logger.error(f'{self.acc_info} - транзакция не успешна...')
            return False

    async def transfer(self):
        return await self.transfer_token(meme_address, 'meme')
