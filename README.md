## Welcome to Hub20

Hub20 is an early stage open source, self-hosted online payment
solution that can be considered as the Ethereum equivalent of
[BTCPayServer](https://btcpayserver.org) payment gateway, allowing
users to collect payments in any Ethereum-compatible blockchain, using
either the blockchain's native token or any ERC20-compatible token
smart contract.

#### Integration with Layer-2 systems for fast and ultra-cheap transactions

The ability to interact with any blockchain that uses Ethereum's JSON
RPC protocol means that it is possible to interact seamlessly with
scaling projects such as
[roll-ups](https://docs.ethhub.io/ethereum-roadmap/layer-2-scaling/optimistic_rollups/)
like [Arbitrum](https://arbitrum.io/) or
[Optimism](https://www.optimism.io/), and also sidechains like
[xDAI](https://xdaichain.com) or
[Polygon](https://polygin.technology).

Hub20 also integrates with [Raiden Network](https://raiden.network),
so that if you have a node running you should be able to accept and
send payments of ERC20 tokens with near-zero fees. Integrating Raiden
brings the possibility of nearly-free transfers, irreversibility of
transactions and the usage of stablecoins such as
[DAI](https://makerdao.com), which make it a very compelling offer for anyone
that wants to receive payments online.

### More than a payment gateway

Hub20 also allows users *sending* their tokens to either other users
of the hub as well as to any external account (on the compatible
blockchains), effectively turning any deployment of a hub20 server
into an exclusive Paypal/Venmo/cryptobank for its users.

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

  - [Main website](https://hub20.io)
  - [Documentation](https://docs.hub20.io)
  - [Blog](https://blog.hub20.io)
  - [Frontend](https://app.hub20.io) application is available and can
    connect to any backend server available on the internet. Use
    https://demo.hub20.io as a test instance that we provide,
    connected to test networks (Görli, Binance Test, Test Arbitrum, Test Optimism).


### Contributing

If you like to contribute, don't hesitate to get in touch. Any
contribution is more than welcome. You don't need to be a developer to
try the demo application, find bugs and make suggestions for
improvements. We are using
[Taiga](https://tree.taiga.io/project/lullis-mushroomlabshub20/) to
track issues and to manage the work and milestones.

The official repository is at
[Gitlab](https://gitlab.com/mushroomlabs/hub20), and we also keep a
mirror at [Github](https://github.com/mushroomlabs/hub20). Gitlab is
preferred because it provides a free (as in libre) platform for our
Continuous Integration system.

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
