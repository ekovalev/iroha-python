#!/usr/bin/env python3
#
# Copyright Soramitsu Co., Ltd. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
#

import os
import binascii
from iroha import IrohaCrypto
from iroha import Iroha, IrohaGrpc
from iroha.primitive_pb2 import can_set_my_account_detail
import sys

if sys.version_info[0] < 3:
    raise Exception('Python 3 or a more recent version is required.')


IROHA_HOST_ADDR = os.getenv('IROHA_HOST_ADDR', '127.0.0.1')
IROHA_PORT = os.getenv('IROHA_PORT', '50051')
ADMIN_ACCOUNT_ID = os.getenv('ADMIN_ACCOUNT_ID', 'admin@nbc')
ADMIN_PRIVATE_KEY = os.getenv('ADMIN_PRIVATE_KEY', '72a9eb49c0cd469ed64f653e33ffc6dde475a6b9fd8be615086bce7c44b5a8f8')
# ADMIN_PRIVATE_KEY = os.getenv(
#     'ADMIN_PRIVATE_KEY', 'f101537e319568c765b2cc89698325604991dca57b9716b58016b253506cab70')

user_private_key = ADMIN_PRIVATE_KEY
user_public_key = '4a60a53785ab3aeed09fc57c9360c37597ded473efda0826bace79aa08522e48'
# user_private_key = IrohaCrypto.private_key()
# user_public_key = IrohaCrypto.derive_public_key(user_private_key)
iroha = Iroha(ADMIN_ACCOUNT_ID)
net = IrohaGrpc('{}:{}'.format(IROHA_HOST_ADDR, IROHA_PORT))

code = ("608060405234801561001057600080fd5b50610202806100206000396000f3fe60806040"
        "5234801561001057600080fd5b506004361061004c5760003560e01c80631e90718a1461"
        "00515780638909aa3f146100895780638da5cb5b146100cb5780638e7394611461011557"
        "5b600080fd5b6100876004803603604081101561006757600080fd5b8101908080359060"
        "20019092919080359060200190929190505050610157565b005b6100b560048036036020"
        "81101561009f57600080fd5b8101908080359060200190929190505050610173565b6040"
        "518082815260200191505060405180910390f35b6100d361018b565b604051808273ffff"
        "ffffffffffffffffffffffffffffffffffff1673ffffffffffffffffffffffffffffffff"
        "ffffffff16815260200191505060405180910390f35b6101416004803603602081101561"
        "012b57600080fd5b81019080803590602001909291905050506101b0565b604051808281"
        "5260200191505060405180910390f35b8060016000848152602001908152602001600020"
        "819055505050565b60016020528060005260406000206000915090505481565b60008090"
        "54906101000a900473ffffffffffffffffffffffffffffffffffffffff1681565b600060"
        "01600083815260200190815260200160002054905091905056fea265627a7a7230582077"
        "9ec39a199bc65c53dbf9ef4e05a4971d3acea03101e00f52502aa3bcce34a064736f6c63"
        "4300050a0032")

data = ""

caller = 'caller'
callee = 'callee'

def trace(func):
    """
    A decorator for tracing methods' begin/end execution points
    """

    def tracer(*args, **kwargs):
        name = func.__name__
        print('\tEntering "{}"'.format(name))
        result = func(*args, **kwargs)
        print('\tLeaving "{}"'.format(name))
        return result

    return tracer


@trace
def send_transaction_and_print_status(transaction):
    hex_hash = binascii.hexlify(IrohaCrypto.hash(transaction))
    print('Transaction hash = {}, creator = {}'.format(
        hex_hash, transaction.payload.reduced_payload.creator_account_id))
    net.send_tx(transaction)
    for status in net.tx_status_stream(transaction):
        print(status)


@trace
def create_domain_and_asset():
    """
    Creates domain 'domain' and asset 'coin#domain' with precision 2
    """
    commands = [
        iroha.command('CreateDomain', domain_id='bar', default_role='user'),
        iroha.command('CreateAsset', asset_name='foo', domain_id='bar', precision=2)
    ]
    tx = IrohaCrypto.sign_transaction(
        iroha.transaction(commands), ADMIN_PRIVATE_KEY)
    send_transaction_and_print_status(tx)

@trace
def create_domain(domainID):
    """
    Creates domain @domain
    """
    commands = [
        iroha.command('CreateDomain', domain_id=domainID, default_role='user'),
    ]
    tx = IrohaCrypto.sign_transaction(
        iroha.transaction(commands), ADMIN_PRIVATE_KEY)
    send_transaction_and_print_status(tx)

@trace
def create_asset(domainID, asset):
    """
    Creates asset 'coin#domain' with precision 2
    """
    tx = iroha.transaction([
        iroha.command('CreateAsset', asset_name=asset,
                      domain_id=domainID, precision=2)
    ])
    IrohaCrypto.sign_transaction(tx, ADMIN_PRIVATE_KEY)
    send_transaction_and_print_status(tx)

