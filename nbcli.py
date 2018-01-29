#!/usr/bin/env python
"""nbcli is a CLI client for NetBox.

It enables a variety of bulk actions, especially the ability to check whether
or not items in a file are also in NetBox.
"""

from argparse import RawTextHelpFormatter
from distutils.util import strtobool
import argparse
import csv
import inspect
import logging
import os
import pynetbox
# import requests
import sys

NETBOX = 'https://your.url.here'


# =======================
def lineno():
    """Return current line number for use in logger.debug."""
    return str(inspect.currentframe().f_back.f_lineno).zfill(3)


# =======================
# setup debug logging (and disable by default)
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.disabled = True
# logger.disabled = False
logger.debug(lineno() + ': ==== start of program ====')

# ====================================================
# get the API token and create NetBox connection
path = os.path.dirname(os.path.realpath(__file__)) + '/.token'
with open(path) as f:
    secret = f.read().splitlines()
token = str(secret[0]).strip()
nb = pynetbox.api(NETBOX, token)


# =======================
def ArgParse(argparser):
    """Prep argument parser."""
    logger.debug(lineno() + ': ArgParse()')
    # -a ACTION
    argparser.add_argument(
        '-a', '--action', default='list',
        help='''delete, rename, export, list, locate
-a rename: requires a TSV input file with OLDNAME\\tNEWNAME
-a list: with -f defaults to showing items in NetBox, use -r to reverse that
''',
        required=False)
    # -f FILE
    argparser.add_argument(
        '-q', '--query', default=None, type=str,
        help='General search in NetBox'
    )
    argparser.add_argument(
        '-f', '--file', default=None,
        help='file with one -t TYPE per line (do not include mask or FQDN)'
    )
    # -t TYPE
    argparser.add_argument(
        '-r', '--reverse', action='store_true',
        help='reverse search to list objects in NetBox',
        required=False)
    argparser.add_argument(
        '-hd', '--headers',
        action='store_true',
        help='show headers when listing',
        required=False)
    argparser.add_argument(
        '-t', '--type', default='device',
        help='device, ip, vlan, circuit, rack, prefix, interface',
        required=False)

    # exit with --help if no arguments
    if len(sys.argv[1:]) == 0:
        argparser.print_help()
        sys.exit(1)

    args = argparser.parse_args()
    if (args.action == 'list') and args.type is None:
        argparser.error("-a list requires -t [type]")
    return vars(args)


# =============================
# Functions for pretty printing outputs
def print_row(column1, column2):
    print "%-35s %-15s" % (column1, column2)


def print_row(column1, column2):
    print "%-35s %-15s" % (column1, column2)


def print_row1(column1):
    print "%-35s" % (column1)


def print_row2(column1, column2):
    print "%-30s %-15s" % (column1, column2)


def print_row3(column1, column2, column3):
    print "%-30s %-15s %-15s" % (column1, column2, column3)


def print_row4(column1, column2, column3, column4):
    print "%-15s %-30s %-15s %-15s" % (column1, column2, column3, column4)


def print_row6(column1, column2, column3, column4, column5, column6):
    print("%-35s%-20s%-30s%-15s%-15s%-15s" %
          (column1, column2, column3, column4, column5, column6))


def print_row7(column1, column2, column3, column4, column5, column6, column7):
    print("%-35s%-20s%-30s%-15s%-15s%-15s%-15s" %
          (column1, column2, column3, column4, column5, column6, column7))


def print_row_ip(column1, column2, column3, column4, column5, column6):
    print("%-20s%-25s%-30s%-15s%-15s%-15s" %
          (column1, column2, column3, column4, column5, column6))


def print_row_vlan(column1, column2, column3, column4, column5):
    print("%-40s%-10s%-30s%-15s%-15s" %
          (column1, column2, column3, column4, column5))


def print_row_rack(column1, column2, column3):
    print "%-20s %-15s %-15s" % (column1, column2, column3)


def print_row_prefix(column1, column2, column3, column4, column5, column6):
    print("%-30s%-15s%-15s%-30s%-20s%-15s" %
          (column1, column2, column3, column4, column5, column6))


# =============================
# Handles all device related inquires
# Should split into further cleaner functions

