#!/bin/env python3

API='https://api.openshift.com/api/clusters_mgmt/v1'

import requests
from requests_oauthlib import OAuth2Session
import json
from pathlib import Path
import pprint
import datetime
from dateparser import parse

pp = pprint.PrettyPrinter(indent=4)


# print(access_token)

def get_token():
  home = str(Path.home())

  f = open(home + "/.ocm.json",)
  user = json.load(f)

  auth = (user['client_id'], user['access_token'])

  params = {
    "grant_type": "refresh_token",
    "refresh_token": user['refresh_token']
  }

  response = requests.post(user['token_url'], auth=auth, data=params)

  return response.json()['access_token']


def list_clusters(session):
  response = session.get(API + "/clusters/")
  return response.json()['items']

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


# get list of clusters

# access_token = get_token()

session = requests.Session()
session.headers.update({'Authorization': 'Bearer {0}'.format(get_token())})

clusters = list_clusters(session)

old, new = clusters_older_than_today(clusters)

for cluster in old:
  # /api/clusters_mgmt/v1/clusters/{cluster_id}
  # if cluster['name'] == "ca14a1be-83b1-432c-af8a-7ec4a20c56c0":

    # desc = describe_cluster(session, cluster['id'])
    pp.pprint(cluster)
    break