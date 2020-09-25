import session from './session';

export default {
  getTokenList() {
    return session.get('/api/tokens/');
  },
  getToken(address) {
    return session.get(`/api/tokens/token/${address}`);
  },
};
