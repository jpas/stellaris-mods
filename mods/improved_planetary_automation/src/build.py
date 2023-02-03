#! /usr/bin/env python

import dataclasses
from copy import deepcopy
from dataclasses import dataclass, field
from enum import Enum
from functools import partial
from typing import *

import stellaris
from stellaris.ast import *

# TODO: check if has_building_construction should be required building emergencies
# TODO: advanced settings button/ui
# TODO: verbose tooltips
# TODO: deficit only automation for non-rare resources
# TODO: deficit, check if there is a planet already working on it?

# TODO: chamber of elevation?
# TODO: planetary shield generator?
# TODO: military academy?
# TODO: ranger lodge?
# TODO: slave processing facility?

# XXX: puposely omitted:
#      - sanctum of the *
#      - ministry of culture

category_registry = {}
automation_registry = {}
localization = {}

scripted_loc = {}
scripted_values = {}


def maybe_iter(it):
    if it is not None:
        yield from iter(it)


def t_parse(t, **kw):
    if t is None:
        return Exps()

    match t:
        case str():
            return stellaris.parse(t, **kw)
        case Node():
            return t

    raise ValueError(t)


def t_concat(*ts):
    out = Exps()
    for t in ts:
        if t:
            out.extend(t_parse(t))
    return out


def t_apply(t, *ts):
    return Exps([Statement(Label(t), '=', t_concat(*ts))])


t_not = partial(t_apply, 'not')
t_and = partial(t_apply, 'and')
t_nand = partial(t_apply, 'nand')
t_or = partial(t_apply, 'or')
t_nor = partial(t_apply, 'nor')


def make_category(
    name,
    loc=None,
    loc_desc=None,
    available=None,
):
    name = name.format(prefix='ipa_category')
    if name in category_registry:
        raise ValueError(f'category {name!r} already registered')

    final = Exps()

    available = t_parse(available)
    if available:
        final.append(Statement(Label('available'), '=', available))

    category_registry[name] = final

    if loc:
        localization[f'{name}:0'] = loc

    if loc_desc:
        localization[f'{name}_desc:0'] = loc_desc


def make_automation(
    name,
    category=None,
    available=None,
    districts=None,
    buildings=None,
    job_changes=None,
    local_emergency=False,
    empire_emergancy=False,
):
    category = category if category else name
    districts = districts if districts else {}

    name = name.format(prefix='ipa_automate')
    if name in automation_registry:
        raise ValueError(f'automation {name!r} already registered')

    category = category.format(prefix='ipa_category')
    if (c := category_registry.get(category)) is None:
        raise ValueError(f'category {category!r} not found')
    category_available = c.get('available', Exps())

    final = Exps()
    final.append(Statement(Label('category'), '=', Quoted(category)))

    if local_emergency:
        final.append(Statement(Label('emergency'), '=', Label('yes')))

    if empire_emergancy:
        final.append(Statement(Label('empire_wide_emergency'), '=', Label('yes')))

    available = t_concat(category_available, available)
    if available:
        final.append(Statement(Label('available'), '=', available))

    district_exps = Exps()
    for district, district_available in districts.items():
        if district_available:
            make_automation(
                name=f'{name}_{district}',
                category=category,
                districts={district: None},
                available=t_concat(available, district_available),
            )
        else:
            district_exps.append(Label(district))
    if district_exps:
        final.append(Statement(Label('prio_districts'), '=', district_exps))

    building_exps = Exps()
    for building in maybe_iter(buildings):
        match building:
            case str():
                building_exps.append(make_building(building))
            case Statement(Label(), _, _):
                building_exps.append(building)
            case _:
                raise ValueError(building)
    if building_exps:
        final.append(Statement(Label('buildings'), '=', building_exps))

    job_change_exps = Exps()
    for job_change in maybe_iter(job_changes):
        match job_change:
            case Statement(Label(), _, _):
                job_change_exps.append(job_change)
            case _:
                raise ValueError(job_change)
    if job_change_exps:
        final.append(Statement(Label('job_changes'), '=', job_change_exps))

    automation_registry[name] = final

def make_building(
        name,
        label=None,
        available=None,
        upgrade=None,
):
    label = label if label else 'x'

    final = Exps()
    final.append(Statement(Label('building'), '=', Label(name)))

    available = t_parse(available)
    if available:
        final.append(Statement(Label('available'), '=', available))

    upgrade = t_parse(upgrade)
    if upgrade:
        final.append(Statement(Label('upgrade_trigger'), '=', upgrade))

    return Statement(Label(label), '=', final)


