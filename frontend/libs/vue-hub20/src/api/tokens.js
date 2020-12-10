import client from './client'

export default {
  _client: client,
  getList() {
    return this._client.get('/tokens/')
  },
  get(address) {
    return this._client.get(`/tokens/token/${address}`)
  }
}
