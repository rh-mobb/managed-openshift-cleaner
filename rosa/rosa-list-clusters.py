#!/bin/env python3

import requests
from requests_oauthlib import OAuth2Session
import json
from pathlib import Path
import pprint
import datetime
from dateparser import parse
import os

pp = pprint.PrettyPrinter(indent=4)

API='https://api.openshift.com/api/clusters_mgmt/v1'
SKIP_CLUSTERS = ['mobb-infra', os.getenv('SKIP_CLUSTERS','').split(",")]
DELETE = os.getenv('DELETE', False)
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
  for cluster in response.json()['items']:
    if cluster['name'] not in SKIP_CLUSTERS and not cluster['name'].startswith('poc-'):
      clusters.append(cluster)
    else:
      print("-> skipping {0}".format(cluster['name']))
  return clusters

def describe_cluster(session, id):
  response = session.get("{0}/clusters/{1}".format(API,id))
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

def delete_cluster(session, cluster):
  if DELETE:
    print("-> deleting cluster {0}".format(cluster['name']))
    response = session.delete("{0}/clusters/{1}".format(API,cluster['id']))
    if response.status_code == 204:
      return True
    else:
      print("-> failed to delete cluster {0}".format(cluster['name']))
      pp.pprint(response.json())
      return False
  else:
    print("-> pretending to delete cluster {0}".format(cluster['name']))
    return True



# get list of clusters

session = requests.Session()
session.headers.update({'Authorization': 'Bearer {0}'.format(get_token())})

clusters = list_clusters(session)

old, new = clusters_older_than_today(clusters)

for cluster in old:
      delete_cluster(session, cluster)
