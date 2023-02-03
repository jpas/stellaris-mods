#! /usr/bin/env python

from string import Template

import stellaris
from stellaris.ast import *


def mk_available(trigger):
    if isinstance(trigger, str):
        exps = stellaris.parse(trigger)
    else:
        exps = trigger
    return Statement(Label('available'), '=', exps)

def mk_category(name, available=None):
    exps = []
    if available is not None:
        exps.append(mk_available(available))
    return Statement(Label(f'planet_automation_{name}'), '=', Exps(exps))


# TODO: ping planet when it would want to build important but it cannot due to
#       no available space.

# TODO: check if has_building_construction should be required building emergencies


def maybe_parse(x):
    match x:
        case str():
            return stellaris.parse(x)
        case _:
            return x


def mk_statement(label, value, op='='):
    match value:
        case Node():
            pass
        case _:
            value = Label(value)
    return Statement(Label(label), op, value)


def mk_building_rule(building, available=None):
    b = Exps()
    b.append(mk_statement('building', f'building_{building}'))
    if available is not None:
        b.append(mk_statement('available', maybe_parse(available)))
    return mk_statement('x', b)


def mk_resource_fill(resource, district, available=None, buildings=None):
    es = Exps()
    es.append(mk_statement('category', Quoted(f'planet_automation_{resource}')))

    or_ = mk_statement('or', Exps([
        mk_statement('has_district', f'district_{district}'),
        mk_statement('num_free_districts', Exps([
            mk_statement('type', f'district_{district}'),
            mk_statement('value', Int(0), op='>'),
        ])),
    ]))

    av = Exps([or_])
    if available is not None:
        av.extend(maybe_parse(available))
    es.append(mk_statement('available', av))

    es.append(mk_statement('prio_districts', Exps([Label(f'district_{district}')])))

    if buildings is not None:
        bs = Exps([mk_building_rule(b, a) for b, a in buildings.items()])
        es.append(mk_statement('buildings', bs))

    l = Label(f'automate_resource_fill_{resource}_{district}')
    return Statement(l, '=', es)

def mk_resource_fallback_buildings(resource, buildings):
    es = Exps()
    es.append(mk_statement('category', Quoted(f'planet_automation_{resource}')))

    if buildings is not None:
        bs = Exps([mk_building_rule(b, a) for b, a in buildings.items()])
        es.append(mk_statement('buildings', bs))

    l = Label(f'automate_resource_fill_{resource}_fallback_buildings')
    return Statement(l, '=', es)

# TODO: advanced settings button/ui
# TODO: verbose tooltips
# TODO: jobs available based detection
# TODO: limited jobs
# TODO: non-unique buildings
# TODO: monuments

monuments = [
    'building_autochthon_monument',
    'building_corporate_monument',
    'building_simulation_1',
    'building_sensorium_1',
    'building_galactic_memorial_1',
]

resources = {}

resources['research'] = {
    'districts': {
        'hab_science': None,
        'rw_science': None,
    },
    'buildings': {
        'institute': None,
        'supercomputer': None,
    },
    'fallback_buildings': {
        'research_lab_1': '''
            num_free_districts = { type = district_hab_science value = 0 }
            num_free_districts = { type = district_rw_science value = 0 }
        ''',
    },
}

resources['unity'] = {
    'districts': {
        'arcology_administrative': None,
        'arcology_religious': None,
    },
    'buildings': {
        'autocurating_vault': None,
        'corporate_vault': None,
        'citadel_of_faith': None,
        'alpha_hub': None,
    },
    'fallback_buildings': {
        'building_bureaucratic_1': 'not = { uses_district_set = city_world }',
        # TODO: does the arcology do the same thing?
        # 'building_sacrificial_temple_1': 'not = { uses_district_set = city_world }',
        'building_temple': 'not = { uses_district_set = city_world }',
        'building_uplink_node': None,
        'building_hive_node': None,
    },
}

resources['trade_value'] = {
    'districts': {
        'hab_commercial': None,
        'rw_commercial': None,
        'srw_commercial': None,
    },
    'buildings': {
        'galactic_stock_exchange': None,
    },
    'fallback_buildings': {
        'commercial_zone': '''
            num_free_districts = { type = district_hab_commercial value = 0 }
            num_free_districts = { type = district_rw_commercial value = 0 }
            num_free_districts = { type = district_srw_commercial value = 0 }
        ''',
    },
}

