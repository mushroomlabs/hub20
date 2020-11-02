import session from './session';

export default {
  getCredits() {
    return session.get('/api/credits');
  },
  getDebits() {
    return session.get('/api/debits');
  },
  getBalances() {
    return session.get('/api/balances');
  },
  getTokenBalance(address) {
    return session.get(`/api/balance/${address}`);
  },
};