def make_job_change(
        name,
        amount,
        label=None,
        available=None,
):
    label = label if label else 'x'

    final = Exps()
    final.append(Statement(Label('job'), '=', Label(name)))
    final.append(Statement(Label('amount'), '=', Int(amount)))

    available = t_parse(available)
    if available:
        final.append(Statement(Label('available'), '=', available))

    return Statement(Label(label), '=', final)


def make_automation_resource(
        name,
        threshold=None,
        category=None,
        available=None,
        designations=None,
        **kw,
):
    category = category if category else name

    available = t_parse(available)

    if designations:
        has_designation = [
            t_parse(f'has_designation = {d}')
            for d in designations
        ]

        available_designation = t_concat(available, t_or(*has_designation))
        make_automation(
            name.format(prefix='{prefix}_designation'),
            category=category,
            available=available_designation,
            **kw,
        )

        available = t_concat(available, t_nor(*has_designation))

    make_automation(name=name, category=category, available=available, **kw)


make_category('planet_automation_deficit_restriction')
make_category('planet_automation_upgrade_buildings')

make_automation(
    name='{prefix}_upgrade_capital',
    category='planet_automation_upgrade_buildings',
    local_emergency=True,
    available='''
        owner = { is_gestalt = no }
    ''',
    buildings=[
        'building_colony_shelter',
        'building_resort_capital',
        'building_slave_capital',
    ],
)
make_automation(
    name='{prefix}_upgrade_capital_habitat',
    category='planet_automation_upgrade_buildings',
    local_emergency=True,
    buildings=[
        'building_hab_capital'
    ],
)
make_automation(
    name='{prefix}_upgrade_capital_hive',
    category='planet_automation_upgrade_buildings',
    local_emergency=True,
    available='''
        owner = { is_hive_empire = yes }
    ''',
    buildings=[
        'building_hive_capital',
    ]
)
make_automation(
    name='{prefix}_upgrade_capital_machine',
    category='planet_automation_upgrade_buildings',
    local_emergency=True,
    available='''
        owner = { is_machine_empire = yes }
    ''',
    buildings=[
        'building_deployment_post',
    ],
)

make_automation(
    name='{prefix}_idyllic_bloom',
    category='planet_automation_upgrade_buildings',
    local_emergency=True,
    available='''
        owner = { or = {
            has_valid_civic = civic_idyllic_bloom
            has_valid_civic = civic_hive_idyllic_bloom
        } }
    ''',
    buildings=[
        # TODO: check if this works as expected
        make_building(
            name='building_gaiaseeders_1',
            available='always = no',
            upgrade='always = yes',
        ),
    ],
)

make_category(
    name='{prefix}_research',
    loc='£physics£ £society£ £engineering£ Research'
)
make_automation_resource(
    name='{prefix}_research',
    districts={
        'district_hab_science': None,
        'district_rw_science': None,
    },
    buildings=[
        'building_institute',
        'building_supercomputer',
        make_building(
            name='building_research_lab_1',
            available='''
                num_free_districts = { type = district_hab_science value = 0 }
                num_free_districts = { type = district_rw_science value = 0 }
            ''',
        ),
    ],
    designations=[
        'col_research',
        'col_ecu_research',
        'col_habitat_research',
        'col_ring_research',
    ],
)

make_category(
    name='{prefix}_unity',
    loc='£unity£ $unity$'
)
make_automation_resource(
    name='{prefix}_unity',
    available='''
        owner = {
            is_gestalt = no
            is_spiritualist = no
            has_make_spiritualist_perk = no
        }
    ''',
    districts={
        'district_arcology_administrative': None,
    },
    buildings=[
        'building_autocurating_vault',
        'building_corporate_vault',
        make_building(
            name='building_bureaucratic_1',
            available='''
                num_free_districts = { type = district_arcology_administrative value = 0 }
            ''',
        ),
    ],
    designations=[
        'col_bureau',
        'col_habitat_bureau',
    ],
)

make_automation_resource(
    name='{prefix}_unity_religious',
    category='{prefix}_unity',
    available='''
        owner = {
            is_gestalt = no
            or = {
                is_spiritualist = yes
                has_make_spiritualist_perk = yes
            }
        }
    ''',
    districts={
        'district_arcology_religious': None,
    },
    buildings=[
        'building_citadel_of_faith',
        make_building(
            name='building_sacrificial_temple_1',
            available='''
                owner = { is_death_cult_empire = yes }
                num_free_districts = { type = district_arcology_religious value = 0 }
            ''',
        ),
        make_building(
            name='building_temple',
            available='''
                owner = { is_death_cult_empire = no }
                num_free_districts = { type = district_arcology_religious value = 0 }
            ''',
        ),
    ],
    designations=[
        'col_bureau_spiritualist',
        'col_habitat_bureau_spiritualist',
    ]
)

