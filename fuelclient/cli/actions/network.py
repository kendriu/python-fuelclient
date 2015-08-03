#    Copyright 2014 Mirantis, Inc.
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

import netaddr

from fuelclient.cli.actions.base import Action
from fuelclient.cli import arguments as Args
from fuelclient.cli.arguments import group
from fuelclient.cli import error
from fuelclient.objects.environment import Environment
from fuelclient import utils

DHCP_TEMPLATE_PATH = '/etc/cobbler/dnsmasq.template'

GROUP_ID_TEMPLATE = '# node group: {group_id}'

DNSMASQ_ENTRY_TEMPLATE = '\\n' + GROUP_ID_TEMPLATE + (
    '\\n'
    'dhcp-range=internal{group_id},{range_from},{range_to},{cidr},120m\\n'
    'dhcp-option=net:internal{group_id},option:router,{gateway}\\n'
    'dhcp-boot=net:internal{group_id},pxelinux.0,boothost,{boothost}')


def exec_cmd_on_cobbler(cmd, cwd=None):
    utils.exec_cmd('dockerctl shell cobbler ' + cmd, cwd)


class NetworkAction(Action):
    """Show or modify network settings of specific environments
    """
    action_name = "network"

    def __init__(self):
        super(NetworkAction, self).__init__()
        self.args = (
            Args.get_env_arg(required=True),
            Args.get_dir_arg("Directory with network data."),
            group(
                Args.get_download_arg(
                    "Download current network configuration."),
                Args.get_verify_arg(
                    "Verify current network configuration."),
                Args.get_upload_arg(
                    "Upload changed network configuration."),
                required=True
            ),
            Args.get_dnsmasq_arg("Update dnsmasq.template according to "
                                 "network configuration")
        )
        self.flag_func_map = (
            ("upload", self.upload),
            ("verify", self.verify),
            ("download", self.download)
        )

    def upload(self, params):
        """To upload network configuration from some
           directory for some environment:
                fuel --env 1 network --upload --dir path/to/directory
         If you want update dnsmasq.template in cobbler add "--dnsmasq"
           param:
               fuel --env 1 network --upload -dir path/to/directory --dnsmasq
        """
        env = Environment(params.env)
        network_data = env.read_network_data(
            directory=params.dir,
            serializer=self.serializer
        )
        env.set_network_data(network_data)
        print(
            "Network configuration uploaded."
        )
        if params.dnsmasq:
            self._update_dnsmasq_template(network_data['networks'])

    @utils.master_only
    def _update_dnsmasq_template(self, networks):
        fw_admin_nets = dict([(n['group_id'], n) for n in networks if
                              n['name'] == 'fuelweb_admin'])
        base_net = fw_admin_nets.pop(None)
        for group_id, net in fw_admin_nets.iteritems():
            marker = GROUP_ID_TEMPLATE.format(group_id=group_id)
            try:
                exec_cmd_on_cobbler('grep -q "{0}" {1}'.format(
                    marker, DHCP_TEMPLATE_PATH
                ))
            except error.ExecutedErrorNonZeroExitCode:
                # network is not in dnsmasq.template yet
                ip_range = net['ip_ranges'][0]
                entry = DNSMASQ_ENTRY_TEMPLATE.format(
                    group_id=group_id,
                    range_from=ip_range[0],
                    range_to=ip_range[1],
                    cidr=netaddr.IPNetwork(net['cidr']).netmask,
                    gateway=net['gateway'],
                    boothost=base_net['gateway']
                )
                exec_cmd_on_cobbler("sed -r '$a \{0}' -i {1};".format(
                    entry, DHCP_TEMPLATE_PATH))

        exec_cmd_on_cobbler('cobbler sync > /dev/null 2>&1')
        print (
            "Updated {0} and synced cobbler.".format(DHCP_TEMPLATE_PATH)
        )

    def verify(self, params):
        """To verify network configuration from some directory
           for some environment:
                fuel --env 1 network --verify --dir path/to/directory
        """
        env = Environment(params.env)
        response = env.verify_network()
        print(
            "Verification status is '{status}'. message: {message}"
            .format(**response)
        )

    def download(self, params):
        """To download network configuration in this
           directory for some environment:
                fuel --env 1 network --download
        """
        env = Environment(params.env)
        network_data = env.get_network_data()
        network_file_path = env.write_network_data(
            network_data,
            directory=params.dir,
            serializer=self.serializer)
        print(
            "Network configuration for environment with id={0}"
            " downloaded to {1}"
            .format(env.id, network_file_path)
        )
