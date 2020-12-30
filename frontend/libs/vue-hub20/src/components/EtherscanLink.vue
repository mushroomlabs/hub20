<template>
  <a :href="linkUrl" target="_blank">{{ address }}</a>
</template>
<script>
export default {
  name: 'EtherscanLink',
  props: {
    address: String,
    networkId: {
      type: Number,
      default: 1
    }
  },
  computed: {
    linkUrl() {
      const ETHERSCAN_DOMAINS_BY_NETWORK = {
        1: 'etherscan.io',
        3: 'ropsten.etherscan.io',
        4: 'rinkeby.etherscan.io',
        5: 'goerli.etherscan.io',
        42: 'kovan.etherscan.io'
      }

      const domain = ETHERSCAN_DOMAINS_BY_NETWORK[this.networkId]

      return domain && `https://${domain}/address/${this.address}`
    }
  }
}
</script>