make_automation_resource(
    name='{prefix}_unity_hive',
    category='{prefix}_unity',
    available='''
        owner = { is_hive_empire = yes }
    ''',
    buildings=[
        'building_alpha_hub',
        'building_hive_node',
    ],
    designations=[
        'col_bureau_hive',
        'col_habitat_bureau_hive',
    ],
)

make_automation_resource(
    name='{prefix}_unity_machine',
    category='{prefix}_unity',
    available='''
        owner = {
            is_machine_empire = yes
            not = { has_valid_civic = civic_machine_servitor }
        }
    ''',
    buildings=[
        'building_alpha_hub',
        'building_uplink_node',
    ],
    designations=[
        'col_bureau_machine',
        'col_habitat_bureau_machine',
    ],
)

make_automation_resource(
    name='{prefix}_unity_servitor',
    category='{prefix}_unity',
    available='''
        owner = {
            is_machine_empire = yes
            has_valid_civic = civic_machine_servitor
        }
    ''',
    districts={
        'district_hab_cultural': '''
            nor = {
                has_available_jobs = bio_trophy
                has_forbidden_jobs = bio_trophy
            }
        ''',
        'district_arcology_organic_housing': '''
            nor = {
                has_available_jobs = bio_trophy
                has_forbidden_jobs = bio_trophy
            }
        ''',
    },
    buildings=[
        make_building(
            name='building_organic_sanctuary',
            upgrade='''
                nor = {
                    has_available_jobs = bio_trophy
                    has_forbidden_jobs = bio_trophy
                }
                num_free_districts = { type = district_hab_cultural value = 0 }
                num_free_districts = { type = district_arcology_organic_housing value = 0 }
            ''',
            # upgrades happen with higher priority than building
            available='''
                nor = {
                    has_available_jobs = bio_trophy
                    has_forbidden_jobs = bio_trophy
                }
                num_free_districts = { type = district_hab_cultural value = 0 }
                num_free_districts = { type = district_arcology_organic_housing value = 0 }
            ''',
        ),
    ],
    designations=[
        'col_trophy_machine',
    ],
)

make_category(
    name='{prefix}_trade_value',
    loc='£trade_value£ Trade Value',
    available='''
        owner = { is_gestalt = no }
    ''',
)

make_automation_resource(
    name='{prefix}_trade_value',
    districts={
        'district_hab_commercial': None,
        'district_rw_commercial': None,
        'district_srw_commercial': None,
    },
    buildings=[
        'building_galactic_stock_exchange',
        make_building(
            name='building_commercial_zone',
            available='''
                num_free_districts = { type = district_hab_commercial value = 0 }
                num_free_districts = { type = district_rw_commercial value = 0 }
                num_free_districts = { type = district_srw_commercial value = 0 }
            ''',
        ),
    ],
    designations=[
        'col_habitat_trade',
        'col_ring_trade',
        'col_resort',
    ]
)

make_category(
    name='{prefix}_alloys',
    loc='£alloys£ $alloys$',
)

make_automation_resource(
    name='{prefix}_alloys',
    districts={
        'district_industrial': '''
            not = { has_designation = col_factory }
        ''',
        'district_hab_industrial': '''
            not = { has_designation = col_habitat_factory }
        ''',
        'district_arcology_arms_industry': None,
        'district_rw_industrial': '''
            not = { has_designation = col_factory }
        ''',
    },
    buildings=[
        'building_foundry_1',
        'building_ministry_production',
        'building_production_center',
        'building_coordinated_fulfillment_center_1',
    ],
    designations=[
        'col_ecu_foundry',
        'col_foundry',
        'col_habitat_foundry',
        'col_hiv_foundry',
        'col_mac_foundry',
    ],
)

make_category(
    name='{prefix}_consumer_goods',
    loc='£consumer_goods£ $consumer_goods$',
)

make_automation_resource(
    name='{prefix}_consumer_goods',
    districts={
        'district_industrial': '''
            not = { has_designation = col_foundry }
        ''',
        'district_hab_industrial': '''
            not = { has_designation = col_habitat_foundry }
        ''',
        'district_arcology_civilian_industry': None,
        'district_rw_industrial': '''
            not = { has_designation = col_foundry }
        ''',
        # TODO: 'district_srw_commercial': None,
    },
    buildings=[
        'building_factory_1',
        'building_ministry_production',
        'building_production_center',
        'building_coordinated_fulfillment_center_1',
    ],
    designations=[
        'col_ecu_factory',
        'col_factory',
        'col_habitat_factory',
        'col_mac_factory',
    ],
)

make_category(
    name='{prefix}_energy',
    loc='£energy£ $energy$',
)

