
# Given STS is used, the previous rosa cleaner script left over orphaned roles and oidc script
# This script find roles and make sure they are not used by any clusters


import boto3
import os
from pathlib import Path
import json
import requests


API = 'https://api.openshift.com/api/clusters_mgmt/v1'
OCM_JSON = os.getenv('OCM_JSON', str(Path.home()) + "/.ocm.json")
DELETE = os.getenv("DELETE", 'False').lower() in ('true', '1', 't')


def get_token():

    f = open(OCM_JSON,)
    user = json.load(f)

    auth = (user['client_id'], user['access_token'])

    params = {
        "grant_type": "refresh_token",
        "refresh_token": user['refresh_token']
    }

    response = requests.post(user['token_url'], auth=auth, data=params)

    return response.json()['access_token']


def find_rosa_clusters(session):
    clusters = []
    response = session.get(API + "/clusters/?size=500")
#   print(json.dumps(response.json()))
    for cluster in response.json()['items']:
        if cluster['product']['id'] == 'rosa':
            clusters.append(cluster['id'])
    print(json.dumps(clusters))
    return clusters


def delete_role(iam, role):
    policies = iam.list_attached_role_policies(RoleName=role)
    for policy in policies['AttachedPolicies']:
        iam.detach_role_policy(RoleName=role, PolicyArn=policy['PolicyArn'])
    iam.delete_role(RoleName=role)


def delete_roles_not_in_cluster(iam, clusters):
    roles = iam.list_roles(MaxItems=500)['Roles']
    for role in roles:
        tags = iam.list_role_tags(RoleName=role['RoleName'])['Tags']
        for tag in tags:
            if tag['Key'] == 'rosa_cluster_id' and tag['Value'] not in clusters:
                print('Role does not belong to any active rosa cluster, need to be deleted {0}. the old rosa cluster id: {1}'.format(
                    role['RoleName'], tag['Value']))
                if DELETE:
                    delete_role(iam, role['RoleName'])


def delete_oidc_provider_not_in_cluster(iam, clusters):
    providers = iam.list_open_id_connect_providers()[
        'OpenIDConnectProviderList']
    for provider in providers:
        tags = iam.list_open_id_connect_provider_tags(
            OpenIDConnectProviderArn=provider['Arn'])['Tags']
        for tag in tags:
            if tag['Key'] == 'rosa_cluster_id' and tag['Value'] not in clusters:
                print('OIDC Provider does not belong to any active rosa cluster, need to be deleted {0}. the old rosa cluster id: {1}'.format(
                    provider['Arn'], tag['Value']))
                if DELETE:
                    iam.delete_open_id_connect_provider(
                        OpenIDConnectProviderArn=provider['Arn'])


session = requests.Session()
session.headers.update({'Authorization': 'Bearer {0}'.format(get_token())})
active_clusters = find_rosa_clusters(session)
iam = boto3.client('iam')
if not DELETE:
    print('-> This is in DRY_RUN mode. To delete the resource -> DELETE="1" python orphan-iam-cleaner.py')
delete_roles_not_in_cluster(iam, active_clusters)
delete_oidc_provider_not_in_cluster(iam, active_clusters)
