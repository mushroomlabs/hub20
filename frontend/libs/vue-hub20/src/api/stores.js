import session from './session';

export default {
  create(storeData) {
    const {name, site_url, accepted_currencies } = storeData;
    let payload = { name, site_url, accepted_currencies };
    return session.post('/api/stores', payload);
  },
  getList() {
    return session.get('/api/stores');
  },
  get(storeId) {
    return session.get(`/api/stores/${storeId}`);
  },
  update(storeData) {
    const {url, name, site_url, accepted_currencies}  = storeData;
    let payload = { name, site_url, accepted_currencies };
    return session.put(url, payload)
  },
  remove(storeId) {
    return session.delete(`/api/stores/${storeId}`);
  }
};
