import client from './client'

const indexResponseKeys = [
  'current_user_url',
  'network_status_url',
  'accounting_report_url',
  'tokens_url',
  'users_url',
  'version'
]

const isExpectedResponseData = data => {
  const responseKeys = Object.keys(data)
  return [
    responseKeys.length == Object.keys(indexResponseKeys).length,
    responseKeys.every(key => indexResponseKeys.includes(key))
  ].every(pred => Boolean(pred))
}

export default {
  _client: client,
  setUrl(url) {
    this._client.defaults.baseURL = url
  },
  checkHub20Server(url) {
    return this._client.get('/', {baseURL: url}).then(({data}) => {
      if (isExpectedResponseData(data)) {
        return Promise.resolve(data.version)
      } else {
        return Promise.reject('Server response is not from Hub20 backend')
      }
    })
  }
}
