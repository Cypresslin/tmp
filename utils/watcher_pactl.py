#!/usr/bin/env python3
'''
Script for monitoring local recording events of a targeted app.
Parse the output base on two criteria:
1. 'change' event on 'Source'
2. Check the state of the changed source, highlight if it's 'RUNNING'

This file is part of the Ubuntu Phone pre-loaded app monitoring tool.

Copyright 2016 Canonical Ltd.
Authors:
  Po-Hsu Lin <po-hsu.lin@canonical.com>
'''

from gettext import gettext as _
import argparse
import re
import subprocess
import common_tools

parser = argparse.ArgumentParser(description='Sensitive event monitor with pactl')
parser.add_argument('--proc', help='Target app executable name', required=True)
parser.add_argument('--name', help='Target app human readable name')
args = parser.parse_args()


try:
    proc_name = args.proc
    app_name = args.name if args.name else 'APPNAME'
    # It's no necessary to get PID here, but still check it
    proc_id = subprocess.check_output(['adb', 'shell', 'ubuntu-app-pid', proc_name]).decode('utf-8').rstrip()
    if proc_id.isnumeric():
        status = ['RUNNING', 'IDLE']
        # Kill the old pactl subscribe task first
        common_tools.kill('pactl')
        # Track the audio recording event with pactl
        process = subprocess.Popen(['adb', 'shell', 'pactl', 'subscribe', '|', 'grep', 'source #'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        while True:
            output = process.stdout.readline().decode('utf-8').strip()
            if output == '' and process.poll() is not None:
                break
            else:
                if 'change' in output:
                    num = re.search('(\d+$)', output).group(0)
                    detail = subprocess.check_output(['adb', 'shell', 'pactl', 'list', 'sources']).decode('utf8')
                    # Reformat the output, truncate the output from source ~ properties
                    pattern = 'Source #{}(?P<status>.*Properties)'.format(num)
                    detail = re.search(pattern, detail, re.DOTALL).group('status')
                    for stat in status:
                        if stat in detail:
                            common_tools.printer(app_name, proc_name, 'audio', _('local recording'), stat)
    else:
        print(_("{} is not running").format(proc_name))

except KeyboardInterrupt:
    print(_("Process Terminated by user"))
except Exception as e:
    print(_("Exception occurred - {}").format(e))