resources['alloys'] = {
    'districts': {
        'industrial': 'not = { has_designation = col_factory }',
        'hab_industrial': 'not = { has_designation = col_habitat_factory }',
        'arcology_arms_industry': None,
        'rw_industrial': None,
    },
    'buildings': {
        'foundry_1': None,
        'ministry_production': None,
        'production_center': None,
        # 'coordinated_fulfillment_center_1': None,
    },
    'fallback_buildings': {}
}

resources['consumer_goods'] = {
    'districts': {
        'industrial': '''
            nor = {
                has_designation = col_foundry
                has_planet_flag = use_srw_commercial_for_consumer_goods
            }
        ''',
        'hab_industrial': 'not = { has_designation = col_habitat_foundry }',
        'arcology_civilian_industry': None,
        'rw_industrial': None,
        'srw_commercial': 'has_planet_flag = use_srw_commercial_for_consumer_goods',
    },
    'buildings': {
        'factory_1': None,
        'ministry_production': None,
        'production_center': None,
        # 'coordinated_fulfillment_center_1': None,
    },
    'fallback_buildings': {}
}

resources['energy'] = {
    'districts': {
        'generator': None,
        'generator_uncapped': None,
        'hab_energy': None,
    },
    'buildings': {
        'energy_grid': None,
        'waste_reprocessing_center': None,
    },
    'fallback_buildings': {}
}

resources['minerals'] = {
    'districts': {
        'mining': None,
        'mining_uncapped': None,
        'hab_mining': None,
    },
    'buildings': {
        'mineral_purification_plant': None,
    },
    'fallback_buildings': {}
}

resources['food'] = {
    'districts': {
        'farming': None,
        'farming_uncapped': None,
        'hab_housing': 'has_designation = col_habitat_farming',
        'rw_farming': None,
    },
    'buildings': {
        'food_processing_facility': None,
    },
    'fallback_buildings': {}
}

localization = {
    # fixes
    'planet_automation_designation_construction:0': '£district£ Designation',
    'planet_automation_rare_resources:0': '£exotic_gases£ £rare_crystals£ £volatile_motes£ Rare Resources',
    'planet_automation_pop_assembly:0': '£mod_planet_pop_assembly_mult£ Pop Assembly',
    'planet_automation_building_slot:0': '£building£ Building Slots',
    'planet_automation_crime:0': '£crime£ [Owner.GetCrimeDeviancy]',

    # new
    'planet_automation_research:0': '£physics£ £society£ £engineering£ Research',
    'planet_automation_unity:0': '£unity£ $unity$',
    'planet_automation_trade_value:0': '£trade_value£ Trade Value',
    'planet_automation_alloys:0': '£alloys£ $alloys$',
    'planet_automation_consumer_goods:0': '£consumer_goods£ $consumer_goods$',
    'planet_automation_energy:0': '£energy£ $energy$',
    'planet_automation_minerals:0': '£minerals£ $minerals$',
    'planet_automation_food:0': '£food£ $food$',
}

@stellaris.mod('improved_planet_automation')
def build(args=None):
    categories = stellaris.touch('common/colony_automation_categories/01_ipa_categories.txt')
    for resource in resources:
        categories.append(mk_statement(f'planet_automation_{resource}', Exps()))

    automations = stellaris.touch('common/colony_automation/01_ipa_automation.txt')
    for resource, db in resources.items():
        for district, available in db['districts'].items():
            if (buildings := db.get('buildings')):
                automations.append(mk_resource_fill(
                    resource,
                    district,
                    available,
                    buildings,
                ))

        if (buildings := db.get('fallback_buildings')):
            automations.append(mk_resource_fallback_buildings(
                resource,
                buildings,
            ))

    emergencies = stellaris.touch('common/colony_automation_emergencies/01_ipa_emergencies.txt')
    emergencies.append(stellaris.parse('''
        automate_clerk_management = {
            category = "planet_automation_trade_value"
            emergency = yes

            job_changes = {
                x = {
                    job = clerk
                    amount = -1
                    available = {
                        OR = {
                            has_available_jobs = clerk
                        }
                    }
                }
                x = {
                    job = clerk
                    amount = 1
                    available = {
                        not = { has_available_jobs = clerk }
                        # to allow for migration
                        num_unemployed > 1
                    }
                }
            }
        }
    '''))

    categories.append(mk_statement('planet_automation_clear_blockers', Exps()))

    for k, s in localization.items():
        args.patcher.localize('ipa', k, s)


if __name__ == '__main__':
    stellaris.build_mods()
