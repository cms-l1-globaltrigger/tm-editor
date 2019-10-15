#/!usr/bin/env python
# -*- coding: utf-8 -*-

import tmTable

import logging
import argparse
import sys, os

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('filename')
    return parser.parse_args()

def load_xml(filename, debug=False):
    menu = tmTable.Menu()
    scale = tmTable.Scale()
    extSignal = tmTable.ExtSignal()

    message = tmTable.xml2menu(filename, menu, scale, extSignal, debug)
    if message:
        raise RuntimeError(message)

    return menu, scale, extSignal

def main():

    args = parse_args()

    menu, scale, extSignal = load_xml(args.filename)

    print "-" * 80
    print "menu.name:", menu.menu['name']
    print "menu.is_valid:", menu.menu['is_valid']
    print "-" * 80
    print "scale.isValid:", scale.isValid()
    print "scale.scaleSet.scale_set_id:", scale.scaleSet['scale_set_id']
    print "scale.scaleSet.name:", scale.scaleSet['name']
    print "scale.scaleSet.is_valid:", scale.scaleSet['is_valid']
    print "-" * 80
    print "scales (", len(scale.scales), ")"
    for row in scale.scales:
        print row['object'], row['type'], "{ n_bits:", row['n_bits'], "}"
    # for row in scale.scales:
    #     print "::"
    #     print "  scale_id:", row['scale_id']
    #     print "  type:", row['type']
    #     print "  object:", row['object']
    #     print "  step:", row['step']
    #     print "  n_bins:", row['n_bins']
    #     print "  n_bits:", row['n_bits']
    #     print "  minimum:", row['minimum']
    #     print "  maximum:", row['maximum']

    return 0

if __name__ == '__main__':
    try:
        main()
    except RuntimeError as e:
        logging.error(format(e))
        sys.exit(1)
    else:
        sys.exit(0)
