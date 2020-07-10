Hub20 is a fairly standard application implemented in
[Django](https://djangoproject.com) and
[Celery](https://docs.celeryproject.org). Django provides the HTTP API and
the website, while celery is using to run background tasks and
services.


### Integrated services

 - Ethereum node client: to keep track of all of the transactions on
   the blockchain. You can run your own or rely on a third-party
   service provider such as infura.
 - Raiden client: to be able to make and receive payments on the
   raiden network. This client needs to run on your own infrastructure
   and should have its access *always* protected. Currently Raiden
   does not provide any kind of access control or authorization checks
   for its API, which means that anyone with direct network access to
   raiden will be able to make operations with it.

### Dependencies

 - [PostgreSQL](https://postgresql.org) to record all user account
   data and relevant transactions that happen on either raiden or the
   blockchain
 - [Redis](https://redis.io) provides a cache layer, a message broker
   for celery and the scheduling of celery tasks and also as the
   comunication layer for django channels. It is *strongly*
   recommended that you use separate redis databases for each of these
   duties.
