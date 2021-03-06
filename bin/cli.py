#!/usr/bin/env python3

"""Prototype for HPE Container Platform API.

Required this functionality to be more usable: https://github.com/google/python-fire/issues/255

Example configuration file  (~/.hpecp.conf):

[default]
api_host = 127.0.0.1
api_port = 8080
use_ssl = True
verify_ssl = False
warn_ssl = True

[demosrv]
username = admin
password = admin123
"""

import base64
import sys
import os
import fire
import yaml
import json
import sys
if sys.version_info[0] >= 3:
    unicode = str

from hpecp import (
    ContainerPlatformClient,
    APIException,
    APIItemConflictException,
    APIItemNotFoundException,
)
from hpecp.k8s_cluster import K8sClusterHostConfig, K8sClusterStatus
from hpecp.gateway import Gateway, GatewayStatus

PROFILE = os.getenv("PROFILE", "default")
HPECP_CONFIG_FILE = os.getenv("HPECP_CONFIG_FILE", "~/.hpecp.conf")


def get_client():
    """Utility function to retrieve an authenticated client object"""
    try:
        client = ContainerPlatformClient.create_from_config_file(
            config_file=HPECP_CONFIG_FILE, profile=PROFILE
        )
        client.create_session()
        return client
    except APIException as e:
        print(e.message)
        sys.exit(1)


class Gateway(object):
    def create_with_ssh_key(
        self, ip, proxy_node_hostname, ssh_key=None, ssh_key_file=None, tags=[]
    ):
        """Create a Gateway using SSH key authentication

        :param ip: The IP address of the proxy host.  Used for internal communication.
        :param proxy_node_hostname: Clients will access cluster services will be accessed using this name.
        :param ssh_key: The ssh key data as a string.  Alternatively, use the ssh_key_file parameter.
        :param ssh_key_file: The file path to the ssh key.  Alternatively, use the ssh_key parameter.
        :param tags: Tags to use, e.g. "{ 'tag1': 'foo', 'tag2', 'bar' }".
        """
        if ssh_key is None and ssh_key_file is None:
            print("Either ssh_key or ssh_key_file must be provided")
            sys.exit(1)

        if ssh_key is not None and ssh_key_file is not None:
            print("Either ssh_key or ssh_key_file must be provided")
            sys.exit(1)

        if ssh_key_file is not None:
            with open(ssh_key_file) as f:
                ssh_key_data = f.read()

        try:
            gateway_id = get_client().gateway.create_with_ssh_key(
                ip=ip,
                proxy_node_hostname=proxy_node_hostname,
                ssh_key_data=ssh_key_data,
                tags=tags,
            )
            print(gateway_id)
        except APIItemConflictException:
            print("Gateway already exists.")
            sys.exit(1)

    def create_with_ssh_password(self):
        """Not yet implemented"""
        raise NotImplementedError("Not yet implemented")

    def get(self, gateway_id, output="yaml"):
        """Retrieve a Gateway by Id

        :param gateway_id: the id of the gateway with format: '/api/v1/workers/[0-9]+'
        :param output: how to display the output ['yaml'|'json']
        """
        response = get_client().gateway.get(gateway_id)
        if output == "yaml":
            print(
                yaml.dump(yaml.load(json.dumps(response.json), Loader=yaml.FullLoader))
            )
        else:
            print(response.json)

    def list(self, output="table", columns=Gateway.default_display_fields):
        """Retrieve the list of Gateways

        :param output: how to display the output [text|table|json]
        """
        if output == "table":
            print(get_client().gateway.list().tabulate(columns=columns))
        elif output == "text":
            print(get_client().gateway.list().tabulate(columns=columns, style='plain', display_headers=False))
        else:
            print(get_client().gateway.list().json)

    def delete(self, gateway_id, wait_for_delete_secs=0):
        """Retrieve a Gateway by Id

        :param gateway_id: the id of the gateway with format: '/api/v1/workers/[0-9]+'
        :param wait_for_delete_secs: if 0 return immediately after calling delete

        wait_for_delete_secs > 0 `calls wait_for_delete()`
        """
        try:
            get_client().gateway.delete(gateway_id)
        except APIException as e:
            print(e.message)
            sys.exit(1)

        if wait_for_delete_secs > 0:
            self.wait_for_delete(gateway_id=gateway_id, timeout_secs=wait_for_delete_secs)

    def wait_for_delete(self, gateway_id, timeout_secs=1200):
        """
        Wait for Gateway to be deleted
        :param gateway_id: Cluster id with format: /api/v1/workers/[0-9]+
        :param timeout_secs: how many secs to wait before exiting
        :returns True if gateway was deleted within timeout_secs.
        """
        self.wait_for_state(gateway_id=gateway_id, timeout_secs=timeout_secs)

    def wait_for_state(self, gateway_id, states=[], timeout_secs=1200):
        """
        Wait for Gateway to have one or more statuses
        :param gateway_id: Cluster id with format: /api/v1/workers/[0-9]+
        :param status: status(es) to wait for with format: ['status1', 'status2', 'statusn'] - set to [] to wait for item to be deleted
        :param timeout_secs: how many secs to wait before exiting
        :returns True/False if status was found within timeout_secs. May raise APIException.

        See also: `hpecp gateway states`
        """
        gateway_states = [GatewayStatus[s] for s in states]

        try:
            success = get_client().gateway.wait_for_state(
                            gateway_id=gateway_id, state=gateway_states)
        except:
            success = False
        
        if not success:
            print("Failed to reach state(s) {} in {}".format(str(states), str(timeout_secs)))
            sys.exit(1)

    def states(self):
        """Return a list of valid states"""
        print([ s.name for s in GatewayStatus ] )

