# -*- coding: utf-8 -*-
"""
Created on Tue Apr 21 00:21:37 2020

@author: user_id
"""

import json
import asyncio
import random
import os

from ledger_common import CommonLedger
from ledger_local import LocalLedger

SLEEPTIME = 1


class LocalBackup:
    """Makes shure to always keep a local backup of the necessary information.

    Uses two files in case one gets corrupted while writing.
    """

    def __init__(self,
                 local_ledger: LocalLedger,
                 common_ledger: CommonLedger,
                 id_=None):
        """Initialize the class."""
        self.local_ledger = local_ledger
        self.common_ledger = common_ledger
        if id_ is None:
            self.id = hash(random.random())
        else:
            self.id = id_

        folder = 'local_backup'
        self.backup_file1 = os.path.join(folder,
                                         f'local_backup1_{self.id}.txt')

        self.backup_file2 = os.path.join(folder,
                                         f'local_backup2_{self.id}.txt')

    def load_backup(self):
        """Import backup data."""
        data = None
        try:
            with open(self.backup_file1, 'r') as file:
                data = json.load(file)

        except Exception as e:
            try:
                with open(self.backup_file2, 'r') as file:
                    data = json.load(file)
            except Exception:
                pass

        if data is not None:

            common_ledger_bytes = data['common_ledger'].encode()
            self.common_ledger += CommonLedger(json_data=common_ledger_bytes)
            local_ledger_bytes = data['local_ledger'].encode()
            self.local_ledger += local_ledger_bytes



    async def run(self):
        """Run the coroutine.

        Dump the current state of the common_ledger and local_ledger to a file
        """
        while True:
            data = {'local_ledger': self.local_ledger.dumps(),
                    'common_ledger': self.common_ledger.dumps()}

            with open(self.backup_file1, 'w') as file:
                json.dump(data, file)


            with open(self.backup_file1, 'w') as file:
                json.dump(data, file)


            await asyncio.sleep(SLEEPTIME)