def dcim(txtfile, type, reversecheck):
    response = nb.dcim.devices.all()
    csvname = arguments['file']
    # need to make the file optional - sometimes we just want to
    # query and see matching devices
    try:
        with open(csvname) as file:
            lines = [line.strip() for line in file]

        if arguments['type'] == 'device':
            string_list = [str(item) for item in response]
            strip_list = [item.strip() for item in string_list]
            a = set(lines)
            b = set(strip_list)
            common = a.intersection(b)
            notInSet2 = a.difference(b)
            if reversecheck:
                print "\nThese devices were not found in NetBox:"
                print '---------------------------------------'
                for line in notInSet2:
                    print_row1(line)
                print '\n'
            else:
                print "\nThese devices were found in NetBox:"
                print '-----------------------------------'
                for line in common:
                    print_row1(line)
                print '\n'

        elif ((arguments['type'] == 'asset_tag') or
              (arguments['type'] == 'asset')):
            if reversecheck:
                for line in response:
                    for lul in lines:
                        if (str(line.asset_tag) == str(lul)):
                            print_row2(str(line.display_name),
                                       str(line.asset_tag))
            else:
                for line in response:
                    for lul in lines:
                        if (str(line.asset_tag) == str(lul)):
                            lines.remove(lul)
                for notinnb in lines:
                    print(notinnb)

    except IOError:
        print '\nThe file does not exist'
    except KeyboardInterrupt:
        print('\nExiting...')
        sys.exit()


# =============================
#
def ipam(txtfile, query, reversecheck):
    try:
        hasSlash = False
        with open(arguments['file']) as file:
            checkList = [line.strip() for line in file]
        # Check for / in the infile
        if checkList[1].find('/') > -1:
            hasSlash = True
        inNetbox = nb.ipam.ip_addresses.all()
        if reversecheck:
            print_row3("Device", "IP", "Interface")
            for nbip in inNetbox:
                cleannbip = str(nbip.address)
                if not hasSlash:
                    cleannbip = cleannbip[:-3]
                for inip in checkList:
                    if cleannbip == str(inip):
                        try:
                            print_row3(str(nbip.interface.device.name),
                                       cleannbip, str(nbip.interface))
                            checkList.remove(inip)
                        except AttributeError:
                                try:
                                    print_row3(str(nbip.assignment), str(inip),
                                               str(nbip.interface))
                                    checkList.remove(inip)
                                except AttributeError:
                                        print_row3(str("no device"), str(inip),
                                                   str(nbip.interface))
                                        checkList.remove(inip)
                    else:
                        pass
        else:
            for nbip in inNetbox:
                cleannbip = str(nbip.address)
                if not hasSlash:
                    cleannbip = cleannbip[:-3]
                for inip in checkList:
                    if cleannbip == str(inip):
                        checkList.remove(inip)
            print("\nNot in NetBox")
            for item in checkList:
                print(item)
    except IOError:
        print('\nFile does not exist')
    except KeyboardInterrupt:
        print('\nExiting...')
        sys.exit()


def querysearch(query):
    try:
        response = nb.dcim.devices.filter(query)
        print('\nDEVICE')
        for device in response:
            print_row7(device.display_name, device.device_type,
                       device.site.name, device.rack, device.position,
                       device.asset_tag, device.serial)

    except AttributeError:
        pass
    try:
        response = nb.ipam.prefixes.filter(query)
        print('\nPREFIXES')
        for obj in response:
            print_row_prefix(obj.prefix, obj.status.label, obj.site,
                             obj.vlan, obj.role, obj.description)
    except AttributeError:
        pass
    try:
        response = nb.ipam.ip_addresses.filter(query)
        print('\nIP_ADDRESSES')
        for ip in response:
            print_row_ip(ip.address, ip.interface, ip.vrf,
                         ip.status, '-', ip.description)
    except AttributeError:
        pass
    try:
        response = nb.ipam.vlans.filter(query)
        print('\nVLANS')
        for vlan in response:
            print_row_vlan(vlan.display_name, vlan.site.name,
                           vlan.group, vlan.status, vlan.description)
    except AttributeError:
        pass
    try:
        response = nb.tenancy.tenants.filter(query)
        print('\nTENANTS')
        for line in response:
            print(line)
    except AttributeError:
        pass


def change_name(txtfile):
    """Bulk rename devices currently in netbox.
    Requires a TSV with one OLD_NAME\tNEW_NAME on each line.
    """
    # TODO: need error check for when dummy passes in file without new names
    try:
        csvname = arguments['file']
        names = []
        notfound = []
        with open(csvname, 'rb') as f:
            reader = csv.reader(f, delimiter='\t')
            for row in reader:
                names.append(row)
        for element in names:
            try:
                response = nb.dcim.devices.get(name=element[0])
                print(response.name + ' changed to ' + element[1])
                response.name = element[1]
                response.save()
                print(response.name)
            except AttributeError:
                notfound.append(element[0])
        if len(notfound) > 0:
            print('\nThese were not found in NetBox and could not be renamed:')
            for line in notfound:
                print(line)
    except KeyboardInterrupt:
        print('\nExiting...')
        sys.exit()


