## Docker

This is the most straightforward method to run all the required services. By using [docker](https://docker.com) and [docker-compose](https://docs.docker.com/compose/) one can quickly bring up an instance of hub20 for development.

!!! attention

    This assumes that you already have an ethereum node client connected to the Göerli test network.

    If you would like to use a different test network, please see below for other variables that need to be changed.

* Clone repository
* Copy the file located at `$PROJECT_ROOT/docker/environments/sample.env` to `$PROJECT_ROOT/.env`
* Change the value of the `WEB3_PROVIDER_URI` variable to point to your ethereum node client.
* Run `docker-compose up` to build the image of hub20, pull required dependency images and and to start up all services. You can also run `docker-compose up -d` if you want to keep the services running in the background.

## Environment variables

The `sample.env` file provides all of the necessary environment
variables for the proper operation of the application running under
docker.

```
DJANGO_SETTINGS_MODULE=hub20.api.settings
HUB20_DATA_FOLDER=/var/hub20
HUB20_BROKER_URL=redis://redis:6379/0
HUB20_CACHE_BACKEND=django_redis.cache.RedisCache
HUB20_CACHE_LOCATION=redis://redis:6379/1
HUB20_CHANNEL_LAYER_HOST=redis
HUB20_DATABASE_HOST=db
HUB20_DATABASE_PORT=5432
HUB20_EMAIL_MAILER_ADDRESS=noreply@hub20.example.com
HUB20_EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
HUB20_SECRET_KEY=base-hub20-secret-key
HUB20_DATABASE_NAME=hub20
HUB20_DATABASE_USER=hub20
HUB20_DATABASE_PASSWORD=hub20_pass

HUB20_DEBUG=1
HUB20_TRACKED_TOKENS=0x0000000000000000000000000000000000000000,0x1c36690810ad06fb15552657c7a8ff653eb46f76,0xA9cad81fD505DBD678599F2541D0101dd01fc94E,0x95B2d84De40a0121061b105E6B54016a49621B44,0x59105441977ecd9d805a4f5b060e34676f50f806,0x709118121A1ccA0f32FC2C0c59752E8FEE3c2834
WEB3_PROVIDER_URI=http://localhost:8545
```

Pay attention to the following:

 * The values provided for what are supposed to be secret credentials (`HUB20_DATABASE_PASSWORD`, `HUB20_SECRET_KEY`) should never be used in an actual production setting.
 * `WEB3_PROVIDER_URI` is the URL that you will use to connect to your ethereum node. Basically, this is the one setting that will determine to which network your application will be connected and collecting data from.
 * `HUB20_TRACKED_TOKENS` is a comma-separated list of the token addresses that you want to use in your instance. The address of `0x0000000000000000000000000000000000000000` is considered the `NULL_ADDRESS` and is meant to be used for ETH. The addresses of the tokens listed in the sample file correspond to ERC20 tokens that are deployed on the Göerli network.