make_automation_resource(
    name='{prefix}_energy',
    districts={
        'district_generator': None,
        'district_generator_uncapped': None,
        'district_hab_energy': None,
    },
    buildings=[
        'building_energy_grid',
        'building_betharian_power_plant',
        'building_waste_reprocessing_center',
    ],
    designations=[
        'col_generator',
        'col_habitat_energy',
        'col_ring_generator',
    ],
)

make_category(
    name='{prefix}_minerals',
    loc='£minerals£ $minerals$',
)

make_automation_resource(
    name='{prefix}_minerals',
    districts={
        'district_mining': None,
        'district_mining_uncapped': None,
        'district_hab_mining': None,
    },
    buildings=[
        'building_mineral_purification_plant',
    ],
    designations=[
        'col_mining',
        'col_habitat_mining',
    ],
)

make_category(
    name='{prefix}_food',
    loc='£food£ $food$',
)

make_automation_resource(
    name='{prefix}_food',
    districts={
        'district_farming': None,
        'district_farming_uncapped': None,
        # 'district_hab_housing': None, # TODO: probably a bad choice
        'district_rw_farming': None,
    },
    buildings=[
        'building_food_processing_facility',
    ],
    designations=[
        'col_farming',
        # 'col_habitat_farming', # TODO: as above
        # 'col_habitat_gestalt_farming', # TODO: as above
        'col_ring_farming',
    ],
)


make_category(
    name='{prefix}_rare_resources',
    loc='£volatile_motes£ £exotic_gases£ £rare_crystals£ Rare Resources',
)

make_automation(
    name='{prefix}_volatile_motes_deficit',
    category='{prefix}_rare_resources',
    available='''
        owner = { has_monthly_income = { resource = volatile_motes value < 3 } }
    ''',
    buildings=[
        'building_mote_harvesters',
        'building_chemical_plant',
    ],
    empire_emergancy=True
)

make_automation(
    name='{prefix}_exotic_gases_deficit',
    category='{prefix}_rare_resources',
    available='''
        owner = { has_monthly_income = { resource = exotic_gases value < 3 } }
    ''',
    buildings=[
        'building_gas_extractors',
        'building_refinery',
    ],
    empire_emergancy=True,
)

make_automation_resource(
    name='{prefix}_rare_crystals_deficit',
    category='{prefix}_rare_resources',
    threshold=(+3),
    empire_emergancy=True,
    available='''
        owner = { has_monthly_income = { resource = rare_crystals value < 3 } }
    ''',
    buildings=[
        'building_crystal_mines',
        'building_crystal_plant',
    ],
)

make_category(
    name='{prefix}_military',
    loc='£job_soldier£ Military',
)
make_automation(
    name='{prefix}_military',
    buildings=[
        'building_stronghold',
    ],
)

make_category(
    name='{prefix}_manage_crime',
    loc='£crime£ [Owner.GetCrimeDeviancy]',
)
make_automation(
    name='{prefix}_manage_crime',
    local_emergency=True,
    available = '''
        owner = { is_gestalt = no }
    ''',
    buildings=[
        make_building(
            name='building_precinct_house',
            available='''
                planet_crime > 30
                nor = {
                    has_available_jobs = enforcer
                    has_forbidden_jobs = enforcer
                }
            ''',
            upgrade='''
                planet_crime > 30
                nor = {
                    has_available_jobs = enforcer
                    has_forbidden_jobs = enforcer
                }
            ''',
        )
    ],
    job_changes=[
        make_job_change(
            name='enforcer',
            amount=(+1),
            # TODO: restore planet stability?
            available='''
                planet_crime > 27
            ''',
        ),
        make_job_change(
            name='enforcer',
            amount=(-1),
            available='''
                planet_crime < 1
            ''',
        ),
    ],
)
make_automation(
    name='{prefix}_manage_crime_gestalt',
    category='{prefix}_manage_crime',
    local_emergency=True,
    available = '''
        owner = { is_gestalt = yes }
    ''',
    buildings=[
        make_building(
            name='building_sentinel_posts',
            available='''
                planet_crime > 30
                nor = {
                    has_available_jobs = patrol_drone
                    has_forbidden_jobs = patrol_drone
                }
            ''',
        )
    ],
    job_changes=[
        make_job_change(
            name='patrol_drone',
            amount=(+1),
            # TODO: restore planet stability?
            available='''
                planet_crime >= 27
            ''',
        ),
        make_job_change(
            name='patrol_drone',
            amount=(-1),
            available='''
                planet_crime < 1
            ''',
        ),
    ],
)

