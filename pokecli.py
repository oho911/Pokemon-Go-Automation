#!/usr/bin/env python
"""
pgoapi - Pokemon Go API
Copyright (c) 2016 tjado <https://github.com/tejado>

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE
OR OTHER DEALINGS IN THE SOFTWARE.

Author: tjado <https://github.com/tejado>
"""

import os
import re
import json
import struct
import logging
import requests
import argparse
import working
import time
import datetime
import ssl
import pokemon

ssl._create_default_https_context = ssl._create_unverified_context

from pgoapi import PGoApi
from pgoapi.utilities import f2i, h2f

from google.protobuf.internal import encoder
from geopy.geocoders import GoogleV3
from s2sphere import CellId, LatLng

log = logging.getLogger(__name__)

pokemon.list()

global config

# Initialise PGOAPI
pgoapi = PGoApi()

def init_config():
    parser = argparse.ArgumentParser()
    config_file = "config.json"

    # If config file exists, load variables from json
    load   = {}
    if os.path.isfile(config_file):
        with open(config_file) as data:
            load.update(json.load(data))

    # Read passed in Arguments
    required = lambda x: not x in load
    parser.add_argument("-a", "--auth_service", help="Auth Service ('ptc' or 'google')",
        required=required("auth_service"))
    parser.add_argument("-u", "--username", help="Username", required=required("username"))
    parser.add_argument("-p", "--password", help="Password", required=required("password"))
    parser.add_argument("-l", "--location", help="Location", required=required("location"))
    parser.add_argument("-s", "--spinstop", help="SpinPokeStop",action='store_true')
    parser.add_argument("-c", "--cp",help="Set CP less than to transfer(DEFAULT 100)",type=int,default=100)
    parser.add_argument("-d", "--dev", help="Dev Mode", action='store_true')
    parser.add_argument("-t", "--test", help="Only parse the specified location", action='store_true')
    parser.set_defaults(DEV=False, TEST=False)
    config = parser.parse_args()

    # Passed in arguments shoud trump
    for key in config.__dict__:
        if key in load and config.__dict__[key] == None:
            config.__dict__[key] = load[key]

    if config.auth_service not in ['ptc', 'google']:
      log.error("Invalid Auth service specified! ('ptc' or 'google')")
      return None

    return config
def get_position(locationName):
    locate = GoogleV3()

    location = locate.geocode(locationName)

    print('[#]')
    print('[x] Address found: ' + location.address.encode('utf-8'))

    with open('location.json', 'w') as outfile:
        json.dump({"lat": location.latitude, "lon": location.longitude, "alt": location.altitude}, outfile)

    return (location.latitude, location.longitude, location.altitude)

