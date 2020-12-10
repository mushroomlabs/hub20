import client from './client'

export default {
  _client: client,
  getCredits() {
    return this._client.get('/credits')
  },
  getDebits() {
    return this._client.get('/debits')
  },
  getBalances() {
    return this._client.get('/balances')
  },
  getTokenBalance(address) {
    return this._client.get(`/balance/${address}`)
  }
}