make_category(
    name='{prefix}_manage_amenities',
    loc='[Owner.GetAmenitiesIcon] Amenities',
    available='''
        log = "- \\\\[This.GetName]"
        log = "- ipa_planet_free_amenities_target = \\\\[This.ipa_planet_free_amenities_target]"
        log = "- ipa_planet_amenities = \\\\[This.ipa_planet_amenities]"
        log = "- ipa_planet_amenities_no_happiness = \\\\[This.ipa_planet_amenities_no_happiness]"
    '''
)
localization.update({
    'amenities_icon:0': '£amenities£',
    'amenities_no_happiness_icon:0': '£amenities_no_happiness£',
})
scripted_loc.update({
    'GetAmenitiesIcon': '''
        text = {
            localization_key = amenities_no_happiness_icon
            trigger = { is_gestalt = yes }
        }
        text = {
            localization_key = amenities_icon
            trigger = { is_gestalt = no }
        }
    ''',
    'ipa_planet_free_amenities_target': '''
        value = value:ipa_planet_free_amenities_target
    ''',
})

scripted_values.update({
    'scripted_modifier_add_mult': '''
        base = 0
        add = modifier:$MODIFIER$_add
        mult = value:scripted_modifier_mult|MODIFIER|$MODIFIER$_mult|
    ''',
    'ipa_planet_free_amenities_target': '''
        base = 0
        add = value:scripted_modifier_add_mult|MODIFIER|planet_amenities|
        add = value:scripted_modifier_add_mult|MODIFIER|planet_amenities_no_happiness|
        subtract = trigger:free_amenities
        modifier = {
            not = { has_planet_flag = ipa_target_high_amenities }
            mult = 0.05
        }
        ceiling = yes
    ''',
    'ipa_planet_free_amenities_target_high': '''
        base = 10
        add = value:ipa_planet_free_amenities_target
    ''',
})

make_automation(
    name='{prefix}_manage_amenities',
    local_emergency=True,
    available='''
        owner = { is_gestalt = no }
        nor = {
            has_available_jobs = entertainer
            has_forbidden_jobs = entertainer
        }
        free_amenities <= value:ipa_planet_free_amenities_target
    ''',
    buildings=[
        'building_holo_theatres',
    ],
)
make_automation(
    name='{prefix}_manage_amenities_jobs',
    category='{prefix}_manage_amenities',
    available='''
        owner = { is_gestalt = no }
    ''',
    job_changes=[
        make_job_change(
            name='entertainer',
            amount=(-1),
            available='''
                free_amenities > value:ipa_planet_free_amenities_target_high
            ''',
        ),
        make_job_change(
            name='entertainer',
            amount=(+1),
            available='''
                free_amenities <= value:ipa_planet_free_amenities_target
            ''',
        ),
    ],
)

make_automation(
    name='{prefix}_manage_amenities_gestalt',
    category='{prefix}_manage_amenities',
    local_emergency=True,
    available='''
        owner = { is_gestalt = yes }
        nor = {
            has_available_jobs = maintenance_drone
            has_forbidden_jobs = maintenance_drone
        }
        free_amenities <= value:ipa_planet_free_amenities_target
    ''',
    districts={
        'district_hab_housing': None,
        'district_arcology_housing': None,
        'district_rw_nexus': None,
        'district_city': None,
        'district_hive': None,
        'district_nexus': None,
    },
)
make_automation(
    name='{prefix}_manage_amenities_gestalt_jobs',
    category='{prefix}_manage_amenities',
    available='''
        owner = { is_gestalt = yes }
    ''',
    job_changes=[
        make_job_change(
            name='maintenance_drone',
            amount=(-1),
            available='''
                free_amenities > value:ipa_planet_free_amenities_target_high
            ''',
        ),
        make_job_change(
            name='maintenance_drone',
            amount=(+1),
            available='''
                free_amenities <= value:ipa_planet_free_amenities_target
            ''',
        ),
    ],
)

make_category(
    name='{prefix}_pop_assembly_biological',
    loc='£mod_planet_pop_assembly_mult£ Pop Assembly: Biological',
)
make_automation(
    name='{prefix}_pop_assembly_biological_offspring',
    category='{prefix}_pop_assembly_biological',
    local_emergency=True,
    available='''
        owner = { has_origin = origin_progenitor_hive }
    ''',
    buildings=[
        'building_offspring_nest',
    ],
)
make_automation(
    name='{prefix}_pop_assembly_biological',
    local_emergency=True,
    buildings=[
        'building_spawning_pool',
        'building_clone_vats',
    ],
)

make_category(
    name='{prefix}_pop_assembly_robotic',
    loc='£mod_planet_pop_assembly_mult£ Pop Assembly: Robotic',
)
make_automation(
    name='{prefix}_pop_assembly_robotic',
    local_emergency=True,
    buildings=[
        'building_machine_assembly_plant',
        'building_robot_assembly_plant',
    ],
)