@trace
def add_coin_to_admin(asset_id, amount):
    """
    Add 1000.00 units of 'coin#domain' to 'admin@test'
    """
    tx = iroha.transaction([
        iroha.command('AddAssetQuantity',
                      asset_id=asset_id, amount=amount)
    ])
    IrohaCrypto.sign_transaction(tx, ADMIN_PRIVATE_KEY)
    send_transaction_and_print_status(tx)


@trace
def create_account_userone():
    """
    Create account 'userone@domain'
    """
    tx = iroha.transaction([
        iroha.command('CreateAccount', account_name='userone', domain_id='domain',
                      public_key=user_public_key)
    ])
    IrohaCrypto.sign_transaction(tx, ADMIN_PRIVATE_KEY)
    send_transaction_and_print_status(tx)


@trace
def transfer_coin_from_admin_to_userone():
    """
    Transfer 2.00 'coin#domain' from 'admin@test' to 'userone@domain'
    """
    tx = iroha.transaction([
        iroha.command('TransferAsset', src_account_id='admin@test', dest_account_id='userone@domain',
                      asset_id='coin#domain', description='init top up', amount='2.00')
    ])
    IrohaCrypto.sign_transaction(tx, ADMIN_PRIVATE_KEY)
    send_transaction_and_print_status(tx)

@trace
def transfer_coin_from_admin_to_user(dest_id):
    """
    Transfer 2.00 'usd#nbc' from 'admin@nbc' to '${name}@nbcß'
    """
    tx = iroha.transaction([
        iroha.command('TransferAsset', src_account_id='admin@nbc', dest_account_id=dest_id,
                      asset_id='usd#nbc', description='init top up', amount='2.00')
    ])
    IrohaCrypto.sign_transaction(tx, ADMIN_PRIVATE_KEY)
    send_transaction_and_print_status(tx)

@trace
def userone_grants_to_admin_set_account_detail_permission():
    """
    Make admin@test able to set detail to userone@domain
    """
    tx = iroha.transaction([
        iroha.command('GrantPermission', account_id='admin@test',
                      permission=can_set_my_account_detail)
    ], creator_account='userone@domain')
    IrohaCrypto.sign_transaction(tx, user_private_key)
    send_transaction_and_print_status(tx)


@trace
def set_age_to_userone():
    """
    Set age to userone@domain by admin@test
    """
    tx = iroha.transaction([
        iroha.command('SetAccountDetail',
                      account_id='userone@domain', key='age', value='18')
    ])
    IrohaCrypto.sign_transaction(tx, ADMIN_PRIVATE_KEY)
    send_transaction_and_print_status(tx)

@trace
def set_age_to_user(account_id):
    """
    Set age to userone@domain by admin@test
    """
    tx = iroha.transaction([
        iroha.command('SetAccountDetail',
                      account_id=account_id, key='age', value='18')
    ])
    IrohaCrypto.sign_transaction(tx, ADMIN_PRIVATE_KEY)
    send_transaction_and_print_status(tx)

@trace
def get_coin_info():
    """
    Get asset info for coin#domain
    :return:
    """
    query = iroha.query('GetAssetInfo', asset_id='coin#domain')
    IrohaCrypto.sign_query(query, ADMIN_PRIVATE_KEY)

    response = net.send_query(query)
    data = response.asset_response.asset
    print('Asset id = {}, precision = {}'.format(data.asset_id, data.precision))


@trace
def get_account_assets():
    """
    List all the assets of userone@domain
    """
    query = iroha.query('GetAccountAssets', account_id='userone@domain')
    IrohaCrypto.sign_query(query, ADMIN_PRIVATE_KEY)

    response = net.send_query(query)
    data = response.account_assets_response.account_assets
    for asset in data:
        print('Asset id = {}, balance = {}'.format(
            asset.asset_id, asset.balance))


@trace
def get_userone_details():
    """
    Get all the kv-storage entries for userone@domain
    """
    query = iroha.query('GetAccountDetail', account_id='userone@domain')
    IrohaCrypto.sign_query(query, ADMIN_PRIVATE_KEY)

    response = net.send_query(query)
    data = response.account_detail_response
    print('Account id = {}, details = {}'.format('userone@domain', data.detail))

@trace
def engine_call(caller, callee, code, data):
    """
    Call smart contract in EVM
    """
    tx = iroha.transaction([
        iroha.command('EngineCall',
                      caller=caller, callee=callee, code=code, input=data)
    ])
    IrohaCrypto.sign_transaction(tx, ADMIN_PRIVATE_KEY)
    send_transaction_and_print_status(tx)


# create_domain_and_asset()
# create_domain('cbr')
# create_asset('ecb', 'eur')
# add_coin_to_admin('usd#nbc', '1000')
# create_account_userone()
# transfer_coin_from_admin_to_user('test@nbc')
# userone_grants_to_admin_set_account_detail_permission()
# set_age_to_user('admin@nbc')
# get_coin_info()
# get_account_assets()
# get_userone_details()
engine_call(caller, callee, code, data)

print('done')