def querysearch(query):
    try:
        response = nb.dcim.devices.filter(query)
        print('\nDEVICE')
        for device in response:
            print_row7(device.display_name, device.device_type,
                       device.site.name, device.rack, device.position,
                       device.asset_tag, device.serial)

    except AttributeError:
        pass
    try:
        response = nb.ipam.prefixes.filter(query)
        print('\nPREFIXES')
        for obj in response:
            print_row_prefix(obj.prefix, obj.status.label, obj.site,
                             obj.vlan, obj.role, obj.description)
    except AttributeError:
        pass
    try:
        response = nb.ipam.ip_addresses.filter(query)
        print('\nIP_ADDRESSES')
        for ip in response:
            print_row_ip(ip.address, ip.interface, ip.vrf,
                         ip.status, '-', ip.description)
    except AttributeError:
        pass
    try:
        response = nb.ipam.vlans.filter(query)
        print('\nVLANS')
        for vlan in response:
            print_row_vlan(vlan.display_name, vlan.site.name,
                           vlan.group, vlan.status, vlan.description)
    except AttributeError:
        pass
    try:
        response = nb.tenancy.tenants.filter(query)
        print('\nTENANTS')
        for line in response:
            print(line)
    except AttributeError:
        pass


# =============================
def object_delete():
    """Bulk delete objects in netbox by device name or ip.
    Needs testing - AND CONFIRMATION
    """
    try:
        if prompt('ARE YOU SURE YOU WANT TO DELETE EVERYTHING IN ' +
                  arguments['file'] + '?'):
            csvname = arguments['file']
            objectsToDelete = arguments['delete']
            with open(csvname) as file:
                lines = [line.strip() for line in file]

            if objectsToDelete == 'device':
                for line in lines:
                    response = nb.dcim.devices.get(name=line)
                    response.delete
                    print line + ' deleted from NetBox'
            elif objectsToDelete == 'ip':
                for line in lines:
                    response = nb.ipam.ip_addresses.get(name=line)
                    response.delete
                    print line + ' deleted from NetBox'

            else:
                print "\nSpecify object type to delete"
        else:
            print('User did not confirm delete')
    except KeyboardInterrupt:
        print('\nExiting...')
        sys.exit()


# ==========================
def device_list():
    """Print asset_tag info for each device in netbox."""
    try:
        response = nb.dcim.devices.all()
        if arguments['headers']:
            print '\n'
            print_row6('NAME', 'PRIMARY IP', 'MODEL',
                       'STATUS', 'SERIAL', 'ASSET TAG')
            print 120 * '-'
        for device in response:
            print_row6(
                device.display_name, device.primary_ip, device.device_type,
                device.status, device.serial, device.asset_tag)
    except KeyboardInterrupt:
        print('\nExiting...')
        sys.exit()


# ==========================
def device_locate():
    """Print location for all devices in NetBox for physical inventory.

    Could be more useful if you could search for the specific device you want
    """
    try:
        response = nb.dcim.devices.all()
        if arguments['headers']:
            print '\n'
            print_row7('NAME', 'MODEL', 'SITE', 'RACK',
                       'RACK LOCATION', 'ASSET TAG', 'SN')
            print 130 * '-'
        for device in response:
            print_row7(device.display_name, device.device_type,
                       device.site.name, device.rack, device.position,
                       device.asset_tag, device.serial)
    except KeyboardInterrupt:
        print('\nExiting...')
        sys.exit()


# ==========================
def cereal():
    """Print serial number and Device name info for each device in NetBox."""
    try:
        response = nb.dcim.devices.all()
        if (arguments['file'] is None):
            for device in response:
                print_row2(device.serial, device.display_name)
        else:
            with open(arguments['file']) as file:
                lines = [line.strip() for line in file]

            string_list = [str(item.serial) for item in response]
            strip_list = [item.strip() for item in string_list]
            a = set(lines)
            b = set(strip_list)
            common = a.intersection(b)
            notInSetB = a.difference(b)

            # print str(strip_list)
            # print str(arguments['reverse'])
            if arguments['reverse']:    # show items NOT in NetBox
                for line in notInSetB:
                    print_row1(line)
            else:                       # show items IN NetBox
                for line in common:
                    print_row1(line)
    except KeyboardInterrupt:
        print('\nExiting...')
        sys.exit()