class K8sWorker(object):
    def create_with_ssh_key(
        self, ip, ssh_key=None, ssh_key_file=None, tags=[]
    ):
        """Create a K8s Worker using SSH key authentication

        :param ip: The IP address of the host.  Used for internal communication.
        :param proxy_node_hostname: Clients will access cluster services will be accessed using this name.
        :param ssh_key: The ssh key data as a string.  Alternatively, use the ssh_key_file parameter.
        :param ssh_key_file: The file path to the ssh key.  Alternatively, use the ssh_key parameter.
        :param tags: Tags to use, e.g. "{ 'tag1': 'foo', 'tag2', 'bar' }".
        """
        if ssh_key is None and ssh_key_file is None:
            print("Either ssh_key or ssh_key_file must be provided")
            sys.exit(1)

        if ssh_key is not None and ssh_key_file is not None:
            print("Either ssh_key or ssh_key_file must be provided")
            sys.exit(1)

        if ssh_key_file is not None:
            with open(ssh_key_file) as f:
                ssh_key_data = f.read()

        try:
            worker_id = get_client().k8s_worker.create_with_ssh_key(
                ip=ip,
                ssh_key_data=ssh_key_data,
                tags=tags,
            )
            print(worker_id)
        except APIItemConflictException:
            print("Worker already exists.")
            sys.exit(1)

    def create_with_ssh_password(self):
        """Not yet implemented"""
        raise NotImplementedError("Not yet implemented")


    def list(self, all_columns=False, columns=["id", "description"]):
        """
        Print a table of K8s Workers
        :param all_columns: (True/False) set to True to return all columns
        :param columns: (aaa) afadsfs
        """
        print(get_client().k8s_worker.list().tabulate())

    def get(self, k8sworker_id):
        """Retrieve a K8s Worker

        :param k8sworker_id: the worker ID
        """
        print(get_client().k8s_worker.get(worker_id=k8sworker_id))

    def delete(self, k8sworker_id):
        """Delete a K8s Worker

        :param k8sworker_id: the cluster ID
        """
        print(get_client().k8s_worker.delete(worker_id=k8sworker_id))

