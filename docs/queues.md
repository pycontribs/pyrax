# Queues

## Basic Concepts
Queues is an open source, scalable, and highly available message and notifications service, based on the OpenStack Marconi project. Users of this service can create and manage a producer-consumer or a publisher-subscriber model. Unlimited queues and messages give users the flexibility they need to create powerful web applications in the cloud.

It consists of a few basic components: queues, messages, claims, and statistics. In the producer-consumer model, users create queues in which producers, or servers, can post messages. Workers, or consumers, can then claim those messages and delete them after they complete the actions associated with the messages. A single claim can contain multiple messages, and administrators can query claims for status.

In the publisher-subscriber model, messages are posted to a queue as in the producer-consumer model, but messages are never claimed. Instead, subscribers, or watchers, send GET requests to pull all messages that have been posted since their last request. In this model, a message remains in the queue, unclaimed, until the message's time to live (TTL) has expired.

In both of these models, administrators can get queue statistics that display the most recent and oldest messages, the number of unclaimed messages, and more.


## Using Queues in pyrax
Once you have authenticated, you can reference the Queues service via `pyrax.queues`. To make your coding easier, include the following line at the beginning of your code:

    pq = pyrax.queues

Then you can simply use the alias `pq` to reference the service. All of the code samples in this document assume that `pq` has been defined this way.


# Client ID
Cloud Queues requires that every client accessing queues have a unique **Client ID**. This Client ID must be a UUID string in its canonical form. Example: "3381af92-2b9e-11e3-b191-71861300734c".

If you aren't familiar with UUIDs, Python provides a module in the Standard Library for working with them. Here is the code for creating a UUID string compatible with Cloud Queues:

    import uuid
    my_client_id = str(uuid.uuid4())

Once you have your ID, you need to make it available to pyrax. There are two ways: 

1) After authenticating, but before calling any Cloud Queues methods, set it directly:

    pq.client_id = my_client_id

2) Export it to an environment variable named `CLOUD_QUEUES_ID`, either in your .bashrc, or by doing it explicitly:

    export CLOUD_QUEUES_ID='3381af92-2b9e-11e3-b191-71861300734c'

If you try to use any of the Cloud Queues methods without setting this value, a `QueueClientIDNotDefined` exception is raised.


## Creating a Queue
Queues require a unique name. If you try to create a queue with a name that already exists, a `DuplicateQueue` exception is raised. The command to create a queue is:

    queue = pq.create("my_unique_queue")

If you wish to check a given queue already exists, you may do so as follows:

    exists = pq.queue_exists("name_to_check")

This call returns `True` or `False`, depending on the existence of a queue with the given name.

## Listing queues
The code below shows how you can list all the queues in a given region:

    qs = pyrax.queues.list()

## Posting a Message to a Queue
Messages can be any type of data, as long as they do not exceed 256 KB in length. The message body can be simple values, or a chunk of XML, or a list of JSON values, or anything else. pyrax handles the JSON-encoding required to post the message.

You need to specify the queue you wish to post to. This can be either the name of the queue, or a `Queue` object. If you already have a `Queue` object reference, you can call its `post_message()` method directly. The call is:

    msg = pq.post_message(queue, body, ttl)
    # or
    msg = queue.post_message(body, ttl)

You must supply both a body and a value for `ttl`. The value of `ttl` must be between 60 and 1209600 seconds (one minute to 14 days).


## Listing Messages in a Queue
To get a listing of messages in a queue, you need the queue name or a `Queue` object reference. If you have a `Queue` object, you can call its `list()` method directly. The call is:

    msgs = pq.list_messages(queue[, echo=False][, include_claimed=False]
            [, marker=None][, limit=None])
    # or
    msgs = queue.list([echo=False][, include_claimed=False]
            [, marker=None][, limit=None])

The optional parameters and their effects are:

Parameter | Default | Effect
---- | ---- | ----
**echo** | False | When True, your own messages are included.
**include_claimed** | False | By default, only unclaimed messages are returned. Pass this as True to get all messages, claimed or not.
**marker** | None | Used for pagination. Normally this should not be needed, as the `list()` methods handle this for you.
**limit** | 10 | The maximum number of messages to return. Note that you may receive fewer than the specified limit if there aren't that many available messages in the queue.


## Claiming Messages in a Queue
Claiming messages is how workers processing a queue mark messages as being handled by that worker, avoiding having two workers process the same message.

To claim messages you need the queue name or a `Queue` object reference. If you have a `Queue` object, you can call its `claim_messages()` method directly. When claiming messages you must not only specify the queue, but also give a TTL and a Grace Period. You may also specify a limit to the number of messages to claim. The call is:

    queue_claim = pq.claim_messages(queue, ttl, grace[, count])
    
    queue_claim = queue.claim_messages(ttl, grace[, count])

An explanation of the parameters of this call follows:

Parameter | Default | Notes
---- | ---- | ----
**queue** |  | Either the name of the queue to claim messages from, or the corresponding `Queue` object.
**ttl** |  | The ttl attribute specifies how long the server waits before releasing the claim. The ttl value must be between 60 and 43200 seconds (12 hours).
**grace** |  | The grace attribute specifies the message grace period in seconds. The value of the grace period must be between 60 and 43200 seconds (12 hours). To deal with workers that have stopped responding (for up to 1209600 seconds or 14 days, including claim lifetime), the server extends the lifetime of claimed messages to be at least as long as the lifetime of the claim itself, plus the specified grace period. If a claimed message would normally live longer than the grace period, its expiration is not adjusted.
**count** | 10 | The number of messages to claim. The maximum number of messages you may claim at once is 20.

If there are no messages to claim, the method returns `None`. When you create a successful claim, a `QueueClaim` object is returned that has a `messages` attribute. This is a list of `QueueMessage` objects representing the claimed messages. You can iterate through this list to process the messages, and once the message has been processed, call its `delete()` method to remove it from the queue to ensure that it is not processed more than once.


## Renewing a Claim
Once a claim has been made, if the TTL and grace period expire, the claim is automatically released and the messages are made available for others to claim. If you have a long-running process and want to ensure that this does not happen in the middle of the process, you should update the claim with one or both of a TTL or grace period. Updating resets the age of the claim, restarting the TTL for the claim. To update a claim, call:

    pq.update_claim(queue, claim[, ttl=None][, grace=None])
    # or
    queue.update_claim(claim[, ttl=None][, grace=None])


## Refreshing a Claim
If you have a `QueueClaim` object, keep in mind that it is not a live window into the status of the claim; rather, it is a snapshot of the claim at the time the object was created. To refresh it with the latest information, call its `reload()` method. This refreshes all of its attributes with the most current status of the claim.


## Releasing a Claim
If you have a claim on several messages and must abandon processing of those messages for any reason, you should release the claim so that those messages can be processed by other workers as soon as possible, instead of waiting for the claim's TTL to expire. When you release a claim, the claimed messages are immediately made available in the queue for other workers to claim. To release a claim, call:

    pq.release_claim(queue, claim)
    # or
    queue.release_claim(claim)


