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

import fuelclient
from fuelclient.tests import utils
from fuelclient.tests.v2.unit.lib import test_api


class TestNodeFacade(test_api.BaseLibTest):

    def setUp(self):
        super(TestNodeFacade, self).setUp()

        self.version = 'v1'
        self.res_uri = '/api/{version}/nodes/'.format(version=self.version)

        self.fake_node = utils.get_fake_node()
        self.fake_nodes = [utils.get_fake_node() for _ in range(10)]

        self.client = fuelclient.get_client('node', self.version)

    def test_node_list(self):
        matcher = self.m_request.get(self.res_uri, json=self.fake_nodes)
        self.client.get_all()

        self.assertTrue(matcher.called)

    def test_node_show(self):
        node_id = 42
        expected_uri = self.get_object_uri(self.res_uri, node_id)

        matcher = self.m_request.get(expected_uri, json=self.fake_node)

        self.client.get_by_id(node_id)

        self.assertTrue(matcher.called)

    def test_node_vms_list(self):
        node_id = 42
        expected_uri = "/api/v1/nodes/{0}/vms_conf/".format(node_id)

        fake_vms = [{'id': 1, 'opt2': 'val2'},
                    {'id': 2, 'opt4': 'val4'}]
        matcher = self.m_request.get(expected_uri, json=fake_vms)

        self.client.get_node_vms_conf(node_id)

        self.assertTrue(matcher.called)

    def test_node_vms_create(self):
        config = [{'id': 1, 'opt2': 'val2'},
                  {'id': 2, 'opt4': 'val4'}]
        node_id = 42

        expected_uri = "/api/v1/nodes/{0}/vms_conf/".format(node_id)
        expected_body = {'vms_conf': config}

        matcher = self.m_request.put(expected_uri, json=expected_body)

        self.client.node_vms_create(node_id, config)

        self.assertTrue(matcher.called)
        self.assertEqual(expected_body, matcher.last_request.json())

    def test_node_set_hostname(self):
        node_id = 42
        hostname = 'test-name'
        data = {"hostname": hostname}
        expected_uri = self.get_object_uri(self.res_uri, node_id)

        matcher = self.m_request.put(expected_uri, json=data)

        self.client.update(node_id, **data)

        self.assertTrue(matcher.called)
        self.assertEqual(data, matcher.last_request.json())

    def test_get_all_labels_for_all_nodes(self):
        matcher = self.m_request.get(self.res_uri, json=self.fake_nodes)
        self.client.get_all_labels_for_nodes()

        self.assertTrue(matcher.called)

    def test_set_labels_for_all_nodes(self):
        labels = ['key_1=val_1', 'key_2=val_2', 'key_3   =   val_4']
        data = {'labels': {
            'key_1': 'val_1',
            'key_2': 'val_2',
            'key_3': 'val_4'
        }}

        expected_uri = self.get_object_uri(self.res_uri, 42)

        matcher_get = self.m_request.get(self.res_uri, json=self.fake_nodes)
        matcher_put = self.m_request.put(expected_uri, json=data)

        self.client.set_labels_for_nodes(labels=labels)

        self.assertTrue(matcher_get.called)
        self.assertTrue(matcher_put.called)
        self.assertEqual(data, matcher_put.last_request.json())

    def test_set_labels_for_specific_nodes(self):
        labels = ['key_1=val_1', 'key_2=val_2', 'key_3   =   val_4']
        node_ids = ['42']
        data = {'labels': {
            'key_1': 'val_1',
            'key_2': 'val_2',
            'key_3': 'val_4'
        }}
        expected_uri = self.get_object_uri(self.res_uri, 42)

        matcher_get = self.m_request.get(expected_uri, json=self.fake_node)
        matcher_put = self.m_request.put(expected_uri, json=data)

        self.client.set_labels_for_nodes(
            labels=labels, node_ids=node_ids)

        self.assertTrue(matcher_get.called)
        self.assertTrue(matcher_put.called)
        self.assertEqual(data, matcher_put.last_request.json())

    def test_delete_labels_for_all_nodes(self):
        labels_keys = ['key_1', '   key_3   ']
        data = {'labels': {'key_2': None}}
        expected_uri = self.get_object_uri(self.res_uri, 42)

        matcher_get = self.m_request.get(self.res_uri, json=self.fake_nodes)
        matcher_put = self.m_request.put(expected_uri, json=data)

        self.client.delete_labels_for_nodes(labels_keys=labels_keys)

        self.assertTrue(matcher_get.called)
        self.assertTrue(matcher_put.called)
        self.assertEqual(data, matcher_put.last_request.json())

    def test_delete_labels_for_specific_nodes(self):
        labels_keys = ['key_2']
        node_ids = ['42']
        data = {'labels': {'key_1': 'val_1', 'key_3': 'val_3'}}
        expected_uri = self.get_object_uri(self.res_uri, 42)

        matcher_get = self.m_request.get(expected_uri, json=self.fake_node)
        matcher_put = self.m_request.put(expected_uri, json=data)

        self.client.delete_labels_for_nodes(
            labels_keys=labels_keys, node_ids=node_ids)

        self.assertTrue(matcher_get.called)
        self.assertTrue(matcher_put.called)
        self.assertEqual(data, matcher_put.last_request.json())

    def test_get_name_and_value_from_labels(self):
        for label in (
            'key=value',
            '   key   =value',
            'key=    value    ',
            '  key  =  value   ',
        ):
            name, value = self.client._split_label(label)
            self.assertEqual(name, 'key')
            self.assertEqual(value, 'value')

    def test_get_name_and_empty_value_from_lables(self):
        for label in (
            'key=',
            '   key   =',
            'key=        ',
            '  key  =     ',
        ):
            name, value = self.client._split_label(label)
            self.assertEqual(name, 'key')
            self.assertIsNone(value)

    def test_labels_after_delete(self):
        all_labels = {
            'label_A': 'A',
            'label_B': None,
            'label_C': 'C',
            'label_D': None,
        }
        expected_labels = {
            'label_A': 'A',
            'label_D': None,
        }

        for labels_to_delete in (
            ('label_B', 'label_C'),
            ('   label_B', 'label_C   '),
            ('label_B', 'label_C  ', 'unknown_label'),
        ):
            result = self.client._labels_after_delete(
                all_labels, labels_to_delete)
            self.assertEqual(result, expected_labels)