def cerealsearch():
    try:
        notfound = []
        with open(arguments['file']) as file:
            lines = [line.strip() for line in file]
        for inputserial in lines:
            try:
                response = nb.dcim.devices.get(serial=inputserial)
                print_row4(response.serial, response.display_name,
                           response.device_type.model, response.site)
            except AttributeError:
                notfound.append(inputserial)

        print('\nNot Found in NetBox:')
        for line in notfound:
            print(line)

    except KeyboardInterrupt:
        print('\nExiting...')
        sys.exit()


# ==========================
def eyepee():
    # ip - list returns IP, VLAN, device, interface, status, description
    try:
        response = nb.ipam.ip_addresses.all()
        if arguments['headers']:
            print_row_ip('IP_ADDRESS', 'INTERFACE', 'DEVICE',
                         'STATUS', 'VLAN', 'DESCRIPTION')
            print 120 * '-'
        for ip in response:
            try:
                print_row_ip(ip, ip.interface, ip.interface.device.name,
                             ip.status, '-', ip.description)
            except AttributeError:
                print_row_ip(ip, ip.interface, 'N/A',
                             ip.status, '-', ip.description)
    except KeyboardInterrupt:
        print('\nExiting...')
        sys.exit()


# =======================
def veelan():
    # vlan - vlan, site, prefix, status, description
    try:
        response = nb.ipam.prefixes.all()
        if arguments['headers']:
            print_row_vlan('VLAN', 'SITE', 'PREFIX', 'STATUS', 'DESCRIPTION')
            print 120 * '-'
        for prefixes in response:
            try:
                vlanid = prefixes.vlan.id
                vlanresponse = nb.ipam.vlans.get(vlanid)
                print_row_vlan(
                    vlanresponse.display_name,
                    vlanresponse.site.name,
                    prefixes, vlanresponse.status.label,
                    vlanresponse.description)
            except AttributeError:
                pass
        print 120 * '-'
    except KeyboardInterrupt:
        print('\nExiting...')
        sys.exit()


def sircut():
    """Return ID, Type, Provider, A Side, Z Side, Description.

    TODO: Implement a cross reference between circuit and circuit terminations
    """
    try:
        response = nb.circuits.circuits.all()
        if arguments['headers']:
            print_row6('ID', 'TYPE', 'PROVIDER',
                       'A-SIDE', 'Z-SIDE', 'DESCRIPTION')
            print 120 * '-'
        for obj in response:
            print_row6(obj.cid, obj.type, obj.provider,
                       obj.description[:3], '-', obj.description)
        print 120 * '-'
    except KeyboardInterrupt:
        print('\nExiting...')
        sys.exit()


def rack():
    """Return name, site, role."""
    try:
        response = nb.dcim.racks.all()
        if arguments['headers']:
            print_row_rack('NAME', 'SITE', 'ROLE')
            print 120 * '-'
        for obj in response:
            print_row_rack(obj.name, obj.site.name, obj.role)
        print 120 * '-'
    except KeyboardInterrupt:
        print('\nExiting...')
        sys.exit()


def prefix():
    """Return prefix, status, site, vlan, role, description."""
    try:
        response = nb.ipam.prefixes.all()
        if arguments['headers']:
            print_row_prefix('PREFIX', 'STATUS', 'SITE',
                             'VLAN', 'ROLE', 'DESCRIPTION')
            print 120 * '-'
        for obj in response:
            print_row_prefix(obj.prefix, obj.status.label, obj.site,
                             obj.vlan, obj.role, obj.description)
        print 120 * '-'
    except KeyboardInterrupt:
        print('\nExiting...')
        sys.exit()


def prompt(query):
    sys.stdout.write('%s [YES / NO]: ' % query)
    val = raw_input()
    try:
        ret = strtobool(val)
    except ValueError:
        sys.stdout.write('Please answer with a yes or no\n')
        return prompt(query)
    return ret


