#! /usr/bin/env python

import stellaris
from stellaris.ast import *


@stellaris.mod('balance_rare_deposits')
def build(args):
    deposits = stellaris.load('common/deposits/01_planetary_deposits.txt')

    for exp in deposits:
        match exp:
            case Statement(Label(label), _, defn):
                if label.startswith('d_hab'):
                    continue

                if defn.get('category') != 'deposit_cat_rare':
                    continue

                print(label)


if __name__ == '__main__':
    stellaris.build_mods()
