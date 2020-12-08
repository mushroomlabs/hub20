import axios from 'axios'

export const API_ROOT_URL = 'https://api.coingecko.com/api/v3'
export const TOKEN_LIST_URL = 'https://tokens.coingecko.com/uniswap/all.json'
export const ETHEREUM_LOGO_URL =
  'https://assets.coingecko.com/coins/images/279/large/ethereum.png'
export const client = axios.create()

export default {
  getTokenList() {
    return client.get(TOKEN_LIST_URL)
  },
  getEthereumRate(currencyCode) {
    const url = `${API_ROOT_URL}/simple/price?ids=ethereum&vs_currencies=${currencyCode}`
    return client
      .get(url)
      .then(({data}) => Promise.resolve(data.ethereum[currencyCode.toLowerCase()]))
  },
  getTokenRate(token, currencyCode) {
    const url = `${API_ROOT_URL}/simple/token_price/ethereum?contract_addresses=${
      token.address
    }&vs_currencies=${currencyCode}`
    return client.get(url).then(({data}) => {
      // Attention: data will be keyed by checksummed token address,
      // while token address is not necessarily checksummed. This is
      // fine because the Object will have only one item, so we can
      // go straight to about the object values
      let quotes = Object.values(data)
      return Promise.resolve(quotes[0][currencyCode.toLowerCase()])
    })
  },
  getTokenLogoUrl(token) {
    const url = `${API_ROOT_URL}/coins/ethereum/contract/${token.address}`
    return client.get(url).then(({data}) => {
      const logoUrl = data && data.image && data.image.large
      return Promise.resolve(logoUrl || ETHEREUM_LOGO_URL)
    })
  }
}
