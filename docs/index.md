# Hub20 Documentation

!!! danger "This software is still in very early stage and not yet recommended to be run by non-developers."

    Its functionality is directly tied up with the Ethereum blockchain and we assume that the reader is aware of technical and security implications of operating this kind of system. For its proper operation, private keys of an Ethereum account are required by the system. *DO NOT* use this software with any key that holds any substantial amounts of cryptocurrency.


## Introduction

Hub20 is an open source, self-hosted web application that provides a
wrapper for Ethereum and [Raiden Network](https://raiden.network)
client nodes. It hides all of the complexity from end-users so that
they can make and receive payments in ETH and any ERC20-compliant
token using always the fastest/cheapest possible route without ever
needing to know any technical detail. It also provides a set of APIs
that effectively turn any deployment into a payment gateway for
Ethereum tokens.

In practice, one can think of each instance of Hub20 of a single
"crypto bank" where users simply have access to their individual
accounts and token balances, while the person running the deployment
(hub operator or hub owner) is the one with actual access to the bank
vault and funds.


## Is Hub20 a Custodial Wallet?

This is a question that those more familiar with how blockchain and
cryptocurrency systems will certainly make. The short answer would be
*"No. Operators control the keys and can do whatever they want"*.

The correct answer is a bit more complex, because the operators can
also add accounts for other users and these users would not have
control over the keys. So let's take some time to explain what is
Hub20's value proposition.
