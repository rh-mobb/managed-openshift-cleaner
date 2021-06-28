# Image Build Pipeline

Create a namespace

```
kubectl create ns rosa-cleaner
```

Create a secret for gitlab credentials

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

Link that secret to the pipeline builder user

```
oc secret link pipeline gitlab-rosa-cleaner-auth
```

Create the tekton pipeline

```
k apply -f k8s/pipeline.yaml
```

Test the pipeline

```
k apply -f k8s/pipeline-run.yaml
```

Create the build trigger

```
k apply -f k8s/trigger.yaml
```