make_category(
    name='{prefix}_manage_bio_trophy',
    loc='£job_bio_trophy£ $job_bio_trophy_plural$',
    loc_desc='Ensures that there are no excess $job_bio_trophy$ jobs, enable the $unity$ automation to build additional sanctuaries.',
    available='''
        owner = { has_valid_civic = civic_machine_servitor }
    ''',
)
make_automation(
    name='{prefix}_manage_bio_trophy',
    job_changes=[
        make_job_change(
            name='bio_trophy',
            amount=(-1),
            available='''
                has_available_jobs = bio_trophy
            ''',
        ),
        make_job_change(
            name='bio_trophy',
            amount=(+1),
            available='''
                num_unemployed > 0
                any_owned_pop = {
                    is_unemployed = yes
                    can_work_specific_job = bio_trophy
                }
            ''',
        ),
    ],
)
make_automation(
    name='{prefix}_manage_bio_trophy_housing',
    category='{prefix}_manage_bio_trophy',
    local_emergency=True,
    available='''
        nor = {
            has_building = building_organic_sanctuary
            has_building = building_organic_paradise
            has_district = district_hab_cultural
            has_district = district_arcology_organic_housing
        }
    ''',
    districts={
        'district_hab_cultural': None,
        'district_arcology_organic_housing': None,
    },
    buildings=[
        make_building(
            name='building_organic_sanctuary',
            upgrade='always = no',
        ),
    ],
)

make_category(
    name='{prefix}_monument',
    loc='[Owner.GetMonumentJobIcon] [Owner.GetMonument]',
)
make_automation(
    name='{prefix}_monument',
    local_emergency=True,
    buildings=[
        'building_autochthon_monument',
        'building_corporate_monument',
        'building_simulation_1',
        'building_sensorium_1',
        'building_galactic_memorial_1',
    ],
)
localization.update({
    'job_culture_worker_icon:0': '£job_culture_worker£',
    'job_death_chronicler_icon:0': '£job_death_chronicler£',
    'job_evaluator_icon:0': '£job_evaluator£',
    'job_chronicle_drone_icon:0': '£job_chronicle_drone£',
})
scripted_loc.update({
    'GetMonument': '''
        text = {
            localization_key = building_galactic_memorial_1
            trigger = { is_memorialist_empire = yes }
        }
        text = {
            localization_key = building_sensorium_1
            trigger = { is_hive_empire = yes }
        }
        text = {
            localization_key = building_simulation_1
            trigger = { is_machine_empire = yes }
        }
        text = {
            localization_key = building_corporate_monument
            trigger = { is_megacorp = yes }
        }
        default = building_autochthon_monument
    ''',
    'GetMonumentJobIcon': '''
        text = {
            localization_key = job_culture_worker_icon
            trigger = {
                is_gestalt = no
                is_memorialist_empire = no
            }
        }
        text = {
            localization_key = job_evaluator_icon
            trigger = {
                is_gestalt = yes
                is_memorialist_empire = no
            }
        }
        text = {
            localization_key = job_death_chronicler_icon
            trigger = {
                is_gestalt = no
                is_memorialist_empire = yes
            }
        }
        text = {
            localization_key = job_chronicle_drone_icon
            trigger = {
                is_gestalt = yes
                is_memorialist_empire = yes
            }
        }
    ''',
})

make_category(
    name='{prefix}_noble_estates',
    loc='£job_noble£ $building_noble_estates$',
    available='''
        owner = { has_valid_civic = civic_aristocratic_elite }
    ''',
)
make_automation(
    name='{prefix}_noble_estates',
    local_emergency=True,
    buildings=['building_noble_estates'],
)

make_category(
    name='{prefix}_psi_corps',
    loc='£job_telepath£ $building_psi_corps$',
    available='''
        owner = { or = {
             has_ascension_perk = ap_mind_over_matter
             has_origin = origin_shroudwalker_apprentice
        } }
    ''',
)
make_automation(
    name='{prefix}_psi_corps',
    local_emergency=True,
    buildings=['building_psi_corps'],
)

make_category(
    name='{prefix}_posthumous_employment_center',
    loc='£job_reassigner£ $building_posthumous_employment_center$',
    available='''
        owner = { has_valid_civic = civic_permanent_employment }
    ''',
)
make_automation(
    name='{prefix}_posthumous_employment_center',
    local_emergency=True,
    buildings=['building_posthumous_employment_center'],
)

make_category(
    name='{prefix}_dread_encampment',
    loc='£job_necromancer£ $building_dread_encampment$',
    available='''
        owner = { has_valid_civic = civic_reanimated_armies }
    ''',
)
make_automation(
    name='{prefix}_dread_encampment',
    local_emergency=True,
    buildings=['building_dread_encampment'],
)

make_category(
    name='{prefix}_gene_clinic',
    loc='£job_healthcare£ $building_clinic$',
    available='''
        owner = { is_gestalt = no }
    ''',
)
make_automation(
    name='{prefix}_gene_clinic',
    local_emergency=True,
    buildings=['building_clinic'],
)

