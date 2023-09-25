
# ROSA Cleaner in stand alone

## Prerequisites

* AWS CLI configured
* OCM.json is in the home path
* Python installed

## what does [rosa-cleaner.py](./rosa-cleaner.py) do

* The cleaner deletes rosa cluster through red hat cluster manager
* The cleaner cleans up the oidc connector provider and sts roles
* By Default it only cleans up the clusters deployed yesterday

### How to run

* By Default it is doing dry run

```
python rosa-cleaner.py
```

* Enable Delete

```
DELETE="1" python rosa-cleaner.py
```

* Delete New Cluster as well

```
DELETE_NEW_CLUSTERS=[CLUSTER_NAME] DELETE="1" python rosa-cleaner.py
```

* Skip Certain Clusters

```
SKIP_CLUSTERS=[CLUSTER_NAME] DELETE="1" python rosa-cleaner.py
```

## what does [orphan-iam-cleaner.py](./orphan-iam-cleaner.py) do

In case the a rosa cluster were deleted, but the sts roles and oidc connector deletion failed.
This scripts deletes rosa roles and oidc providers, which does not belong to any mobb rosa clusters.

Always dry run first
```
python orphan-iam-cleaner.py
```

Enable delete action
```
DELETE='1' python orphan-iam-cleaner.py python orphan-iam-cleaner.py
```

# ROSA Cleaner In the pipeline

## Prerequisites

* ROSA Cluster
* RedHat Pipelines

## Image Build Pipeline

1. Create a namespace

    ```
    oc new-project rosa-cleaner
    ```

1. Create a secret for AWS credentials (user rosa-cleaner)

    ```
    oc create secret generic aws-iam-cleaner-secret \
      --from-literal=aws_access_key_id=<AWS_ACCESS_KEY_ID> \
      --from-literal=aws_secret_access_key=<AWS_SECRET_ACCESS_KEY>
    ```

2. Create a secret for OCM credentials

    ```
    oc create secret generic openshift-cluster-manager-credentials \
      --from-file=$HOME/.config/ocm/ocm.json
    ```

3. Patch the openshift-client clusterTask

    ```
    oc patch clustertask openshift-client --type=merge \
      -p='{"spec":{"workspaces":[{"name":"source"}]}}'
    ```

4. Create the tekton pipeline

    ```
    oc apply -f pipelines/pipeline.yaml
    ```

5. Test the Pipeline

    ```
    oc apply -f pipelines/pipeline-run.yaml
    ```

6. Create the build trigger

    ```
    oc apply -f pipelines/trigger.yaml
    ```
