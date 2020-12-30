import client from './client'

export default {
  _client: client,
  getAccountingReport() {
    return this._client.get('/status/accounting')
  },
  getWalletBalances() {
    return this._client.get('/status/accounts')
  }
}