make_category(
    name='{prefix}_toxic_baths',
    loc='[Owner.GetToxicBathWithJobIcon]',
    available='''
        owner = { or = {
            has_valid_civic = civic_toxic_baths
            has_valid_civic = civic_corporate_toxic_baths
            has_valid_civic = civic_hive_toxic_baths
            has_valid_civic = civic_machine_toxic_baths
        } }
    ''',
)
make_automation(
    name='{prefix}_toxic_baths',
    local_emergency=True,
    buildings=[
        'building_toxic_bath',
        'building_toxic_bath_hive',
        'building_toxic_bath_machine',
    ],
)
localization.update({
    'job_bath_attendant_with_icon:0': '£job_bath_attendant£ $building_toxic_bath$',
    'job_bath_attendant_hive_with_icon:0': '£job_bath_attendant_hive£ $building_toxic_bath_hive$',
    'job_bath_attendant_machine_with_icon:0': '£job_bath_attendant_machine£ $building_toxic_bath_machine$',
})
scripted_loc.update({
    'GetToxicBathWithJobIcon': '''
        text = {
            localization_key = job_bath_attendant_with_icon
            trigger = { is_gestalt = no }
        }
        text = {
            localization_key = job_bath_attendant_hive_with_icon
            trigger = { is_hive_empire = yes }
        }
        text = {
            localization_key = job_bath_attendant_machine_with_icon
            trigger = { is_machine_empire = yes }
        }
    ''',
})

make_category('planet_automation_clear_blockers')

make_category(
    name='{prefix}_building_slots',
    loc='£building£ Building Slots',
)
make_automation(
    name='{prefix}_building_slots',
    local_emergency=True,
    available='''
        free_building_slots < 1
        num_buildings = { type = any value < 12 }
    ''',
    districts={
        'district_city': None,
        'district_hive': None,
        'district_nexus': None,
    },
)

make_category(
    name='{prefix}_housing',
    loc='£housing£ Housing',
)
make_automation(
    name='{prefix}_housing',
    local_emergency=True,
    available='''
        free_housing < 0
    ''',
    districts={
        'district_hab_housing': None,
        'district_arcology_housing': None,
        'district_rw_nexus': None,
        'district_city': None,
        'district_hive': None,
        'district_nexus': None,
    },
)


# fixes
localization.update({
    'planet_automation_designation_construction:0': '£district£ Designation',
    'planet_automation_rare_resources:0': '£exotic_gases£ £rare_crystals£ £volatile_motes£ Rare Resources',
    'planet_automation_pop_assembly:0': '£mod_planet_pop_assembly_mult£ Pop Assembly',
    'planet_automation_building_slot:0': '£building£ Building Slots',
    'planet_automation_crime:0': '£crime£ [Owner.GetCrimeDeviancy]',
})


def order_coverage(order, registry):
    out = {}
    seen = set()
    order_keys = set(order)

    for key in registry:
        if key not in order_keys:
            yield key, 'missing'

    for key in order:
        if key in seen:
            yield key, 'duplicate'
        elif key not in registry:
            yield key, 'unknown'
        seen.add(key)

    return out


def build_categories(args):
    categories = args.patcher.touch('common/colony_automation_categories/01_ipa_categories.txt')

    order = [
        'planet_automation_deficit_restriction',
        'planet_automation_upgrade_buildings',
        'ipa_category_research',
        'ipa_category_unity',
        'ipa_category_trade_value',
        'ipa_category_rare_resources',
        'ipa_category_alloys',
        'ipa_category_consumer_goods',
        'ipa_category_energy',
        'ipa_category_minerals',
        'ipa_category_food',
        'ipa_category_military',
        'ipa_category_manage_crime',
        'ipa_category_manage_amenities',
        'ipa_category_manage_bio_trophy',
        'ipa_category_pop_assembly_biological',
        'ipa_category_pop_assembly_robotic',
        'ipa_category_monument',
        'ipa_category_dread_encampment',
        'ipa_category_gene_clinic',
        'ipa_category_noble_estates',
        'ipa_category_posthumous_employment_center',
        'ipa_category_psi_corps',
        'ipa_category_toxic_baths',
        'planet_automation_clear_blockers',
        'ipa_category_building_slots',
        'ipa_category_housing',
    ]
    for key, status in order_coverage(order, category_registry):
        print(f'category {status}: {key!r}')

    for key in order:
        category = category_registry[key]
        categories.append(Statement(Label(key), '=', category))


