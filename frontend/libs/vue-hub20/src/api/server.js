import session from './session'

export default {
  getStatus() {
    return session.get('/api/status')
  }
}
