rpcs = {
       'eth': 'https://rpc.ankr.com/eth',
       'bsc': 'https://rpc.ankr.com/bsc'
}
# мешать ли коши
shuffle_keys = True

# количество кошельков в одном потоке, если хотим чтобы шли по порядку оставляем как есть
amount_wallets_in_batch = 1

# гвей ниже которого будет работать скрипт
gwei = 60

# cон после транзакции
delay = [0, 100]

# если нужно клеймить с кастомным гвеем для бск сети (нужна анкр рпц) ставим тут значение
custom_bsc_gwei = False

# -------------POLYHEDRA-------------
# bsc eth
claim_chain_polyhedra = 'bsc'

