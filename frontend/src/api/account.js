import session from './session';

export default {
  getBalances() {
    return session.get('/api/balances');
  },
  getTokenBalance(address) {
    return session.get(`/api/balance/${address}`);
  },
};
