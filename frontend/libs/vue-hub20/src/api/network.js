import client from './client'

export default {
  _client: client,
  getStatus() {
    return this._client.get('/status/networks')
  }
}
