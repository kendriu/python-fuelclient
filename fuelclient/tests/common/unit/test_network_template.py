# -*- coding: utf-8 -*-
#
#    Copyright 2015 Mirantis, Inc.
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

import json
import mock
import requests_mock
import yaml

from fuelclient.tests import base

YAML_TEMPLATE = """adv_net_template:
  default:
    network_assignments:
      fuelweb_admin:
        ep: br-fw-admin
      management:
        ep: br-mgmt
      private:
        ep: br-prv
      public:
        ep: br-ex
      storage:
        ep: br-storage
    nic_mapping:
      default:
        if1: eth0
    templates_for_node_role:
      ceph-osd:
      - common
      - storage
      compute:
      - common
      - private
      - storage
      controller:
      - public
      - private
      - storage
      - common
"""

JSON_TEMPLATE = """{
  "adv_net_template": {
    "default": {
      "nic_mapping": {
        "default": {
          "if1": "eth0"
        }
      },
      "templates_for_node_role": {
        "controller": [
          "public",
          "private",
          "storage",
          "common"
        ],
        "compute": [
          "common",
          "private",
          "storage"
        ],
        "ceph-osd": [
          "common",
          "storage"
        ]
      },
      "network_assignments": {
        "storage": {
          "ep": "br-storage"
        },
        "private": {
          "ep": "br-prv"
        },
        "public": {
          "ep": "br-ex"
        },
        "management": {
          "ep": "br-mgmt"
        },
        "fuelweb_admin": {
          "ep": "br-fw-admin"
        }
      }
    }
  }
}
"""


class TestNetworkTemplate(base.UnitTestCase):
    def setUp(self):
        super(TestNetworkTemplate, self).setUp()

        self.env_id = 42
        self.req_path = ('/api/v1/clusters/{0}/network_configuration/'
                         'template'.format(self.env_id))

        self.mocker = requests_mock.Mocker()
        self.mocker.start()

    def tearDown(self):
        self.mocker.stop()

    def test_upload_action(self):
        self.mocker.put(self.req_path)
        test_command = [
            'fuel', 'network-template', '--env', str(self.env_id), '--upload']

        m_open = mock.mock_open(read_data=YAML_TEMPLATE)
        with mock.patch('__builtin__.open', m_open, create=True):
            self.execute(test_command)

        self.assertEqual(self.mocker.last_request.method, 'PUT')
        self.assertEqual(self.mocker.last_request.path, self.req_path)
        self.assertEqual(self.mocker.last_request.json(),
                         json.loads(JSON_TEMPLATE))
        m_open().read.assert_called_once_with()

    def test_download_action(self):
        self.mocker.get(self.req_path, text=JSON_TEMPLATE)

        test_command = [
            'fuel', 'network-template', '--env', str(self.env_id),
            '--download']

        m_open = mock.mock_open()
        with mock.patch('fuelclient.cli.serializers.open', m_open,
                        create=True):
            self.execute(test_command)

        self.assertEqual(self.mocker.last_request.method, 'GET')
        self.assertEqual(self.mocker.last_request.path, self.req_path)

        written_yaml = yaml.safe_load(m_open().write.mock_calls[0][1][0])
        expected_yaml = yaml.safe_load(YAML_TEMPLATE)
        self.assertEqual(written_yaml, expected_yaml)