class K8sCluster(object):
    def create(
        self,
        name,
        k8shosts_config,
        description=None,
        k8s_version=None,
        pod_network_range="10.192.0.0/12",
        service_network_range="10.96.0.0/12",
        pod_dns_domain="cluster.local",
        persistent_storage_local=False,
        persistent_storage_nimble_csi=False,
    ):
        """Create a K8s Cluster

        :param name: the cluster name
        :param k8shosts_config: k8s host ids and roles 'id1:master|worker,id2:master|worker,...'
        :param description: the cluster descripton
        :param k8s_version: e.g. 1.17.0
        :param pod_network_range: the pod network range, default='10.192.0.0/12'
        :param service_network_range: the service network range, default='10.96.0.0/12'
        :param pod_dns_domain: the pod dns domain, default='cluster.local'
        :param persistent_storage_local: True/False
        :param persistent_storage_nimble_csi: True/False
        """

        host_config = [
            K8sClusterHostConfig.create_from_list(h.split(":"))
            for h in k8shosts_config.split(",")
        ]

        print(
            get_client().k8s_cluster.create(
                name=name,
                description=description,
                k8s_version=k8s_version,
                pod_network_range=pod_network_range,
                service_network_range=service_network_range,
                pod_dns_domain=pod_dns_domain,
                persistent_storage_local=persistent_storage_local,
                persistent_storage_nimble_csi=persistent_storage_nimble_csi,
                k8shosts_config=host_config,
            )
        )

    def list(self, all_columns=False, columns=["id", "name", "description", "status"]):
        """
        Print a table of K8s Clusters
        :param all_columns: (True/False) set to True to return all columns
        :param columns: (aaa) afadsfs
        """

        if all_columns:
            print(get_client().k8s_cluster.list().tabulate())
        else:
            print(get_client().k8s_cluster.list().tabulate(columns=columns))

    def get(self, k8scluster_id):
        """Retrieve a K8s Cluster

        :param k8scluster_id: the cluster ID
        """
        response = get_client().k8s_cluster.get(k8scluster_id=k8scluster_id).json
        print(
                yaml.dump(yaml.load(json.dumps(response), Loader=yaml.FullLoader))
        )

    def admin_kube_config(self, k8scluster_id):
        """Retrieve a K8s Cluster Admin Kube Config

        :param k8scluster_id: the cluster ID
        """
        cfg = get_client().k8s_cluster.get(k8scluster_id=k8scluster_id).json['admin_kube_config']
        print(cfg.replace('\\n', '\n'))

    def dashboard_url(self, k8scluster_id):
        """Retrieve a K8s Cluster Dashboard URL

        :param k8scluster_id: the cluster ID
        """
        url = get_client().k8s_cluster.get(k8scluster_id=k8scluster_id).json['dashboard_endpoint_access']
        print(url)

    def dashboard_token(self, k8scluster_id):
        """Retrieve a K8s Cluster Dashboard Token

        :param k8scluster_id: the cluster ID
        """
        token = get_client().k8s_cluster.get(k8scluster_id=k8scluster_id).json['dashboard_token']
        print(base64.b64decode(token).decode('utf-8'))

    def delete(self, k8scluster_id):
        """Delete a K8s Cluster

        :param k8scluster_id: the cluster ID
        """
        print(get_client().k8s_cluster.delete(k8scluster_id=k8scluster_id))

    def wait_for_status(self, k8scluster_id, status=[], timeout_secs=60):
        """
        Wait for K8s Cluster to have one or more statuses
        :param k8scluster_id: Cluster id with format: /api/v2/k8scluster/[0-9]+
        :param status: status(es) to wait for with format: ['status1', 'status2', 'statusn']
        :param timeout_secs: how many secs to wait before exiting
        :returns True/False if status was found within timeout_secs. May raise APIException.
        """
        cluster_status = [K8sClusterStatus[s] for s in status]
        get_client().k8s_cluster.wait_for_status(
            k8scluster_id=k8scluster_id, status=cluster_status
        )

    def statuses(self):
        """Return a list of valid statuses"""
        print([ s.name for s in K8sClusterStatus ] )

class Lock(object):
    def get(self, output="yaml"):
        """Get the system and user locks
        :param output: how to display the output ['yaml'|'json']
        """
        response = get_client().lock.get()

        if output == "yaml":
            print(
                yaml.dump(yaml.load(json.dumps(response), Loader=yaml.FullLoader))
            )
        else:
            print(response)

    def list(self, output="yaml"):
        """Get the system and user locks
        :param output: how to display the output ['yaml'|'json']
        """
        self.get(output=output)

    def create(self, reason):
        """Create a lock"""
        get_client().lock.create(reason)
        print('Done')

    def delete(self, lock_id):
        """Delete a user lock"""
        print(get_client().lock.delete(lock_id))

    def delete_all(self, timeout_secs=300):
        """Delete all locks"""
        print(get_client().lock.delete_all(timeout_secs=300))

