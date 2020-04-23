People's Assembly uses the WriteInPublic API to provide functionality to email Members of Parliament and Committees via the website.

The WriteInPublic service is at http://writeinpublic.pa.org.za

[Edit diagram](https://docs.google.com/drawings/d/1-Gvynn2s62mIn1hZemxf3cESYyVfObt18supQ5sU0nw/edit)

<img src="https://docs.google.com/drawings/d/e/2PACX-1vQPyYFAZPMebpX71N3ceQQwnA13c9l-5boMXzKZiSodJlJTAhe3oo4nvHYTlNnFeH6xnnSHu1DKhjUH/pub?w=1440&amp;h=1080">


## Installation


### DNS

`writeinpublic.pa.org.za` and `*.writeinpublic.pa.org.za` should point to the server and be served by the WriteInPublic django app.

`writeinpublic.pa.org.za` seems to be used by the write_in_public django app.

`*.writeinpublic.pa.org.za` seems to provide instance-specific interfaces for managing templates and getting API details,e.g. http://south-africa-assembly.writeinpublic.pa.org.za 


## Legacy

This WriteInPublic instance used to get contacts from EveryPolitician but EveryPolitician has been paused, and contact details for MPs and Committees.

