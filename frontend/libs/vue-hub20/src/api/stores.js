import client from './client'

export default {
  _client: client,
  create(storeData) {
    const {name, site_url, accepted_currencies} = storeData
    let payload = {name, site_url, accepted_currencies}
    return this._client.post('/stores', payload)
  },
  getList() {
    return this._client.get('/stores')
  },
  get(storeId) {
    return this._client.get(`/stores/${storeId}`)
  },
  update(storeData) {
    const {url, name, site_url, accepted_currencies} = storeData
    let payload = {name, site_url, accepted_currencies}
    return this._client.put(url, payload)
  },
  remove(storeId) {
    return this._client.delete(`/stores/${storeId}`)
  }
}
