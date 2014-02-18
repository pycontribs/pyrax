# Cloud Monitoring

## Basic Concepts
Rackspace Cloud Monitoring provides timely and accurate information about how your resources are performing. It supplies you with key information that can help you manage your business by enabling you to keep track of your cloud resources and receive instant notification when a resource needs your attention. You can quickly create multiple monitors with predefined checks, such as PING, HTTPS, SMTP, and many others.

## Monitoring in pyrax
Once you have authenticated, you can reference the monitoring service via `pyrax.cloud_monitoring`. You interact with Cloud Monitoring through this object.

For the sake of brevity and convenience, it is common to define abbreviated aliases for the modules. All the code in this document assumes that you have added the following line at the top of your script:

    cm = pyrax.cloud_monitoring

Note that as of this writing, pyrax only supports **remote monitoring**. There is a second type of monitoring that is currently in Preview mode that uses a *Monitoring Agent* installed on your device.


## Key Terminology
### Entity
In Rackspace Cloud Monitoring, an entity is the object or resource that you want to monitor. It can be any object or device that you want to monitor. It is commonly a web server, but it might also be a website, a web page, or a web service.

When you create an entity, you will specify characteristics that describe what you are monitoring. At a minimum you must specify a name for the entity. The name is a user-friendly label or description that helps you identify the resource. You can also specify other attributes of the entity, such the entity's IP address, and any metadata that you'd like to associate with the entity.

### Check
Once you've created an entity, you can configure one or more checks for it. A check is the building block of the monitoring system, and is always associated with an entity. The check specifies the parts or pieces of the entity that you want to monitor, the monitoring frequency, how many monitoring zones are launching the check, and so on. Basically, it contains the specific details of how you are monitoring the entity.

You can associate one or more checks with an entity. An entity must have at least one check, but by creating multiple checks for an entity, you can monitor several different aspects of a single resource.

For each check you create within the monitoring system, you'll designate a check type. The check type tells the monitoring system which method to use, such as PING, HTTP, SMTP, and so on, when investigating the monitored resource. Rackspace Cloud Monitoring check types are fully described [here](http://docs.rackspace.com/cm/api/v1.0/cm-devguide/content/appendix-check-types.html).

Note that if something happens to your resource, the check does not trigger a notification action. Rather, the alarms that you create separately and associate with the check trigger the notifications.

### Monitoring Zones
When you create a check, you specify which monitoring zone(s) you want to launch the check from. A monitoring zone is the point of origin, or "launch point", of the check. This concept of a monitoring zone is similar to that of a datacenter, however in the monitoring system, you can think of it more as a geographical region.

You can launch checks for a particular entity from multiple monitoring zones. This allows you to observe the performance of an entity from different regions of the world. It is also a way to prevent false alarms. For example, if the check from one monitoring zone reports that an entity is down, a second or third monitoring zone might report that the entity is up and running. This gives you a better picture of an entity's overall health.

### Collectors
A collector collects data from the monitoring zone and is mapped directly to an individual machine or a virtual machine. Monitoring zones contain many collectors, all of which will be within the IP address range listed in the response. Note that there may also be unallocated IP addresses or unrelated machines within that IP address range.

### Monitoring Agent
Note: The Monitoring Agent is a Preview feature.

