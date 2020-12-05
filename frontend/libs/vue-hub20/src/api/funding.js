import session from './session'

export default {
  createDeposit(token) {
    return session.post('/api/deposits', {
      token: token.address
    })
  },
  getDeposits() {
    return session.get('/api/deposits')
  },
  getDeposit(depositId) {
    return session.get(`/api/deposit/${depositId}`)
  },
  createPaymentOrder(token, amount) {
    return session.post('/api/payment/orders', {
      amount: amount,
      token: token.address
    })
  },
  getPaymentOrder(orderId) {
    return session.get(`/api/payment/orders/${orderId}`)
  },
  cancelPaymentOrder(orderId) {
    return session.delete(`/api/payment/orders/${orderId}`)
  },
  getTransfers() {
    return session.get('/api/transfers')
  },
  scheduleTransfer(token, amount, options) {
    let payload = {
      amount: amount,
      token: token.address,
      ...options
    }
    return session.post('/api/transfers', payload)
  }
}
