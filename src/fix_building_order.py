#! /usr/bin/env python

import argparse
import itertools
import io
from pathlib import Path
from collections import defaultdict

import stellaris
from stellaris.ast import *


@stellaris.mod('improved_planet_automation')
def build(args=None):
    #args = parser.parse_args(args)

    buildings = Exps()

    building_files = [
        '00_capital_buildings.txt',
        '00_example.txt',
        '01_pop_assembly_buildings.txt',
        '02_government_buildings.txt',
        '03_resource_buildings.txt',
        '04_manufacturing_buildings.txt',
        '05_research_buildings.txt',
        '06_trade_buildings.txt',
        '07_amenity_buildings.txt',
        '08_unity_buildings.txt',
        '09_army_buildings.txt',
        '10_deposit_buildings.txt',
        #'11_primitive_buildings.txt',
        '12_event_buildings.txt',
        #'13_fallen_empire_buildings.txt',
        #'14_branch_office_buildings.txt',
        #'15_overlord_holdings.txt',
    ]

    exclude = {
        # special
        'building_resource_silo',
        'building_order_keep',
        'building_nanite_transmuter',
        'building_bio_reactor',
        'building_ranger_lodge',

        # don't build but should upgrade?
        'building_coordinated_fulfillment_center_1',
        'building_gaiaseeders_1',
        'building_necrophage_elevation_chamber',

        # events
        'building_composer_sanctum',
        'building_eater_sanctum',
        'building_instrument_sanctum',
        'building_whisperers_sanctum',
        'building_artist_patron',
        'building_akx_worm_3',

        # housing
        'building_hive_warren',
        'building_drone_storage',
        'building_communal_housing',
        'building_luxury_residence',

        # useless
        'building_xeno_zoo',
    }

    for p in building_files:
        for exp in stellaris.load(f'common/buildings/{p}'):
            match exp:
                case Statement(Label(l), _, b):
                    if l in exclude:
                        continue

                    if 'owner' != b.get('owner_type', default='owner'):
                        continue

                    if 'yes' != b.get('can_build', default='yes'):
                        continue

                    buildings.append(exp)

    for exp in buildings:
        match exp:
            case Statement(Label(l), _, b):
                #print(exp.pretty())

                #print('...')

                exp.right.append(Statement(Label('position_priority'), '=', Int(10)))

                #print(exp.pretty())

                return


if __name__ == '__main__':
    stellaris.build_mods()
