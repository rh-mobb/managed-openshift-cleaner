#!/bin/env python3

import requests
from requests_oauthlib import OAuth2Session
import json
from pathlib import Path
import pprint
import datetime
from dateparser import parse
import os
import boto3
import time
from requests.exceptions import ConnectionError

pp = pprint.PrettyPrinter(indent=4)

API = 'https://api.openshift.com/api/clusters_mgmt/v1'
SKIP_CLUSTERS = ['mobb-infra', 'mobb-infra-gcp',
                 os.getenv('SKIP_CLUSTERS', '').split(",")]
DELETE_NEW_CLUSTERS = os.getenv('DELETE_NEW_CLUSTERS', '').split(",")
DELETE = os.getenv('DELETE', False)
DEBUG = os.getenv('DEBUG', False)
OCM_JSON = os.getenv('OCM_JSON', str(Path.home()) + "/.ocm.json")

# print(access_token)


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


def list_clusters(session):
    clusters = []
    response = session.get(API + "/clusters/")
    if DEBUG:
        pp.pprint(response.json())
    for cluster in response.json()['items']:
        if cluster['name'] not in SKIP_CLUSTERS and not cluster['name'].startswith('poc-'):
            if cluster['managed'] and cluster['cloud_provider']['id'] == 'aws' :
                clusters.append(cluster)
            else:
                print(
                    "-> skipping {0} (unmanaged / ARO / GCP)".format(cluster['name']))
        else:
            print("-> skipping {0}".format(cluster['name']))
    return clusters


def describe_cluster(session, id):
    response = session.get("{0}/clusters/{1}".format(API, id))
    return response.json()


def clusters_older_than_today(clusters):
    old = []
    new = []
    today = datetime.date.today()
    for cluster in clusters:
        creation_timestamp = parse(cluster['creation_timestamp']).date()
        if today > creation_timestamp:
            old.append(cluster)
        else:
            new.append(cluster)
    return old, new


def wait_for_deletion(session, cluster):
    while True:
        try:
          response = session.get(
              "{0}/clusters/{1}/status".format(API, cluster['id']))
          if response.json()['id'] != "404":
              print("-> cluster {0} is still under deleting, checking after 30 seconds. state is: {1}".format(
                  cluster['name'], response.json()['state']))
              time.sleep(30)
          else:
              print(
                  "-> cluster {0} is deleted, checking after 30 seconds".format(cluster['name']))
              break
        except requests.exceptions.RequestException as e:
          print(e)


def delete_cluster(session, cluster):
    if DELETE:
        print("-> deleting cluster {0}".format(cluster['name']))
        response = session.delete(
            "{0}/clusters/{1}".format(API, cluster['id']))
        if response.status_code == 204:
            if 'sts' in cluster['aws']:
                wait_for_deletion(session, cluster)
                delete_roles(cluster, iam)
                delete_oidc_endpoint(cluster, iam)
            return True
        else:
            print("-> failed to delete cluster {0}".format(cluster['name']))
            pp.pprint(response.json())
            return False
    else:
        print("-> pretending to delete cluster {0}".format(cluster['name']))
        return True


def delete_roles(cluster, iam):
    roles = []
    for role in cluster['aws']['sts']['operator_iam_roles']:
        roles.append(role['role_arn'].split("/")[1])
    for role in roles:
        print(
            "-> deleting cluster {0} operator role {1}".format(cluster['name'], role))
        policies = iam.list_attached_role_policies(RoleName=role)
        for policy in policies['AttachedPolicies']:
            iam.detach_role_policy(
                RoleName=role, PolicyArn=policy['PolicyArn'])
        iam.delete_role(RoleName=role)


def delete_oidc_endpoint(cluster, iam):
    oidcProvider = cluster['aws']['sts']['oidc_endpoint_url'].replace(
        "https://", "")
    for arn in iam.list_open_id_connect_providers()['OpenIDConnectProviderList']:
        if oidcProvider in arn['Arn']:
            print(
                "-> deleting cluster oidc provider {0} with arn {1}".format(oidcProvider, arn['Arn']))
            iam.delete_open_id_connect_provider(
                OpenIDConnectProviderArn=arn['Arn'])
            return
    raise RuntimeError("Can not fine the oidc arn")


# get list of clusters
iam = boto3.client('iam')
session = requests.Session()
session.headers.update({'Authorization': 'Bearer {0}'.format(get_token())})

clusters = list_clusters(session)

old, new = clusters_older_than_today(clusters)

for cluster in new:
    if cluster['name'] in DELETE_NEW_CLUSTERS:
        delete_cluster(session, cluster)
    else:
        print("-> skipping cluster {0}, it is new ".format(cluster['name']))

for cluster in old:
    print("-> delete expired cluster {0}".format(cluster['name']))
    delete_cluster(session, cluster)
