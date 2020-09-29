import session from './session';

export default {
  getList() {
    return session.get('/api/tokens/');
  },
  get(address) {
    return session.get(`/api/tokens/token/${address}`);
  },
};
