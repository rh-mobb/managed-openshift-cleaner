# ROSA Cleaner

# Image Build Pipeline

1. Create a namespace

    ```
    kubectl create ns rosa-cleaner
    ```

1. Create a secret for gitlab credentials

    ```
    cat << EOF | kubectl apply -f
    apiVersion: v1
    kind: Secret
    type: kubernetes.io/basic-auth
    metadata:
      annotations:
        tekton.dev/git-0: https://gitlab.consulting.redhat.com/
      name: gitlab-rosa-cleaner-auth
      namespace: rosa-cleaner
    stringData:
      password: <username>
      username: <password>
    EOF
    ```

1. Create a secret for OCM credentials

    ```
    kubectl create secret generic openshift-cluster-manager-credentials \
      --from-file=$HOME/.ocm.json

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
    k apply -f k8s/pipeline.yaml
    ```

1. Test the Pipeline

    ```
    k apply -f k8s/pipeline-run.yaml
    ```

1. Create the build trigger

    ```
    k apply -f k8s/trigger.yaml
    ```