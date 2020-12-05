import session from './session'

export default {
  getUserList() {
    return session.get('/api/users')
  },
  getUser(username) {
    return session.get(`/api/users/${username}`)
  },
  searchUsers(searchTerm) {
    return session.get('/api/users', {params: {search: searchTerm}})
  }
}
