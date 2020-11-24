import account from './account'
import auth from './auth'
import events from './events'
import funding from './funding'
import notifications from './notifications'
import password from './password'
import server from './server'
import signup from './signup'
import stores from './stores'
import tokens from './tokens'
import web3 from './web3'

export const EVENT_TYPES = {
  BLOCKCHAIN_BLOCK_CREATED: 'blockchain.block.created',
  BLOCKCHAIN_DEPOSIT_BROADCAST: 'blockchain.deposit.broadcast',
  BLOCKCHAIN_DEPOSIT_RECEIVED: 'blockchain.deposit.received',
  BLOCKCHAIN_ROUTE_EXPIRED: 'blockchain.payment_route.expired',
  ETHEREUM_NODE_UNAVAILABLE: 'ethereum_node.unavailable',
  ETHEREUM_NODE_OK: 'ethereum_node.ok',
  RAIDEN_DEPOSIT_RECEIVED: 'raiden.deposit.received',
  RAIDEN_ROUTE_EXPIRED: 'raiden.payment_route.expired'
}

export default {
  account,
  auth,
  events,
  funding,
  notifications,
  password,
  server,
  signup,
  stores,
  tokens,
  web3,
  EVENT_TYPES
}
