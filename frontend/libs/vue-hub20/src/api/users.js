import client from './client'

export default {
  _client: client,
  getUserList() {
    return this._client.get('/users')
  },
  getUser(username) {
    return this._client.get(`/users/${username}`)
  },
  searchUsers(searchTerm) {
    return this._client.get('/users', {params: {search: searchTerm}})
  }
}
