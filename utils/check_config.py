#!/usr/bin/env python3
'''
Script for checking basic config for a targeted app.

This file is part of the Ubuntu Phone pre-loaded app monitoring tool.

Copyright 2016 Canonical Ltd.
Authors:
  Po-Hsu Lin <po-hsu.lin@canonical.com>
'''

from gettext import gettext as _
import argparse
import json
import os
import subprocess
import common_tools

parser = argparse.ArgumentParser(description='Check basic config for an App')
group = parser.add_mutually_exclusive_group(required=True)
group.add_argument('--check-mode', action='store_true',
                   help='Check the AppArmor profile mode')
group.add_argument('--check-process', action='store_true',
                   help='Check if the process is confined by AppArmor profile')
group.add_argument('--check-policy', action='store_true',
                   help='Check the AppArmor policy for the app')
group.add_argument('--copy-rules', action='store_true',
                   help='Copy the AppArmor Final Rules for the app')
parser.add_argument('--proc', help='Target app executable name', required=True)
parser.add_argument('--path', help='Target directory for saving the log')
args = parser.parse_args()


def confine_check(process_name):
    '''
    Checking if this is a confined app
    '''
    command = ['adb', 'shell', 'ps', 'auxZ', '|', 'grep', '-v', 'unconfined',
               '|', 'grep', process_name]
    result = subprocess.check_output(command).strip().decode('utf8')
    return result is not ""


# Get the app name from the temperorary file
try:
    proc_name = args.proc
    # Check if the process is running, use ubuntu-app-list with grep
    cmd = ['adb', 'shell', 'ubuntu-app-list', '|', 'grep', proc_name]
    if subprocess.check_output(cmd):
        if args.check_mode:
            cmd = ['adb', 'shell', 'grep', proc_name, '/proc/*/attr/current']
            output = subprocess.check_output(cmd).decode('utf-8')
            if ' (enforce)' in output:
                print(_("Enforcement Mode"))
            elif ' (complain)' in output:
                print(_("Complain Mode"))
            else:
                print(_("Unconfined App"))
        elif args.check_process:
            if confine_check(proc_name):
                print(_("Yes"))
            else:
                print(_("No"))
        elif args.check_policy:
            if confine_check(proc_name):
                remote_path = '/var/lib/apparmor/clicks/{}.json'.format(proc_name)
                cmd = ['adb', 'shell', 'cat', remote_path]
                output = subprocess.check_output(cmd).decode('utf8')
                output = json.loads(output)
                for key in output:
                    print(key, ':', output[key])
            else:
                print(_("Unconfined App, no policy file available."))
        elif args.copy_rules:
            local_path = args.path if args.path else os.getcwd()
            remote_path = '/var/lib/apparmor/profiles/click_{}'.format(proc_name)
            cmd = ['adb', 'pull', remote_path, local_path]
            output = subprocess.check_output(cmd).decode('utf8')
            print(_("Done: file copied"))
    else:
        print(_("Error: App is not running"))
except Exception as e:
    print(_("Exception occurred - {}").format(e))
