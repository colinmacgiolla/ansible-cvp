# Arista Ansible-CVP Example Playbooks
This section contains a set of example playbooks, with any associated notes.
## Playbooks
### [01 - Change Control Example](./01-change-control-example.yaml)
This playbook assumes that you have 2 pending tasks, "21" and "22" to be executed, and that you want to perform a health check before execution.

The health checks will be performed in parallel, in a `Pre-Checks` stage, with the following `Upgrades` state containing 2 further sub-stages, one for each of the devices, executed serially.

`SERIAL_NUMBER` should be replaced with the actual serial number of the devices in question.

## [02 - Image Bundle Creation Example](./02-image-bundle-creation.yaml)
This playbook uploads a new vEOS-lab image and TerminAttr image, and bundles them together into an image bundle named `spine_bundle`.

If the named bundle already exists, the contents of the bundle is updated to include those images provided in the `image_list`.

## [03 - Create Spine Change Control](./03-create-spine-upgrade-cc.yaml)
This playbook assumes two things;
1. There are pending tasks to upgrade the image
2. The word 'spine' is in the hostname

It will perform the following steps;
1. Find the pending image push tasks, where the hostname contains the word `SPINE`
2. Create a Pre-Checks stage, to be executed in parallel, over all the spines.
3. Create an `Upgrades` parent stage, and sub-stages (one for each spine switch), to be executed serially. This means that, regardless of the number of spines, we will only upgrade one at a time.