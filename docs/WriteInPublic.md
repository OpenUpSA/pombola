People's Assembly uses the WriteInPublic API to provide functionality to email Members of Parliament and Committees via the website.

The WriteInPublic service is at http://writeinpublic.pa.org.za.

MPs and Committees are configured in two WriteInPublic _instances_ with the respective **slugs** 

- `south-africa-assembly`
- `south-africa-committees`.

[Edit diagram](https://docs.google.com/drawings/d/1-Gvynn2s62mIn1hZemxf3cESYyVfObt18supQ5sU0nw/edit)

<img src="https://docs.google.com/drawings/d/e/2PACX-1vQPyYFAZPMebpX71N3ceQQwnA13c9l-5boMXzKZiSodJlJTAhe3oo4nvHYTlNnFeH6xnnSHu1DKhjUH/pub?w=1440&amp;h=1080">


## Installation

### Configuring People's Assembly to use its WriteInPublic instances



### DNS

`writeinpublic.pa.org.za` and `*.writeinpublic.pa.org.za` should point to the server and be served by the WriteInPublic django app.

`writeinpublic.pa.org.za` seems to be used by the write_in_public django app pombola for API calls to WriteInPublic and also for superuser admin tasks.

`*.writeinpublic.pa.org.za` seems to provide instance-specific interfaces for managing templates and getting API details,e.g. http://south-africa-assembly.writeinpublic.pa.org.za 


## Legacy

This WriteInPublic instance used to get contacts from EveryPolitician but EveryPolitician has been paused, and contact details for MPs and Committees.

## Using a local instance of WriteInPublic

- Clone https://github.com/mysociety/writeinpublic
- If you're running PA on port 8000, change the port on which WriteInPublic will run in the `docker-compose.yml` file.
- Run `docker-compose up`
- Enable your PA container to connect to your localhost by following one of the answers in [this question](https://stackoverflow.com/questions/24319662/from-inside-of-a-docker-container-how-do-i-connect-to-the-localhost-of-the-mach) or:
  - Run `export DOCKERHOST=$(ifconfig | grep -E "([0-9]{1,3}\.){3}[0-9]{1,3}" | grep -v 127.0.0.1 | awk '{ print $2 }' | cut -f2 -d: | head -n1)`
  - Add the following under the `app` service in your PA `docker-compose.yml` file:
   ```
     extra_hosts:
    - "dockerhost:$DOCKERHOST"
   ```
  - Ensure you have two `Configuration` objects (rows in the `writeinpublic_configuration` table) in your database with the `url` values as `http://dockerhost:8001` and the `slug` values as `south-africa-committees` and `south-africa-assembly` respectively.
  - You'll also need to create `ApiKey` and `WriteItInstance` objects in WriteInPublic and save their `api_key` and `instance_id` values in your `Configuration` objects.