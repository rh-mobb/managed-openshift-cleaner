
# ROSA Cleaner in stand alone

## Prerequisites

* AWS CLI configured
* OCM.json is in the home path
* Python installed

## what does [rolsa-cleaner.py](./rosa-cleaner.py) do

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

* Skip Certian Clusters

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

1. Create a secret for gitlab credentials (create a gitlab auth token for the repo) and save them as Env Variables

   ```
   export GL_USERNAME=osd-cleaner
   export GL_PASSWORD=<token>
   ```


   ```
cat << EOF | kubectl apply -f -
apiVersion: v1
kind: Secret
type: kubernetes.io/basic-auth
metadata:
  annotations:
    tekton.dev/git-0: https://gitlab.consulting.redhat.com/
  name: gitlab-rosa-cleaner-auth
  namespace: rosa-cleaner
stringData:
  password: $GL_USERNAME
  username: $GL_PASSWORD
EOF
   ```

1. Create a secret for gitlab tekton credentials

   ```
cat << EOF | kubectl apply -f -
kind: Secret
apiVersion: v1
metadata:
  name: gitlab-rosa-cleaner-clone-auth
type: Opaque
stringData:
  .gitconfig: |
    [credential]
      helper = store
    [credential "https://gitlab.consulting.redhat.com"]
      username = $GL_USERNAME
  .git-credentials: |
    https://$GL_USERNAME:$GL_PASSWORD@gitlab.consulting.redhat.com
EOF
   ```

1. Create a secret for OCM credentials

    ```
    kubectl create secret generic openshift-cluster-manager-credentials \
      --from-file=$HOME/.config/ocm/ocm.json

1. Link that secret to the pipeline builder user

    ```
    oc secret link pipeline gitlab-rosa-cleaner-auth
    ```

1. Patch the openshift-client clusterTask

    ```
    oc patch clustertask openshift-client --type=merge \
      -p='{"spec":{"workspaces":[{"name":"source"}]}}'
    ```

1. Create the tekton pipeline

    ```
    oc apply -f pipelines/pipeline.yaml
    ```

1. Test the Pipeline

    ```
    oc apply -f pipelines/pipeline-run.yaml
    ```

1. Create the build trigger

    ```
    oc apply -f pipelines/trigger.yaml
    ```
