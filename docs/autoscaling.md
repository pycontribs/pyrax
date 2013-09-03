# Autoscaling

## Basic Concepts
Autoscale is a service that enables you to scale your application by adding or removing servers based on monitoring events, a schedule, or arbitrary webhooks.

Please note that _this is a Rackspace-specific service_. It is not available in any other OpenStack cloud, so if you add it to your application, keep the code isolated if you need to run your application on non-Rackspace clouds.

Autoscale functions by linking three services:

* Monitoring (such as Monitoring as a Service)
* Autoscale API
* Servers and Load Balancers


## Workflow

An Autoscaling group is monitored by Rackspace Cloud Monitoring. When Monitoring triggers an alarm for high utilization within the Autoscaling group, a webhook is triggered. The webhook calls the autoscale service, which consults a policy in accordance with the webhook. The policy determines how many additional Cloud Servers should be added or removed in accordance with the alarm.

Alarms may trigger scaling up or scaling down. Scale down events always remove the oldest server in the group.

Cooldowns allow you to ensure that you don't scale up or down too fast. When a scaling policy runs, both the scaling policy cooldown and the group cooldown start. Any additional requests to the group are discarded while the group cooldown is active. Any additional requests to the specific policy are discarded when the policy cooldown is active.

It is important to remember that Autoscale does not configure anything within a server. This means that all images should be self-provisioning. It is up to you to make sure that your services are configured to function properly when the server is started. We recommend using something like Chef, Salt, or Puppet.


## Using Autoscaling in pyrax
Once you have authenticated, you can reference the Autoscaling service via `pyrax.autoscaling`. That is a lot to type over and over in your code, so it is easier if you include the following line at the beginning of your code:

    au = pyrax.autoscaling

Then you can simply use the alias `au` to reference the service. All of the code samples in this document assume that `au` has been defined this way.


## The Scaling Group
The **Scaling Group** is the basic unit of Autoscaling. It determines the minimum and maximum number of servers that exist at any time for the group, the cooldown period between Autoscaling events, the configuration for each new server, the load balancer to add these servers to (optional), and any policies that are used for this group.

### Listing Your Scaling Groups
The `list()` method displays all the Scaling Groups currently defined in your account:

    print au.list()

This returns a list of `ScalingGroup` objects:

    [<ScalingGroup activeCapacity=3, desiredCapacity=3,
    id=2747cd20-39cb-443d-9217-53107775ba37, paused=False,
    pendingCapacity=0, name=FirstTest, cooldown=120, metadata={},
    min_entities=1, max_entities=4>,
    <ScalingGroup activeCapacity=2, desiredCapacity=2,
    id=76ee2de8-4df2-4664-b55c-60d0edd5dff8, paused=False,
    pendingCapacity=0, name=SecondTest, cooldown=90, metadata={},
    min_entities=2, max_entities=5>]