# =======================
if __name__ == "__main__":
    argparser = argparse.ArgumentParser(
        formatter_class=RawTextHelpFormatter,
        prog='nbcli',
        usage='%(prog)s [options]',
        description='A NetBox CLI tool useful for bulk actions and comparison',
        epilog="""Examples:\nnbcli -a list -t device -f mydevices.txt
Show all the devices in mydevices.txt that ARE in NetBox.

nbcli -a list -t device -f mydevices.txt -r
Show all the devices in mydevices.txt that are NOT in NetBox.
"""
    )
    arguments = ArgParse(argparser)
    if (arguments['file'] is not None):
        try:
            f = open(arguments['file'])
        except IOError:
            print 'Error: File "' + arguments['file'] + '" not accessible'
            sys.exit(1)
        else:
            f.close()

    # 2017-09-27/DN: Re-doing the if-thens to be more comprehensive.
    # 2017-09-27/DN: Wow. That is giant and messy. I'm 90% sure there's a better
    #       way to do that, I think it involves dictionaries but I'm not
    #       certain
    # 2017-10-16/AJ: Goddamn this looks ugly

    # ========================
    # query

    if (arguments['query'] is not None):
        querysearch(arguments['query'])
    # =======================
    # -t device
    elif (arguments['type'] == 'device'):
        if (arguments['action'] == 'list'):
            logger.debug(lineno() + ': -t ' + str(arguments))
            if (arguments['file'] is None):
                device_list()
            else:
                dcim(arguments['file'], arguments['type'],
                     arguments['reverse'])
        elif (arguments['action'] == 'delete'):
            logger.debug(lineno() + ': -t ' + str(arguments))
            object_delete()
        elif (arguments['action'] == 'rename'):
            logger.debug(lineno() + ': -t ' + str(arguments))
            if (arguments['file'] is None):
                print("Error: File required with one device name"
                      "per line - oldName{tab}newName")
            else:
                change_name(arguments['file'])
        elif (arguments['action'] == 'export'):
            logger.debug(lineno() + ': -t ' + str(arguments))
            print 'Not implemented: ' + str(arguments)
        elif (arguments['action'] == 'locate'):
            logger.debug(lineno() + ': -t ' + str(arguments))
            device_locate()
        else:
            print "Error: unregcognized action: -a", arguments['action']
            sys.exit(1)

    # -t circuit
    elif (arguments['type'] == 'circuit'):
        if (arguments['action'] == 'list'):
            logger.debug(lineno() + ': -t ' + str(arguments))
            sircut()
        elif (arguments['action'] == 'delete'):
            logger.debug(lineno() + ': -t ' + str(arguments))
            print 'Not implemented: ' + str(arguments)
        elif (arguments['action'] == 'rename'):
            logger.debug(lineno() + ': -t ' + str(arguments))
            print 'Not implemented: ' + str(arguments)
        elif (arguments['action'] == 'export'):
            logger.debug(lineno() + ': -t ' + str(arguments))
            print 'Not implemented: ' + str(arguments)
        elif (arguments['action'] == 'locate'):
            logger.debug(lineno() + ': -t ' + str(arguments))
            print 'Not implemented: ' + str(arguments)
        else:
            print "Error: unregcognized action: -a", arguments['action']
            sys.exit(1)

    # -t ip
    elif (arguments['type'] == 'ip'):
        if (arguments['action'] == 'list'):
            logger.debug(lineno() + ': -t ' + str(arguments))
            if (arguments['file'] is None):
                eyepee()
            else:
                ipam(arguments['file'], arguments['type'],
                     arguments['reverse'])
        elif (arguments['action'] == 'delete'):
            logger.debug(lineno() + ': -t ' + str(arguments))
            print 'Not implemented: ' + str(arguments)
        elif (arguments['action'] == 'rename'):
            logger.debug(lineno() + ': -t ' + str(arguments))
            print 'Not implemented: ' + str(arguments)
        elif (arguments['action'] == 'export'):
            logger.debug(lineno() + ': -t ' + str(arguments))
            print 'Not implemented: ' + str(arguments)
        elif (arguments['action'] == 'locate'):
            logger.debug(lineno() + ': -t ' + str(arguments))
            print 'Not implemented: ' + str(arguments)
        else:
            print "Error: unregcognized action: -a", arguments['action']
            sys.exit(1)

    # -t interface
    elif (arguments['type'] == 'interface'):
        if (arguments['action'] == 'list'):
            logger.debug(lineno() + ': -t ' + str(arguments))
            print 'Not implemented: ' + str(arguments)
        elif (arguments['action'] == 'delete'):
            logger.debug(lineno() + ': -t ' + str(arguments))
            print 'Not implemented: ' + str(arguments)
        elif (arguments['action'] == 'rename'):
            logger.debug(lineno() + ': -t ' + str(arguments))
            print 'Not implemented: ' + str(arguments)
        elif (arguments['action'] == 'export'):
            logger.debug(lineno() + ': -t ' + str(arguments))
            print 'Not implemented: ' + str(arguments)
        elif (arguments['action'] == 'locate'):
            logger.debug(lineno() + ': -t ' + str(arguments))
            print 'Not implemented: ' + str(arguments)
        else:
            print "Error: unregcognized action: -a", arguments['action']
            sys.exit(1)

    # -t prefix
    elif (arguments['type'] == 'prefix'):
        if (arguments['action'] == 'list'):
            logger.debug(lineno() + ': -t ' + str(arguments))
            prefix()
        elif (arguments['action'] == 'delete'):
            logger.debug(lineno() + ': -t ' + str(arguments))
            print 'Not implemented: ' + str(arguments)
        elif (arguments['action'] == 'rename'):
            logger.debug(lineno() + ': -t ' + str(arguments))
            print 'Not implemented: ' + str(arguments)
        elif (arguments['action'] == 'export'):
            logger.debug(lineno() + ': -t ' + str(arguments))
            print 'Not implemented: ' + str(arguments)
        elif (arguments['action'] == 'locate'):
            logger.debug(lineno() + ': -t ' + str(arguments))
            print 'Not implemented: ' + str(arguments)
        else:
            print "Error: unregcognized action: -a", arguments['action']
            sys.exit(1)

    # -t rack
    elif (arguments['type'] == 'rack'):
        if (arguments['action'] == 'list'):
            logger.debug(lineno() + ': -t ' + str(arguments))
            rack()
        elif (arguments['action'] == 'delete'):
            logger.debug(lineno() + ': -t ' + str(arguments))
            print 'Not implemented: ' + str(arguments)
        elif (arguments['action'] == 'rename'):
            logger.debug(lineno() + ': -t ' + str(arguments))
            print 'Not implemented: ' + str(arguments)
        elif (arguments['action'] == 'export'):
            logger.debug(lineno() + ': -t ' + str(arguments))
            print 'Not implemented: ' + str(arguments)
        elif (arguments['action'] == 'locate'):
            logger.debug(lineno() + ': -t ' + str(arguments))
            print 'Not implemented: ' + str(arguments)
        else:
            print "Error: unregcognized action: -a", arguments['action']
            sys.exit(1)

    # -t serial
    elif (arguments['type'] == 'serial'):
        if (arguments['action'] == 'list'):
            logger.debug(lineno() + ': -t ' + str(arguments))
            cereal()
        elif (arguments['action'] == 'delete'):
            logger.debug(lineno() + ': -t ' + str(arguments))
            print 'Not implemented: ' + str(arguments)
        elif (arguments['action'] == 'rename'):
            logger.debug(lineno() + ': -t ' + str(arguments))
            print 'Not implemented: ' + str(arguments)
        elif (arguments['action'] == 'export'):
            logger.debug(lineno() + ': -t ' + str(arguments))
            print 'Not implemented: ' + str(arguments)
        elif (arguments['action'] == 'locate'):
            logger.debug(lineno() + ': -t ' + str(arguments))
            cerealsearch()
        else:
            print "Error: unregcognized action: -a", arguments['action']
            sys.exit(1)

    # -t vlan
    elif (arguments['type'] == 'vlan'):
        if (arguments['action'] == 'list'):
            logger.debug(lineno() + ': -t ' + str(arguments))
            if (arguments['file'] is None):
                veelan()
            else:
                print "-t vlan with -f isn't working yet"
        elif (arguments['action'] == 'delete'):
            logger.debug(lineno() + ': -t ' + str(arguments))
            print 'Not implemented: ' + str(arguments)
        elif (arguments['action'] == 'rename'):
            logger.debug(lineno() + ': -t ' + str(arguments))
            print 'Not implemented: ' + str(arguments)
        elif (arguments['action'] == 'export'):
            logger.debug(lineno() + ': -t ' + str(arguments))
            print 'Not implemented: ' + str(arguments)
        elif (arguments['action'] == 'locate'):
            logger.debug(lineno() + ': -t ' + str(arguments))
            print 'Not implemented: ' + str(arguments)
        else:
            print "Error: unregcognized action: -a", arguments['action']
            sys.exit(1)

    # -t unrecognized
    else:
        print "Error: unregcognized type: -t", arguments['type']
        sys.exit(1)
