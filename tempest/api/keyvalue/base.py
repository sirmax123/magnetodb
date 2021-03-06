# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2012 OpenStack Foundation
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

#from boto import exception

import tempest.clients
import tempest.config
import tempest.test
from tempest.api.keyvalue import test
from tempest.common.utils import data_utils
from tempest.openstack.common import log as logging


LOG = logging.getLogger(__name__)


class MagnetoDBTestCase(test.BotoTestCase):

    @classmethod
    def setUpClass(cls):
        super(MagnetoDBTestCase, cls).setUpClass()
        cls.os = tempest.clients.Manager()
        cls.client = cls.os.dynamodb_client
        # todo(yyekovenko) Research boto error handling verification approach
        #cls.ec = cls.ec2_error_code

        # SMOKE TABLE: THREADS
        cls.hashkey = 'forum'
        cls.rangekey = 'subject'
        cls.smoke_attrs = [
            {'AttributeName': cls.hashkey, 'AttributeType': 'S'},
            {'AttributeName': cls.rangekey, 'AttributeType': 'S'},
            {'AttributeName': 'message', 'AttributeType': 'S'},
            {'AttributeName': 'last_posted_by', 'AttributeType': 'S'},
            {'AttributeName': 'replies', 'AttributeType': 'N'},
        ]
        cls.smoke_schema = [
            {'AttributeName': cls.hashkey, 'KeyType': 'HASH'},
            {'AttributeName': cls.rangekey, 'KeyType': 'RANGE'}
        ]
        cls.smoke_gsi = None
        cls.smoke_lsi = [
            {
                'IndexName': 'last_posted_by_index',
                'KeySchema': [
                    {'AttributeName': cls.hashkey, 'KeyType': 'HASH'},
                    {'AttributeName': 'last_posted_by', 'KeyType': 'RANGE'}
                ],
                'Projection': {'ProjectionType': 'ALL'}
            }
        ]
        cls.smoke_throughput = {'ReadCapacityUnits': 1,
                                'WriteCapacityUnits': 1}

    @classmethod
    def wait_for_table_active(cls, table_name, timeout=120, interval=3):
        # TODO(yyekovenko) Add condition if creation failed?
        def check():
            resp = cls.client.describe_table(table_name)
            if "Table" in resp and "TableStatus" in resp["Table"]:
                return resp["Table"]["TableStatus"] == "ACTIVE"

        return tempest.test.call_until_true(check, timeout, interval)

    def wait_for_table_deleted(self, table_name, timeout=120, interval=3):
        def check():
            return table_name not in self.client.list_tables()['TableNames']

        return tempest.test.call_until_true(check, timeout, interval)

    def build_smoke_item(self, forum, subject, message,
                         last_posted_by, replies):
        return {
            "forum": {"S": forum},
            "subject": {"S": subject},
            "message": {"S": message},
            "last_posted_by": {"S": last_posted_by},
            "replies": {"N": replies},
        }

    def populate_smoke_table(self, table_name, keycount, count_per_key):
        new_items = []
        for _ in range(keycount):
            forum = 'forum%s' % data_utils.rand_int_id()
            for i in range(count_per_key):
                item = self.build_smoke_item(forum,
                                             'subject%s' % i,
                                             data_utils.rand_name(),
                                             data_utils.rand_uuid(),
                                             str(data_utils.rand_int_id()))
                self.client.put_item(table_name, item)
                new_items.append(item)
        return new_items