To see the [launch configuration](#launch-configuration) for a group, call the `get_launch_config()` method:

    groups = au.list()
    group = groups[0]
    print group.get_launch_config()

This returns a dict with the current values for its launch configuration:

    {'disk_config': u'AUTO',
     'flavor': 2,
     'image': u'7789e8ca-b9df-495f-b47d-736a5f7b885a',
     'load_balancers': [{u'loadBalancerId': 175295, u'port': 80}],
     'metadata': {u'somekey': u'somevalue'},
     'name': u'rrr',
     'networks': [{u'uuid': u'11111111-1111-1111-1111-111111111111'}],
     'personality': [],
     'type': u'launch_server'}

### Getting the Current State of a Scaling Group
It is sometimes helpful to determine what the current state of a scaling group is in terms of whether it is scaling up, scaling down, or stable. To do this, call the scaling group's `get_state()` method, or call the client's `get_state()`, passing in the desired scaling group:

    print sg.get_state()
    # or
    print au.get_state(sg)

This returns a dict with the following structure:

    {'active': [u'21d0bce0-c7b9-46f8-80a2-9575bef8b83a', u'3e2c9eac-d7c2-4999-9a17-a6a7ca5d10e7'],
    'desired_capacity': 2,
    'paused': False,
    'pending_capacity': 0,
    'active_capacity': 2}

The `active` key holds a list of the IDs of the servers created as part of this scaling group. The `paused` key shows whether or not the scaling group's response to alarms is active or not. There are 3 'capacity'-related keys: `active_capacity`, `desired_capacity`, and `pending_capacity`:

Key | Respresents
---- | ----
**active_capacity** | The number of active servers that are part of this scaling group
**desired_capacity** | The target number of servers for this scaling group, based on the combination of configuration settings and monitoring alarm responses
**pending_capacity** | The number of servers which are in the process of being created (when positive) or destroyed (when negative).

### Pausing a Scaling Group's Policies
If you wish to pause the execution of a scaling group's policies for any reason, call its `pause()` method, or the `pause()` method of the client:

    sg.pause()
    # or
    au.pause(sg)

There is a corresponding `resume()` method for when you want to re-activate the policies:

    sg.resume()
    # or
    au.resume(sg)

### Creating a Scaling Group
To create a scaling group, you call the `create()` method of the client with the desired parameter values:

    sg = au.create("MyScalingGroup", cooldown=120, min_entities=2,
            max_entities=16, launch_config_type="launch_server",
            server_name="sg_test", flavor=3, image=my_image_id,
            disk_config="AUTO", metadata={"mykey": "myvalue"},
            load_balancers=(1234, 80))

This creates the Scaling Group with the name "MyScalingGroup", and returns a `ScalingGroup` object representing the new group. Since the `min_entities` is 2, it immediately creates 2 servers for the group, based on the image whose ID is in the variable `my_image_id`. When they are created, they are then added to the load balancer whose ID is `1234`, and receive requests on port 80.

Note that the `server_name` parameter represents a base string to which Autoscale prepends a 10-character prefix to create a unique name for each server. The prefix always begins with 'as' and is followed by 8 random hex digits. For example, if you set the server_name to 'testgroup', and the scaling group creates 3 servers, their names would look like these:

    as5defddd4-testgroup
    as92e512fe-testgroup
    asedcf7587-testgroup

#### Parameters
Parameter | Required | Default | Notes
---- | ---- | ---- | ----
**name** | yes |  |
**cooldown** | yes |  | Period in seconds after a scaling event in which further events are ignored
**min_entities** | yes |  |
**max_entities** | yes |  |
**launch_config_type** | yes |  | Only option currently is`launch_server`
**flavor** | yes |  | Flavor to use for each server that is launched
**server_name** | yes |  | The base name for servers created by Autoscale.
**image** | yes |  | Either a Cloud Servers Image object, or its ID. This is the image that all new servers are created from.
**disk_config** | no | MANUAL | Determines if the server's disk is partitioned to the full size of the flavor ('AUTO') or just to the size of the image ('MANUAL').
**metadata** | no |  | Arbitrary key-value pairs you want to associate with your servers.
**personality** | no |  | Small text files that are created on the new servers. _Personality_ is discussed in the [Rackspace Cloud Servers documentation](http://docs.rackspace.com/servers/api/v2/cs-devguide/content/Server_Personality-d1e2543.html)
**networks** | no |  | The networks to which you want to attach new servers. See the [Create Servers documentation](http://docs.rackspace.com/servers/api/v2/cs-devguide/content/CreateServers.html) for the required format.
**load_balancers** | no |  | Either a  list of (id, port) tuples or a single such tuple, representing the loadbalancer(s) to add the new servers to.
**scaling_policies** | no |  | You can define the scaling policies when you create the group, or add them later.

### Updating a Scaling Group
You can modify the settings for a scaling group by calling its `update()` method. The available settings you may change are: `name`, `cooldown`, `min_entities`, `max_entities`, and `metadata`. To update a scaling group, pass one or more of these as keyword arguments. For example, to change the cooldown period to 2 minutes and increase the maximum entities to 16, you call:

    sg.update(cooldown=120,  max_entities=16)

where `sg` is a reference to the scaling group. Similarly, you can make the call on the autoscale client itself, passing in the reference to the scaling group you wish to update:

    au.update(sg, cooldown=120,  max_entities=16)

**Note**: If you pass any metadata values in this call, it must be the full set of metadata for the Scaling Group, since the underlying API call **overwrites** any existing metadata. If you simply wish to update an existing metadata key, or add a new key/value pair, you must call the `update_metadata(new_meta)` method instead. This call preserves your existing key/value pairs, and only updates it with your changes.

### Deleting a Scaling Group
To remove a scaling group, call its `delete()` method:

    sg.delete()

You can also call the `delete()` method of the client itself, passing in the scaling group to delete:

    au.delete(sg)

Note: you cannot delete a scaling group that has active servers in it. You must first delete the servers by setting the `min_entities` and `max_entities` to zero:

    sg.update(min_entities=0, max_entities=0)

Once the servers are deleted you can then delete the scaling group.


## Launch Configurations
Each scaling group has an associated **launch configuration**. This determines the properties of servers that are created in response to a scaling event.

The `server_name` represents a base string to which Autoscale prepends a 10-character prefix. The prefix always begins with 'as' and is followed by 8 random hex digits. For example, if you set the `server_name` to 'testgroup', and the scaling group creates 3 servers, their names would look like these:

    as5defddd4-testgroup
    as92e512fe-testgroup
    asedcf7587-testgroup    

To see the launch configuration for a given scaling group, call:

    sg.get_launch_config()
    # or
    au.get_launch_config(sg)

### Updating the Launch Configuration
You can also modify the launch configuration for your scaling group by calling the `update_launch_config()` method. This method lets you update any of the following setttings: `server_name`, `flavor`, `image`, `disk_config`, `metadata`, `personality`, `networks`, `load_balancers`. You may update one or more of these parameters in the call. For example, to change the scaling group to use a different image, call:

    sg.update_launch_config(image=new_image_id)

You may also make the call on the autoscale client itself, passing in the scaling group you want to modify:

    au.update_launch_config(sg, image=new_image_id)

**Note**: If you pass any metadata values in this call, it must be the full set of metadata for the Launch Configuration, since the underlying API call **overwrites** any existing metadata. If you simply wish to update an existing metadata key in your launch configuration, or add a new key/value pair, you must call the `update_launch_metadata()` method instead. This call preserves your existing key/value pairs, and only updates with your changes.


## Policies
When an alarm is triggered in Cloud Monitoring, it calls the webhook associated with a particular policy. The policy is designed to update the scaling group to increase or decrease the number of servers in response to the particular alarm.

To list the policies for a given scaling group, call its `list_policies()` method:

    policies = sg.list_policies()

You can also call this directly on the client, passing in the scaling group for which you want to get a list of its policies:

    policies = au.list_policies(sg)

### Creating a Policy
To add a policy to a scaling group, call the `add_policy()` method:

    policy = sg.add_policy(name, policy_type, cooldown,
            change, is_percent)
    # or
    policy = au.add_policy(sg, name, policy_type, cooldown,
            change, is_percent)

#### Parameters
Parameter | Required | Default | Notes
---- | ---- | ---- | ----
**name** | yes |  |
**policy_type** | yes | | Only available type now is 'webhook'
**cooldown** | yes |  | Period in seconds after a policy execution in which further events are ignored. This is separate from the overall cooldown for the scaling group.
**change** | yes | | Can be positive or negative, which makes this a scale-up or scale-down policy, respectively.
**is_percent** | no | False | Determines whether the value passed in the `change` parameter is interpreted an absolute number, or a percentage.

### Updating a Policy
You may update a policy at any time, passing in any or all of the above parameters to change that value. For example, to change the cooldown to 60 seconds, and the number of servers to remove to 3, call:

    policy.update(cooldown=60, change=-3)

You may also call the `update_policy()` method of either the scaling group for this policy, or the autoscale client itself. Either of the following two calls is equivalent to the call above:

    sg.update_policy(policy, cooldown=60, change=-3)
    # or
    au.update_policy(sg, policy, cooldown=60, change=-3)

### Executing a Policy
You don't need to wait for an alarm to be triggered in Cloud Monitoring in order to execute a particular policy. If desired, you may do so manually by calling the policy's `execute()` method:

    policy.execute()

You can also call the execute_policy() method of either the policy's scaling group, or on the client itself:

    sg.execute_policy(policy)
    # or
    au.execute_policy(sg, policy)

### Deleting a Policy
To remove a policy, call its `delete()` method:

    policy.delete()

You can also call the delete_policy() method of either the policy's scaling group or on the client itself:

    sg.delete_policy(policy)
    # or
    au.delete_policy(sg, policy)


## Webhooks
When an alarm is triggered in Cloud Monitoring, it calls the associated webhook, which in turn causes the policy for that webhook to be executed.

To list the webhooks for a given policy, call its `list_webhooks()` method:

    webhooks = policy.list_webhooks()

You can also call this directly on either the scaling group or the client, passing in the policy for which you want the list of webhooks:

    webhooks = sg.list_webhooks(policy)
    # or
    webhooks = au.list_webhooks(sg, policy)

### Creating a webhook
To add a webhook to a policy, call the `add_webhook()` method:

    webhook = policy.add_webhook(name, metadata)
    # or
    webhook = sg.add_webhook(policy, name, metadata)
    # or
    webhook = au.add_webhook(sg, policy, name, metadata)

The `name` parameter is required; the `metadata` parameter is optional.

### Updating a webhook
You may update a webhook at any time to change either its name or its metadata:

    webhook.update(name="something_new",
            metadata={"owner": "webteam"})

You may also call the `update_webhook()` method of either the policy for this webhook, or the scaling group for that policy, or the autoscale client itself. Any of the following calls is equivalent to the call above:

    policy.update_webhook(webhook, name="something_new",
            metadata={"owner": "webteam"})
    # or
    sg.update_webhook(policy, webhook, name="something_new",
            metadata={"owner": "webteam"})
    # or
    au.update_webhook(sg, policy, webhook, name="something_new",
            metadata={"owner": "webteam"})

**Note**: If you pass any metadata values in this call, it must be the full set of metadata for the Webhook, since the underlying API call **overwrites** any existing metadata. If you simply wish to update an existing metadata key, or add a new key/value pair, you must call the `webhook.update_metadata(new_meta)` method instead (or the corresponding `au.update_webhook_metadata(sg, policy, webhook, new_meta)`). This call preserves your existing key/value pairs, and only updates it with your changes.

### Deleting a webhook
When you wish to remove a webhook, call its `delete()` method:

    webhook.delete()

You can also call the `delete_webhook()` method of the webhook's policy, or the policy's scaling group, or on the client itself:

    policy.delete_webhook(webhook)
    # or
    sg.delete_webhook(policy, webhook)
    # or
    au.delete_webhook(sg, policy, webhook)








