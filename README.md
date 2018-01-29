# nbcli - Command Line Interface for NetBox

A CLI tool for making bulk changes to [NetBox](https://github.com/digitalocean/netbox) via it's API. 

This was written by a network engineer with who needed a way to compare spreadsheets to NetBox. It could probably be a lot better but at this point it's unlikely that I'll be doing much more with it. 

## What can it do?

Given a text file with appropriate info, nbcli can

- check whether or not objects in the file are also in Netbox
- bulk rename devices
- Confirm ip addresses of devices in Netbox
- List objects in NetBox based on IP address, asset number, or serial number

## Installation

### Requirements
* pyenv (`brew install pyenv`)
* Python modules:
  * argparse, distutils.util, csv, inspect, logging, os, pynetbox, requests, sys
  * (`pip install argparse distutils.util csv inspect logging os pynetbox requests sys`)
* NetBox token 

### Installing
* Clone this repo.
  * If you've got GitHub desktop installed you can click the big green "Clone or download" button and select "Open in Desktop". Make note of the directory you put it in.
* Open iTerm or Terminal and cd to the repo directory.
* Edit nbcli.py to add your NetBox URL to the line that says `NETBOX = 'https://your.url.here'`
* Edit .token and put your NetBox token in it. Nothing else, just the token.
* `pyenv local 2.7.13` or whatever you're 2.7.x is
  * sets the version of python to be used in this directory
  * if you don't have 2.7.13 `pyenv install versions` and install the latest 2.7, or use 2.7.13.
* Copy and paste this into the terminal: ```ln -s $(pwd)/nbcli.py /usr/local/bin/nbcli```
  * This creates a link in /usr/local/bin that points to the script in the local copy of the git repo.
  * Assuming that /usr/local/bin is in your path you can type nbcli in the CLI and it should give you the help screen.

2018-01-18/DN: I _think_ the above is correct but it's been a long time  since I did most of these things. 

## Usage?

In iTerm/Terminal enter `nbcli` to get the usage output. Or you could keep reading. 

### Argument Flags
```
usage: nbcli [options]

Do NetBox things via CLI

optional arguments:
  -h, --help            show this help message and exit
  -a ACTION, --action ACTION
                        delete, rename, export, list, locate
                        -a rename: requires a TSV input file with OLDNAME\tNEWNAME
                        -a list: with -f defaults to showing items in NetBox, use -r to reverse that
  -q QUERY, --query QUERY
                        General search in NetBox
  -f FILE, --file FILE  file with one -t TYPE per line (do not include mask or FQDN)
  -r, --reverse         reverse search to list objects in NetBox
  -hd, --headers        show headers when listing
  -t TYPE, --type TYPE  device, ip, vlan, circuit, rack, prefix, interface
```

### Examples

`nbcli -t device -f infile.txt -r`

- lists devices in infile.txt that are not in NetBox

`nbcli -t ip -f infile.txt`

 - lists ip addresses in infile.txt that are also in NetBox

`nbcli -a rename -f infile.txt`

- renames all devices in infile.txt if it contains one device per line with OLDname{tab}NEWname

`nbcli -t serial`

- list of all serial numbers

`nbcli -t ip`

- list of all IP addresses

# DEBUGGING
If you're having issues you can find the line with `logger.disabled = True` (currently line 31) and change it to False and it will print debug message while running to give help figure out what's going wrong.  I should probably move that to a CLI option.