def main():
    print('[x] Initializing PokemonGO Automation v0.1')
    time.sleep(1)
    print('[x] PokemonGo Automation [@eggins | /r/pokemongodev | darroneggins.com]')


    config = init_config()
    if not config:
        return

    print('[x] Configuration Initialized')

    # Start organising positioning
    position = get_position(config.location)
    # Check if test mode
    if config.test:
        return

    # Set player position in-game
    pgoapi.set_position(*position)
    print('[x] Position in-game set as: ' + str(position))
    if not config.dev:
        time.sleep(1)

    # Attempt login
    if not pgoapi.login(config.auth_service, config.username, config.password):
        return

    # Get Player Details
    pgoapi.get_player()
    response = pgoapi.call()
    # Print out account current statistics
    player = response['responses']['GET_PLAYER']['profile']

    ### @@@ TODO: Convert this to d/m/Y H:M:S
    creation_date = datetime.datetime.fromtimestamp(player['creation_time'] / 1e3)
    
    pokecoins='0'
    stardust='0'
    if 'amount' in player['currency'][0]:
        pokecoins=player['currency'][0]['amount']
    if 'amount' in player['currency'][1]:
        stardust=player['currency'][1]['amount']

    with open('player.json', 'w') as outfile:
        json.dump(player, outfile)

    print('[#]')
    print('[#] Username: ' + str(player['username']))
    print('[#] Acccount Creation: ' + str(creation_date))
    print('[#] Bag Storage: ' + str(working.getInventoryCount(pgoapi, 'item')) + '/' + str(player['item_storage']))
    print('[#] Pokemon Storage: ' + str(working.getInventoryCount(pgoapi, 'pokemon')) + '/' + str(player['poke_storage']))
    print('[#] Stardust: ' + str(stardust))
    print('[#] Pokecoins: ' + str(pokecoins))
    print('[#]')

    print('[#]')


    print('[#] Initalizing automation..')
    if not config.dev:
        time.sleep(1)

    working.transferLowLevel(pgoapi, 200)



    # # chain subrequests (methods) into one RPC call

    # # get player profile call
    # # ----------------------
    # api.get_player()

    # response_dict = api.call()
    # print('Response dictionary: \n\r{}'.format(json.dumps(response_dict, indent=2)))

    # #working.transfer_low_cp_pokomon(api,50)

    # pos = 1
    # x = 0
    # y = 0
    # dx = 0
    # dy = -1
    # steplimit=10
    # steplimit2 = steplimit**2
    # origin_lat=position[0]
    # origin_lon=position[1]
    # while(True):
    #     for step in range(steplimit2):
    #         #starting at 0 index
    #         print('looping: step {} of {}'.format((step+1), steplimit**2))
    #         print('steplimit: {} x: {} y: {} pos: {} dx: {} dy {}'.format(steplimit2, x, y, pos, dx, dy))
    #         # Scan location math
    #         if -steplimit2 / 2 < x <= steplimit2 / 2 and -steplimit2 / 2 < y <= steplimit2 / 2:
    #             position=(x * 0.0025 + origin_lat, y * 0.0025 + origin_lon, 0)
    #             api.set_position(*position)
    #             print(position)
    #         if x == y or x < 0 and x == -y or x > 0 and x == 1 - y:
    #             (dx, dy) = (-dy, dx)

    #         (x, y) = (x + dx, y + dy)
    #         # get map objects call
    #         # ----------------------
    #         timestamp = "\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000"
    #         cellid = get_cellid(position[0], position[1])
    #         api.get_map_objects(latitude=f2i(position[0]), longitude=f2i(position[1]), since_timestamp_ms=timestamp, cell_id=cellid)

    #         response_dict = api.call()
    #         #print('Response dictionary: \n\r{}'.format(json.dumps(response_dict, indent=2)))
    #         if response_dict and 'responses' in response_dict and \
    #             'GET_MAP_OBJECTS' in response_dict['responses'] and \
    #             'status' in response_dict['responses']['GET_MAP_OBJECTS'] and \
    #             response_dict['responses']['GET_MAP_OBJECTS']['status'] is 1:

    #             print('got the maps')
    #             map_cells=response_dict['responses']['GET_MAP_OBJECTS']['map_cells']
    #             print('map_cells are {}'.format(len(map_cells)))
    #             for cell in map_cells:
    #                 working.work_on_cell(cell,api,position,config)
    #         time.sleep(10)
    #                     #print(fort)

    # # spin a fort
    # # ----------------------
    # #fortid = '<your fortid>'
    # #lng = <your longitude>
    # #lat = <your latitude>
    # #api.fort_search(fort_id=fortid, fort_latitude=lat, fort_longitude=lng, player_latitude=f2i(position[0]), player_longitude=f2i(position[1]))

    # # release/transfer a pokemon and get candy for it
    # # ----------------------
    # #api.release_pokemon(pokemon_id = <your pokemonid>)

    # # get download settings call
    # # ----------------------
    # #api.download_settings(hash="4a2e9bc330dae60e7b74fc85b98868ab4700802e")

    # # execute the RPC call
    # #response_dict = api.call()
    # #print('Response dictionary: \n\r{}'.format(json.dumps(response_dict, indent=2)))

    # # alternative:
    # # api.get_player().get_inventory().get_map_objects().download_settings(hash="4a2e9bc330dae60e7b74fc85b98868ab4700802e").call()

if __name__ == '__main__':
    main()
