import asyncio
import json as js
import random
import time

import aiohttp
from eth_utils import to_hex
from loguru import logger
from web3 import AsyncWeb3, Web3
from web3.contract import AsyncContract
from web3.eth import AsyncEth

from config import (
    rpcs, gwei, delay, custom_bsc_gwei
)
from core.info import token_abi, scans


class Account:
    def __init__(self, key, *, id: str = '1', address_to=None, proxy=None, chain='eth'):
        self.proxy = f'http://{proxy}' if proxy else None
        self.w3 = AsyncWeb3(AsyncWeb3.AsyncHTTPProvider(
            rpcs[chain], request_kwargs={"proxy": self.proxy}), modules={'eth': (AsyncEth,)}, middlewares=[])
        self.chain = chain
        self.account = self.w3.eth.account.from_key(key)
        self.address = self.account.address
        self.address_to = address_to
        self.acc_info = f'{id}) {self.address}:{self.chain}'

    def get_contract(self, address, abi) -> AsyncContract:
        return self.w3.eth.contract(address=Web3.to_checksum_address(address), abi=abi)

    @staticmethod
    async def sleep_indicator(info):
        secs = random.uniform(*delay)
        logger.info(f'{info} - жду {secs} секунд')
        await asyncio.sleep(secs)

    async def check_status_tx(self, tx_hash):
        logger.info(f'{self.acc_info} - жду подтверждения транзакции')
        start_time = int(time.time())
        while True:
            current_time = int(time.time())
            if current_time >= start_time + 100:
                logger.debug(
                    f'{self.acc_info} - транзакция не подтвердилась за 100 cекунд, начинаю повторную отправку')
                return 0
            try:
                status = (await self.w3.eth.get_transaction_receipt(tx_hash))['status']
                return status
            except Exception as error:
                await asyncio.sleep(1)

    async def get_nonce(self):
        try:
            return self.w3.eth.get_transaction_count(self.address)
        except Exception as e:
            logger.error(f'{self.acc_info} -{e}')
            return await self.get_nonce()

    async def sign_and_send(self, tx):
        try:
            sign = self.account.sign_transaction(tx)
            hash_ = await self.w3.eth.send_raw_transaction(sign.rawTransaction)
            status = await self.check_status_tx(hash_)
            return status, hash_
        except Exception as e:
            logger.error(f'{self.acc_info} - ошибка при отправке транзакции : \n{e}')
            return

    async def build_tx(self, contract, func=None, value=0, args=None):
        await self.check_gas()
        try:
            nonce = await self.get_nonce()
            func_ = getattr(contract.functions, func)
            tx_dict = {
                'from': self.address,
                'nonce': nonce,
                'value': value,
                'maxFeePerGas': 0,
                'maxPriorityFeePerGas': 0
            }
            if args is None:
                tx = await func_().build_transaction(tx_dict)
            elif type(args) != list and type(args) != str:
                tx = await func_(*args).build_transaction(tx_dict)
            else:
                tx = await func_(args).build_transaction(tx_dict)
            gas = await self.w3.eth.gas_price
            if self.chain != 'bsc':
                gas = int(gas * 1.1)
                tx['maxPriorityFeePerGas'] = gas
                tx['maxFeePerGas'] = gas
            else:
                del tx['maxPriorityFeePerGas']
                del tx['maxFeePerGas']
                tx['gasPrice'] = gas if not custom_bsc_gwei else custom_bsc_gwei
            tx['gas'] = await self.w3.eth.estimate_gas(tx)
            return tx
        except Exception as e:
            logger.error(f'{self.acc_info} - {e}')
            return False

    async def build_tx_with_data(self, contract_address, *, value=0, data='0x'):
        await self.check_gas()
        try:
            tx = {
                'from': self.address,
                'to': Web3.to_checksum_address(contract_address),
                'nonce': await self.get_nonce(),
                'value': value,
                'data': data,
                'chainId': await self.w3.eth.chain_id,
                'maxFeePerGas': 0,
                'maxPriorityFeePerGas': 0
            }
            gas = await self.w3.eth.gas_price
            if self.chain != 'bsc':
                gas = int(gas * 1.1)
                tx['maxPriorityFeePerGas'] = gas
                tx['maxFeePerGas'] = gas
            else:
                del tx['maxPriorityFeePerGas']
                del tx['maxFeePerGas']
                tx['gasPrice'] = gas if not custom_bsc_gwei else custom_bsc_gwei
            tx['gas'] = await self.w3.eth.estimate_gas(tx)
            return tx
        except Exception as e:
            logger.error(f'{self.acc_info} - {e}')
            return False

    async def check_gas(self):
        if self.chain != 'bsc':
            while True:
                try:
                    gas = await self.w3.eth.gas_price
                    gas_ = self.w3.from_wei(gas, 'gwei')
                    logger.success(f'{self.acc_info} - gwei сейчас - {gas_}')
                    if gwei > gas_:
                        return True
                    logger.error(f'{self.acc_info} gwei слишком большой, жду понижения')
                    await asyncio.sleep(30)
                except Exception as e:
                    logger.error(f'{self.acc_info} - {e}')
                    await asyncio.sleep(1)
                    return await self.check_gas()

    async def get_balance(self, address_contract):
        contract = self.get_contract(address=Web3.to_checksum_address(address_contract), abi=token_abi)
        try:
            balance = await contract.functions.balanceOf(self.address).call()
            decimals = await contract.functions.decimals().call()
            return balance, balance / 10 ** decimals
        except Exception as e:
            logger.error(f'{self.acc_info} - {e}')
            await asyncio.sleep(1)
            return await self.get_balance(address_contract)

    async def transfer_token(self, token_address, token_name):
        if not self.address_to:
            logger.error(f'{self.acc_info} - не указан адрес для отправки')
            return

        balance, formatted_balance = await self.get_balance(token_address)
        if balance == 0:
            logger.error(f'{self.acc_info} - нечего отправлять')
            return
        try:
            tx = await self.build_tx_with_data(contract_address=token_address, value=0,
                                               data=self.get_contract(token_address, abi=token_abi).encodeABI(
                                                   'transfer',
                                                   [Web3.to_checksum_address(self.address_to), balance]))
            data = await self.sign_and_send(tx)
            if not data: return
            status, hash_ = data
            if status:
                logger.success(
                    f'{self.acc_info} - успешно отправил {formatted_balance} {token_name}\ntx: {scans[self.chain]}{to_hex(hash_)}')
                await self.sleep_indicator(f'{self.acc_info}')
                return True
            else:
                logger.error(f'{self.acc_info} - транзакция не успешна')
                return False
        except Exception as e:
            logger.error(f'{self.acc_info} - {e}')
            return

    async def send_request(self, url, method, *, params=None, json=None, headers=None):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.request(method, url, headers=headers, params=params, json=json,
                                           proxy=self.proxy) as response:
                    if response.status in [200, 201]:
                        return js.loads(await response.text())
                    await asyncio.sleep(1)
                    logger.error(f'Ошибка при отправке запроса {url}: {await response.text()}')
                    return
        except Exception as e:
            logger.error(f'Ошибка - {e}')
            return
