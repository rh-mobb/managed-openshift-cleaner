#!/bin/env python3

import boto3
import datetime
from re import search

clusters = []

ec2 = boto3.resource('ec2')
today = datetime.date.today()
for instance in ec2.instances.all():
    if today > instance.launch_time.date():
      for tag in instance.tags:
        if "kubernetes.io/cluster/" in tag['Key'] and instance.state['Code'] == 16:
          cluster_name = search(r'^kubernetes.io\/cluster\/(.*)-.*$', tag['Key']).group(1)
          if not cluster_name in clusters:
            clusters.append(cluster_name)
            print(
                "{0} ({1})\n".format(
                cluster_name, instance.launch_time
                )
            )