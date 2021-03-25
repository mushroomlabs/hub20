## Welcome to Hub20

Hub20 is a very-early stage open source, self-hosted online payment
solution that can be considered as the Ethereum equivalent of
[BTCPayServer](https://btcpayserver.org) payment gateway, allowing
users to collect payments in Ethereum and any ERC20 token.

#### Integration with Layer-2 systems for fast and ultra-cheap transactions

Hub20 also provides integration with [Raiden](https://raiden.network),
so that if you have a node running you should be able to accept and
send payments of ERC20 tokens with near-zero fees.

The possiblity of having low-fee payments, irreversibility of
transactions and the usage of stablecoins such as
[DAI](https://makerdao.com) make hub20 a very compelling offer for
anyone that wants to receive payments online.

### More than a payment gateway

Hub20 also allows users *sending* their tokens to either other users
of the hub as well as to any ethereum address, effectively turning any
deployment of a hub20 server into an exclusive Paypal/Venmo/cryptobank
for its users.

This works because hub20 offers the possibility of using custodial
wallets for managing its funds. While this is not ideal for large
deployments such as companies and crypto exchanges, for a self-hosted
service this is more acceptable because the node operator is the one
effectively controlling the wallets and therefore its keys.

This also opens the possibility for, e.g, enthusiasts to set up a
hub20 node for their non-technical friends and family (i.e, people
that are within their circle of trust) so that they can have an easy
way to do transactions in cryptocurrency without ever having to deal
with anything that hinders adoption: nothing to learn about wallets,
no access to exchanges needed, no KYC, etc.

### Extensible architecture

Hub20 is designed to work as a bridge between the "traditional" web
and the growing-but-still-challenging web3 and decentralized apps
based on the Ethereum blockchain. Hub Administrators can choose how
much they want to pick from each "side" of the tech stack that is more
suited to their needs. Want to create a hub that can authenticate with
your company's LDAP or do you prefer to use ethereum account ownership
for authentication? They are both just a configuration setting away.

## More details:

  - [Documentation](https://docs.hub20.io)
  - [Frontend](https://app.hub20.io) application is available and can
    connect to any backend server available on the internet. Use
    https://demo.hub20.io as a test instance that we provide,
    connected to Goerli testnet.


### Contributing

If you are a developer and would like to contribute, don't hesitate to
get in touch. Any contribution is more than welcome. We are using
[Zenhub](https://app.zenhub.com/workspaces/hub20-5dd80da129db370001f2469e/board)
to keep track of ongoing work and plan milestones.

### License

The project is made up of different components:

 - The backend code provides an API and does all the interfacing with
   the blockchain and the underlying Raiden node. This is available
   under the [Affero GNU Public License
   v3](https://www.gnu.org/licenses/agpl-3.0.en.html)
 - The web application that works as the frontend and the base
   javascript library are
   [MIT-licensed](https://www.tldrlegal.com/l/mit)


### Supporters

Hub20 development started thanks to a grant awarded by the [Raiden
Trust](https://medium.com/raiden-network/hub20-the-latest-grant-895c9fabcb9c).
If you'd like to support the project, please visit our [sponsors
page](https://github.com/sponsors/mushroomlabs)
