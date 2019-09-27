# Running the Pombola tests

## Running the tests for South Africa using docker-compose

	docker-compose run --rm app ./run-tests --coverage

## Running tests selectively

Sometimes you want to just try one test method. You can do this
for a generic test, for example, with:

	docker-compose run --rm app ./manage.py test pombola.core.tests.test_models:PositionCurrencyTest.test_from_past_still_current

Note that there must be a colon separating the module from the
class name.

## Speeding up repeated test runs

You can dramatically speed up the second and subsequent test 
runs by supplying the `--keepdb` option to `test`, like:

	docker-compose run --rm app ./manage.py test --keepdb \
		pombola.core.tests.test_models:PositionCurrencyTest.test_from_past_still_current

... because much of the time in running the tests is taken up
with running the database migrations.
