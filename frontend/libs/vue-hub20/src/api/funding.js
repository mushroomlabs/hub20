import client from './client'

export default {
  _client: client,
  createDeposit(token) {
    return this._client.post('/deposits', {
      token: token.address
    })
  },
  getDeposits() {
    return this._client.get('/deposits')
  },
  getDeposit(depositId) {
    return this._client.get(`/deposit/${depositId}`)
  },
  createPaymentOrder(token, amount) {
    return this._client.post('/payment/orders', {
      amount: amount,
      token: token.address
    })
  },
  getPaymentOrder(orderId) {
    return this._client.get(`/payment/orders/${orderId}`)
  },
  cancelPaymentOrder(orderId) {
    return this._client.delete(`/payment/orders/${orderId}`)
  },
  getTransfers() {
    return this._client.get('/transfers')
  },
  scheduleTransfer(token, amount, options) {
    let payload = {
      amount: amount,
      token: token.address,
      ...options
    }
    return this._client.post('/transfers', payload)
  }
}