def build_automations(args):
    automations = args.patcher.touch('common/colony_automation/01_ipa_automation.txt')
    exceptions = args.patcher.touch('common/colony_automation_exceptions/01_ipa_exceptions.txt')

    order = [
        'ipa_automate_pop_assembly_biological_offspring',

        'ipa_automate_manage_bio_trophy',
        'ipa_automate_manage_bio_trophy_housing',

        'ipa_automate_volatile_motes_deficit',
        'ipa_automate_exotic_gases_deficit',
        'ipa_automate_rare_crystals_deficit',

        'ipa_automate_upgrade_capital',
        'ipa_automate_upgrade_capital_hive',
        'ipa_automate_upgrade_capital_machine',
        'ipa_automate_upgrade_capital_habitat',

        'ipa_automate_manage_crime',
        'ipa_automate_manage_crime_gestalt',

        'ipa_automate_posthumous_employment_center',
        'ipa_automate_pop_assembly_biological',
        'ipa_automate_pop_assembly_robotic',

        'ipa_automate_manage_amenities',
        'ipa_automate_manage_amenities_jobs',
        'ipa_automate_manage_amenities_gestalt',
        'ipa_automate_manage_amenities_gestalt_jobs',

        'ipa_automate_housing',
        'ipa_automate_building_slots',

        'ipa_automate_idyllic_bloom',

        'ipa_automate_noble_estates',
        'ipa_automate_psi_corps',
        'ipa_automate_dread_encampment',
        'ipa_automate_monument',
        'ipa_automate_toxic_baths',
        'ipa_automate_gene_clinic',

        'ipa_automate_designation_research',
        'ipa_automate_designation_unity',
        'ipa_automate_designation_unity_religious',
        'ipa_automate_designation_unity_hive',
        'ipa_automate_designation_unity_machine',
        'ipa_automate_designation_unity_servitor_district_hab_cultural',
        'ipa_automate_designation_unity_servitor_district_arcology_organic_housing',
        'ipa_automate_designation_unity_servitor',
        'ipa_automate_designation_trade_value',
        'ipa_automate_designation_alloys_district_industrial',
        'ipa_automate_designation_alloys_district_hab_industrial',
        'ipa_automate_designation_alloys_district_rw_industrial',
        'ipa_automate_designation_alloys',
        'ipa_automate_designation_consumer_goods_district_industrial',
        'ipa_automate_designation_consumer_goods_district_hab_industrial',
        'ipa_automate_designation_consumer_goods_district_rw_industrial',
        'ipa_automate_designation_consumer_goods',
        'ipa_automate_designation_energy',
        'ipa_automate_designation_minerals',
        'ipa_automate_designation_food',

        'ipa_automate_military',

        'ipa_automate_research',
        'ipa_automate_unity',
        'ipa_automate_unity_religious',
        'ipa_automate_unity_hive',
        'ipa_automate_unity_machine',
        'ipa_automate_unity_servitor_district_hab_cultural',
        'ipa_automate_unity_servitor_district_arcology_organic_housing',
        'ipa_automate_unity_servitor',
        'ipa_automate_trade_value',
        'ipa_automate_alloys_district_industrial',
        'ipa_automate_alloys_district_hab_industrial',
        'ipa_automate_alloys_district_rw_industrial',
        'ipa_automate_alloys',
        'ipa_automate_consumer_goods_district_industrial',
        'ipa_automate_consumer_goods_district_hab_industrial',
        'ipa_automate_consumer_goods_district_rw_industrial',
        'ipa_automate_consumer_goods',
        'ipa_automate_energy',
        'ipa_automate_minerals',
        'ipa_automate_food',
    ]

    for key, status in order_coverage(order, automation_registry):
        fail = True
        print(f'automation {status}: {key!r}')

    for key in order:
        automation = automation_registry[key]

        statement = Statement(Label(key), '=', automation)

        local_emergency = automation.get('emergency') == 'yes'
        empire_emergancy = automation.get('empire_wide_emergency') == 'yes'
        if local_emergency or empire_emergancy:
            exceptions.append(statement)
        else:
            automations.append(statement)


@stellaris.mod('improved_planet_automation')
def build(args):
    p = args.patcher

    for _, prev in p.load_glob('common/colony_automation*/*.txt'):
        prev.clear()

    p.localize('ipa', localization.items())

    out = p.touch('common/scripted_loc/01_ipa.txt')
    for name, script in scripted_loc.items():
        out.append(stellaris.parse_template(
            '''
            defined_text = {
                name = $name
                random = no
                $script
            }
            ''',
            name=name,
            script=script,
        ))

    out = p.touch('common/script_values/01_ipa.txt')
    for name, script in scripted_values.items():
        out.append(Statement(Label(name), '=', stellaris.parse(script)))

    build_categories(args)
    build_automations(args)

if __name__ == '__main__':
    stellaris.build_mods()
