## Issue

The normal flow with tekton trigger is to:

* Create event listener
* Configure github/gitlab webhook to trigger the pipeline

The event listener needs to be a public URL that github/gitlab can push event through webhook. 

However, gitlab.consulting.redhat.com has a rigid egress ACL that requires firewall ticket.

## Solution

* We created a [gitlab polling operator](https://gitlab.consulting.redhat.com/mobb/tekton-polling-operator) instead of using event listener