class License(object):
    def platform_id(self):
        """Get the platform ID
        """
        print(get_client().license.platform_id())

    def list(self, output="yaml", license_key_only=False):
        """Retrieve the list of licenses

        :param output: how to display the output ['yaml'|'json']
        """
        response = get_client().license.list()
        if license_key_only:
            response = [ str(unicode(l['LicenseKey'])) for l in response['Licenses'] ]
            print(response)
        else:
            if output == "yaml":
                print(
                    yaml.dump(yaml.load(json.dumps(response), Loader=yaml.FullLoader))
                )
            else:
                print(json.dumps(response))

    def register(self, server_filename):
        """Register a license

        :param server_filename: Filepath to the license on the server, e.g. '/srv/bluedata/license/LICENSE-1.txt'
        """
        get_client().license.register(server_filename=server_filename)
        print("Done.")

    def upload_with_ssh_key(self, server_filename, ssh_key_file=None, ssh_key_data=None, license_file=None, base64enc_license_data=None):
        """Not implemented yet! 

        TODO: 
        assert ssh_key_file or ssh_key_data argument is provided
        assert license_file or base64enc_license_data argument is provided

        Workaround: 
         - scp your license to '/srv/bluedata/license/' on the controller
         - run client.license.register(server_filename) to register the license
        """
        raise Exception("Not implemented yet! Workaround: scp your license to '/srv/bluedata/license/'")  
        
    def upload_with_ssh_pass(self, server_filename, ssh_username, ssh_password, license_file=None, base64enc_license_data=None):
        """Not implemented yet! 

        TODO: 
        assert ssh_key_file or ssh_key_data argument is provided
        assert license_file or base64enc_license_data argument is provided

        Workaround: 
         - scp your license to '/srv/bluedata/license/' on the controller
         - run client.license.register(server_filename) to register the license
        """
        raise Exception("Not implemented yet! Workaround: scp your license to '/srv/bluedata/license/'") 

    def delete(self, license_key):
        """Delete a license by LicenseKey
        
        :param license_key: The license key, e.g. '1234 1234 ... 1234 "SOMETEXT"'

        TIP: use `hpecp license list --license_key_only True` to get the license key
        """
        get_client().license.delete(license_key=license_key)
        print('Delete submitted - verify with: `hpecp license list`')

    def delete_all(self):
        """Delete all licenses"""
        response = get_client().license.list()
        all_license_keys = [ str(unicode(l['LicenseKey'])) for l in response['Licenses'] ]
        for licence_key in all_license_keys:
            get_client().license.delete(license_key=licence_key)
        print('Delete submitted - verify with: `hpecp license list`')

class HttpClient(object):

    def get(self, url):
        """Make HTTP GET request

        Example:

            hpecp httpclient get /api/v1/workers
        """
        response = get_client()._request(url, http_method='get', description='CLI HTTP GET')
        print(response.text)

    def delete(self, url):
        """Make HTTP DELETE request

        Example:

            hpecp httpclient delete /api/v1/workers/1
        """
        response = get_client()._request(url, http_method='delete', description='CLI HTTP DELETE')
        print(response.text)

    def post(self, url, json_file=''):
        """Make HTTP POST request

        Example:

            cat > my.json <<-EOF
            { 
                "external_identity_server":  {
                    "bind_pwd":"5ambaPwd@",
                    "user_attribute":"sAMAccountName",
                    "bind_type":"search_bind",
                    "bind_dn":"cn=Administrator,CN=Users,DC=samdom,DC=example,DC=com",
                    "host":"10.1.0.77",
                    "security_protocol":"ldaps",
                    "base_dn":"CN=Users,DC=samdom,DC=example,DC=com",
                    "verify_peer": false,
                    "type":"Active Directory",
                    "port":636 
                }
            }
            EOF

            hpecp httpclient post /api/v2/config/auth --json-file my.json
        """
        with open(json_file, 'r') as f:
            data = json.load(f)

        response = get_client()._request(url, http_method='post', data=data, description='CLI HTTP POST')
        print(response.text)


class CLI(object):
    def __init__(self):
        self.k8sworker = K8sWorker()
        self.k8scluster = K8sCluster()
        self.gateway = Gateway()
        self.lock = Lock()
        self.license = License()
        self.httpclient = HttpClient()


if __name__ == "__main__":
    fire.Fire(CLI)