The agent provides insight into the internals of your servers with checks for information such as load average and network usage. The agent runs as a single small service that runs scheduled checks and pushes metrics to the rest of Cloud Monitoring so the metrics can be analyzed, alerted on, and archived. These metrics are gathered via checks using agent check types, and can be used with the other Cloud Monitoring primitives such as alarms. See Section B.2, “[Agent Check Types](http://docs.rackspace.com/cm/api/v1.0/cm-devguide/content/appendix-check-types-agent.html)” for a list of agent check types.

### Alarms
An alarm contains a set of rules that determine when the monitoring system sends a notification. You can create multiple alarms for the different check types associated with an entity. For example, if your entity is a web server that hosts your company's website, you can create one alarm to monitor the server itself, and another alarm to monitor the website.

The alarms language provides you with scoping parameters that let you pinpoint the value that will trigger the alarm. The scoping parameters are inherently flexible, so that you can set up multiple checks to trigger a single alarm. The alarm language supplies an adaptable triggering system that makes it easy for you to define different formulas for each alarm that monitors an entity's uptime. To learn how to use the alarm language to create robust monitors, see [Alert Triggering and Alarms](http://docs.rackspace.com/cm/api/v1.0/cm-devguide/content/alerts-language.html).

### Notifications
A notification is an informational message that you receive from the monitoring system when an alarm is triggered. You can set up notifications to alert a single individual or an entire team. Rackspace Cloud Monitoring currently supports calling webhooks, sending email, and the PagerDuty web service for notifications.

### Notification Plans
A notification plan contains a set of notification rules to execute when an alarm is triggered. A notification plan can contain multiple notifications for each of the following states:

* Critical
* Warning
* OK


## How Cloud Monitoring Works
Cloud Monitoring helps you keep a keen eye on all of your resources, from web sites to web servers, routers, load balancers, and more. Use the following Monitoring workflow:

* Create an entity to represent the item you want to monitor. For example, the entity might represent a web site.
* Attach a predefined check to the entity. For example, you could use the PING check to monitor your web site's public IP address.
* Run your checks from multiple monitoring zones to provide redundant monitoring as well as voting logic to avoid false alarms.
* Create a notification to define an action that Cloud Monitoring uses to communicate with you when a problem occurs. For example, you might define a notification that specifies an email that Cloud Monitoring will send when a condition is met.
* Create notification plans which allow you to organize a set of several notifications, or actions, that are taken for different severities.
* Define one or more alarms for each check. An alarm lets you specify trigger conditions for the various metrics returned by the check. When a specific condition is met, the alarm is triggered and your notification plan is put into action. For example, your alarm may indicate a PING response time. If this time elapses, the alarm could send you an email.

## Create an Entity
The first step in working with Cloud Monitoring is to create an `entity`, which represents the device to monitor. To do so, you specify the characteristics of the device, which include one or more IP addresses. The parameter `ip_addresses` is a dictionary, with the keys being a string that can be used to identify the address (known as an *alias* to other parts of the API), and the value the IPv4 or IPv6 address for the entity. You can include as many addresses as you need. You can also include optional metadata to help you identify what the entity represents in your system.

    ent = cm.create_entity(name="sample_entity", ip_addresses={"example": "1.2.34"},
            metadata={"description": "Just a test entity"})

## Create a Check
There are numerous types of checks, and each requires its own parameters, and offers its own combination of metrics. The list of all [available check types](http://docs.rackspace.com/cm/api/v1.0/cm-devguide/content/appendix-check-types.html) shows how extensive your monitoring options are.

### Check Types
As an example, create a check on the HTTP server for the entity. This check will try to connect to the server and retrieve the specified URL using the specified method, optionally with the password and user for authentication, using SSL, and checking the body with a regex. This can be used to test that a web application running on a server is responding without generating error messages. It can also test if the SSL certificate is valid.

From the table in the Available Check Types link above, you can find that the ID of the desired check type is `remote.http`. You can also get a list of all check types by calling:

    chk_types = cm.list_check_types()

This returns a list of `CloudMonitorCheckType` objects. Each object has an attribute named `fields` that lists the parameters for that type, with each indicating whether the field is required or optional, its name, and a brief description. As an example, here is the `fields` attribute for the `remote.http` check type:

    [{u'description': u'Target URL',
          u'name': u'url',
          u'optional': False},
     {u'description': u'Body match regular expression (body is limited to 100k)',
          u'name': u'body',
          u'optional': True},
     {u'description': u'Arbitrary headers which are sent with the request.',
          u'name': u'headers',
          u'optional': True},
     {u'description': u'Body match regular expressions (body is limited to 100k, matches are truncated to 80 characters)',
          u'name': u'body_matches',
          u'optional': True},
     {u'description': u'HTTP method (default: GET)',
          u'name': u'method',
          u'optional': True},
     {u'description': u'Optional auth user',
          u'name': u'auth_user',
          u'optional': True},
     {u'description': u'Optional auth password',
          u'name': u'auth_password',
          u'optional': True},
     {u'description': u'Follow redirects (default: true)',
          u'name': u'follow_redirects',
          u'optional': True},
     {u'description': u'Specify a request body (limited to 1024 characters). If following a redirect, payload will only be sent to first location',
          u'name': u'payload',
          u'optional': True}]

Note that most of the parameters are optional; the only required parameter is **url**. If you only include that, the monitor will simply check that a plain GET on that URL gets some sort of response. By adding additional parameters to the check, you can make the tests that the check carries out much more specific.


### Monitoring Zones
To list the available Monitoring Zones, call:

    cm.list_monitoring_zones()

This returns a list of `CloudMonitorZone` objects:

    [<CloudMonitorZone country_code=US, id=mzdfw, label=Dallas Fort Worth (DFW), source_ips=[u'2001:4800:7902:0001::/64', u'50.56.142.128/26']>,
     <CloudMonitorZone country_code=HK, id=mzhkg, label=Hong Kong (HKG), source_ips=[u'180.150.149.64/26', u'2401:1800:7902:1:0:0:0:0/64']>,
     <CloudMonitorZone country_code=US, id=mziad, label=Washington Dulles (IAD), source_ips=[u'2001:4802:7902:0001::/64', u'69.20.52.192/26']>,
     <CloudMonitorZone country_code=GB, id=mzlon, label=London (LON), source_ips=[u'2a00:1a48:7902:0001::/64', u'78.136.44.0/26']>,
     <CloudMonitorZone country_code=US, id=mzord, label=Chicago (ORD), source_ips=[u'2001:4801:7902:0001::/64', u'50.57.61.0/26']>,
     <CloudMonitorZone country_code=AU, id=mzsyd, label=Sydney (SYD), source_ips=[u'119.9.5.0/26', u'2401:1801:7902:1::/64']>]

The most important piece of information in a `CloudMonitorZone` is the `id`, which you pass in the `monitoring_zones_poll` argument of `create_check`.

## Create the Check
To create the check, run the following:

    chk = cm.create_check(ent, label="sample_check", check_type="remote.http",
            details={"url": "http://example.com/some_page"}, period=900,
            timeout=20, monitoring_zones_poll=["mzdfw", "mzlon", "mzsyd"],
            target_hostname="http://example.com")

This will create an HTTP check on the entity `ent` for the page `http://example.com/some_page` that will run every 15 minutes from the Dallas, London, and Sydney monitoring zones.

There are several parameters for `create_check()`:

Parameter | Required? | Default | Description
------ | ------ | ------ | ------ 
**label** | no | -blank- | An optional label for this check
**name** | no | -blank- | Synonym for 'label'
**check_type** | yes | | The type of check to create. Can be either a `CloudMonitorCheckType` instance, or its ID.
**details** | no | None | A dictionary for the parameters needed for this type of check.
**disabled** | no | False | Passing `disabled=True` creates the check, but it will not be run until the check is enabled.
**metadata** | no | None | Arbitrary key/value pairs you can associate with this check
**monitoring_zones_poll** | yes | | Either a list or a single monitoring zone. Can be either `CloudMonitoringZone` instances, or their IDs.
**period** | no | (account setting) | How often to run the check, in seconds. Can range between 30 and 1800.
**timeout** | no | None | How long to wait before failing the check. Must be less than the period.
**target_hostname** | Mutually exclusive with `target_alias` | None | Either the IP address or the fully qualified domain name of the target of the check. 
**target_alias** | Mutually exclusive with `target_hostname` | None | A key in the 'ip_addresses' dictionary of the entity for this check.

Note that you must supply either a `target_hostname` or a `target_alias`, but not both.

## Create a Notification

There are three supported notification types; `email`, `webhook`, and `pagerduty`, by which you can be notified of alarms. To see the details for each type, call:

    `cm.list_notification_types()`

This returns a list of `CloudMonitorNotificationType` objects:

    [<CloudMonitorNotificationType fields=[{u'optional': False, u'name': u'url', u'description': u'An HTTP or HTTPS URL to POST to'}], id=webhook>,
     <CloudMonitorNotificationType fields=[{u'optional': False, u'name': u'address', u'description': u'Email address to send notifications to'}], id=email>,
     <CloudMonitorNotificationType fields=[{u'optional': False, u'name': u'service_key', u'description': u'The PagerDuty service key to use.'}], id=pagerduty>]

The `id` value is then passed in as the `notification_type` parameter to `create_notification()`.


## Create the Notification

To create the notification, run the following:

    email = cm.create_notification("email", label="my_email_notification",
            details={"address": "me@example.com"})

This will create an email notification that will notify the caller at *me@example.com*.

The `create_notification()` method contains several parameters:

Parameter | Required? | Default | Description
------ | ------ | ------ | ------ 
**notification_type** | yes | | A `CloudMonitoringNotificationType`, or a string matching a supported type's `id` attribute
**label** | no | None | Friendly name for the notification
**details** | no | None | A dictionary of details for your `notification_type`

## Create the Notification Plan

Notification Plans outline the specific notifications to contact under three conditions: **OK**, **Warning**, and **Critical** states. The `create_notification_plan()` method contains several parameters:

Parameter | Required? | Default | Description
------ | ------ | ------ | ------
**label** | no | | Text to identify this plan
**name** | no | | Text to name this plan
**critical_state** | no | None | A `CloudMonitorNotification` object to be notified when an alarm reaches the critical state
**ok_state** | no | None | A `CloudMonitorNotification` object to be notified when an alarm reaches the ok state
**warning_state** | no | None | A `CloudMonitorNotification` object to be notified when an alarm reaches the warning state

Using one or more notifications you've created, call:

    plan = cm.create_notification_plan(label="default", ok_state=ok_hook, warning_state=warning_email, critical_state=critical_email)

Once created, a Notification Plan is used to configure an Alarm.

## Create an Alarm

Alarms build on the previously covered topics, and introduce a mini-language used to specify the situation in which a notification plan should be executed. The alarm language is fully explained in [Appendix A](http://docs.rackspace.com/cm/api/v1.0/cm-devguide/content/alerts-language.html) of the Cloud Monitoring documentation.

### Metrics

The mini-language operates on *metrics*, which are values stored relating to a *check* you have created. To see the list of supported metrics for a given check, call:

    check.list_metrics()

If your check has not yet collected any metrics, which is dependent on the *period* you have configured for your check along with when you're making the request, it could be an empty list. If metrics are available, they'll be returned as a list of strings in the format **monitoringZone.metricName**. For a **remote.ping** check, you may receive metrics like the following:

    [u'mzdfw.available', u'mzdfw.average']

Those metrics can then be used to construct the criteria string in ``cm.create_alarm``.

### Create the Alarm

Once you have created an entity, a check, and a notification plan, you can create an alarm using the mini-language. For example:

    alarm = cm.create_alarm(entity, check, np, "if (rate(metric['average']) > 10) { return new AlarmStatus(WARNING); } return new AlarmStatus(OK);")

This alarm will alert the *warning* notification in the notification plan when your check's **average** metric measures over 10. Otherwise, the the alarm will report that your check turned out *OK*.


## List Alarm Changelogs

The monitoring service records changelogs for alarm statuses. By default the last 7 days of changelog information is returned. If you have many devices that are being monitored, this can be a lot of information, so you can optionally specify an entity, and the results are limited to changelogs for that entity's alarms.

To get the changelogs, make the following call:

    chglogs = cm.get_changelogs([entity=my_entity])

If you specify an entity, it can either be an Entity object returned from a previous operation, or the ID of that entity. The result looks like the following, with one element in the `values` list for each changelog returned:

    {
        "values": [
            {
                "id": "4c5e28f0-0b3f-11e1-860d-c55c4705a286",
                "timestamp": 1320890228991,
                "entity_id": "enPhid7noo",
                "alarm_id": "alahf9vuNa",
                "check_id": "chIe7vohba",
                "state": "WARNING",
                "analyzed_by_monitoring_zone_id": "DFW"
            }
        ],
        "metadata": {
            "count": 1,
            "limit": 50,
            "marker": null,
            "next_marker": null,
            "next_href": null
        }
    }

## Get Overview

Views contain a combination of data that usually includes multiple, different objects. The primary purpose of a view is to save API calls and make data retrieval more efficient. The data is returned in a dictionary with a `values` key that holds a list for each entity in your account and each entity's child check and alarm objects. Along with the child check and alarm objects it also includes the latest computed state for each check and alarm pair. If there is no latest state available for a check and alarm pair, it means the alarm hasn't been evaluated yet and the current state for this pair is 'UNKNOWN'.

Please note that this is a convenience method, and returns raw data, and not the `Entity`, `Alarm`, and `Check` objects like the other methods in this module.

The call is:

    view = cm.get_overview([entity=my_entity])

You can optionally list this to return the information for a single entity. If you specify an entity, it can either be an Entity object returned from a previous operation, or the ID of that entity. The result looks like the following, with one element in the `values` list for each entity returned:

    {'metadata':
        {'count': 3,
          'limit': 50,
          'marker': None,
          'next_href': None,
          'next_marker': None},
     'values': [
         {'alarms': [{'check_id': 'chFour',
         'criteria': 'if (metric["size"] >= 200) { return new AlarmStatus(CRITICAL); }',
         'id': 'alThree',
         'notification_plan_id': 'npOne'}],
       'checks': [{'details': {'method': 'GET', 'url': 'http://www.foo.com'},
         'disabled': False,
         'id': 'chFour',
         'label': 'ch a',
         'monitoring_zones_poll': ['mzA'],
         'period': 150,
         'target_alias': 'default',
         'target_hostname': '',
         'target_resolver': '',
         'timeout': 60,
         'type': 'remote.http'}],
       'entity': {'id': 'enBBBBIPV4',
        'ip_addresses': {'default': '127.0.0.1'},
        'label': 'entity b v4',
        'metadata': None},
       'latest_alarm_states': [{'alarm_id': 'alThree',
         'analyzed_by_monitoring_zone_id': None,
         'check_id': 'chFour',
         'entity_id': 'enBBBBIPV4',
         'previous_state': 'WARNING',
         'state': 'OK',
         'status': 'everything is ok',
         'timestamp': 1321898988}]},
      {'alarms': [],
       'checks': [],
       'entity': {'id': 'enCCCCIPV4',
        'ip_addresses': {'default': '127.0.0.1'},
        'label': 'entity c v4',
        'metadata': None},
       'latest_alarm_states': []},
      {'alarms': [{'check_id': 'chOne',
         'criteria': 'if (metric["duration"] >= 2) { return new AlarmStatus(OK); } return new AlarmStatus(CRITICAL);',
         'id': 'alOne',
         'label': 'Alarm 1',
         'notification_plan_id': 'npOne'},
        {'check_id': 'chOne',
         'criteria': 'if (metric["size"] >= 200) { return CRITICAL } return OK',
         'id': 'alTwo',
         'label': 'Alarm 2',
         'notification_plan_id': 'npOne'}],
       'checks': [{'details': {'method': 'GET', 'url': 'http://www.foo.com'},
         'disabled': False,
         'id': 'chOne',
         'label': 'ch a',
         'monitoring_zones_poll': ['mzA'],
         'period': 150,
         'target_alias': 'default',
         'target_hostname': '',
         'target_resolver': '',
         'timeout': 60,
         'type': 'remote.http'},
        {'details': {'method': 'GET', 'url': 'http://www.foo.com'},
         'disabled': False,
         'id': 'chThree',
         'label': 'ch a',
         'monitoring_zones_poll': ['mzA'],
         'period': 150,
         'target_alias': 'default',
         'target_hostname': '',
         'target_resolver': '',
         'timeout': 60,
         'type': 'remote.http'},
        {'details': {'method': 'GET', 'url': 'http://www.foo.com'},
         'disabled': False,
         'id': 'chTwo',
         'label': 'ch a',
         'monitoring_zones_poll': ['mzA'],
         'period': 150,
         'target_alias': 'default',
         'target_hostname': '',
         'target_resolver': '',
         'timeout': 60,
         'type': 'remote.http'}],
       'entity': {'id': 'enAAAAIPV4',
        'ip_addresses': {'default': '127.0.0.1'},
        'label': 'entity a',
        'metadata': None},
       'latest_alarm_states': [{'alarm_id': 'alOne',
         'analyzed_by_monitoring_zone_id': None,
         'check_id': 'chOne',
         'entity_id': 'enAAAAIPV4',
         'previous_state': 'OK',
         'state': 'WARNING',
         'status': 'matched return statement on line 7',
         'timestamp': 1321898988},
        {'alarm_id': 'alOne',
         'analyzed_by_monitoring_zone_id': None,
         'check_id': 'chTwo',
         'entity_id': 'enAAAAIPV4',
         'state': 'CRITICAL',
         'timestamp': 1321898988}]}
        ]
    }
