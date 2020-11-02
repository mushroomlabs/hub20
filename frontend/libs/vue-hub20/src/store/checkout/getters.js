import Decimal from 'decimal.js-light'

export default {
    acceptedTokens: (state, getters) => {
        return getters.acceptedTokenAddresses.map(address => getters.getToken(address))
    },
    acceptedTokenAddresses: (state) => {
        return (state.store && state.store.accepted_currencies) || []
    },
    paymentOrder: (state) => {
        let checkout = state.checkout

        return checkout && {
            token: checkout.token,
            tokenAmount: Decimal(checkout.amount),
            identifier: checkout.external_identifier,
            createdTime: checkout && new Date(checkout.created),
            isCanceled: Boolean(checkout.cancellation != null)
        }
    },
    paymentRouting: (state) => {
        let checkout = state.checkout
        let routes = checkout && checkout.routes

        if (!routes) {
            return
        }

        let blockchainRoutes = routes.filter(route => route.type == 'blockchain')
        let raidenRoutes = routes.filter(route => route.type == 'raiden')
        return {
            blockchain: (blockchainRoutes && blockchainRoutes[0]) || null,
            raiden: (raidenRoutes && raidenRoutes[0]) || null
        }
    },
    hasPendingTransfers: (state, getters) => {
        return Boolean(getters.blockchainPendingTransfers.length > 0)
    },
    isPaid: (state, getters) => {
        let paymentOrder = getters.paymentOrder
        let orderAmount =  paymentOrder && paymentOrder.tokenAmount

        return Boolean(orderAmount && getters.tokenAmountTransferred.gte(orderAmount))
    },
    isCanceled: (state, getters) => {
        let paymentOrder = getters.paymentOrder
        return Boolean(paymentOrder && paymentOrder.isCanceled)
    },
    tokenAmountTransferred: (state, getters) => {
        return getters.tokenAmountPending.add(getters.tokenAmountConfirmed)
    },
    selectedToken: (state, getters) => {
        return state.selectedTokenAddress && getters.getToken(state.selectedTokenAddress)
    },
    tokenAmountPending: (state, getters) => {
        if (!getters.hasPendingTransfers) {
            return Decimal(0)
        }

        let pendingTransfers = getters.blockchainPendingTransfers
        let transferAmounts = pendingTransfers.map(transfer => Decimal(transfer.amount || 0))
        return transferAmounts.reduce((acc, value) => acc.add(Decimal(value)), Decimal(0))
    },
    tokenAmountConfirmed: (state, getters) => {
        let reducer = (acc, value) => acc.add(Decimal(value))
        let blockchainConfirmedTransfers = getters.blockchainTransfers.filter(transfer => transfer.status == 'confirmed')
        let raidenConfirmedTransfers = getters.raidenTransfers.filter(transfer => transfer.status == 'confirmed')
        let blockchainTransferAmounts = blockchainConfirmedTransfers.map(transfer => Decimal(transfer.amount))
        let raidenTransferAmounts = raidenConfirmedTransfers.map(transfer => Decimal(transfer.amount))
        let totalBlockchain = blockchainTransferAmounts.reduce(reducer, Decimal(0))
        let totalRaiden = raidenTransferAmounts.reduce(reducer, Decimal(0))

        return totalBlockchain.add(totalRaiden)
    },
    tokenAmountDue: (state, getters) => {
        let paymentOrder = getters.paymentOrder
        let orderAmount = paymentOrder && paymentOrder.tokenAmount

        let due = orderAmount && orderAmount.sub(getters.tokenAmountTransferred)

        return due && due.gt(0) ? due.toNumber() : 0
    },
    convertToTokenAmount: (state, getters) => (currencyAmount, token) => {
        let exchangeRate = getters.getExchangeRate(token)

        return exchangeRate && Decimal(currencyAmount).div(Decimal(exchangeRate))
    },
    getExchangeRate: (state) => (token) => {
        return token && state.exchangeRates[token.address]
    },
    getTokenAmountWei: (state, getters) => (amount, tokenAddress) => {
        let token = getters.getToken(tokenAddress)
        return Math.floor(amount * (10 ** token.decimals))
    },
    getToken: (state) => (tokenAddress) => {
        return state.tokens[tokenAddress]
    },
    getTokenLogo: (state) => (token) => {
        return state.tokenLogos[token.address]
    },
    allTokens: (state) => {
        let tokens = Object.values(state.tokens)

        // Addresses are Hex strings of fixed sized so we can lexigographically compare them
        return tokens.sort(function(one, other) { return one.address - other.address })
    },
    amountFormatted: (state) => {
        if (!state.pricingCurrency) {
            return ''
        }

        let formatter = new Intl.NumberFormat(
            [], {style: 'currency', currency: state.pricingCurrency}
        );
        return formatter.format(Decimal(state.amountDue).toNumber())
    },
    transfers: (state, getters) => {
        return [
            ...getters.blockchainTransfers,
            ...getters.raidenTransfers
        ]
    },
    blockchainTransfers: (state) => {
        return Object.values(state.blockchainTransferMap)
    },
    raidenTransfers: (state) => {
        return Object.values(state.raidenTransferMap)
    },
    blockchainPendingTransfers: (state, getters) => {
        let pendingStates = ['sent', 'received', 'pending']
        return getters.blockchainTransfers.filter(transfer => pendingStates.includes(transfer.status))
    },
    websocketRootUrl: (state) => {
        if (!state.apiRootUrl) {
            return null
        }

        let url = new URL(state.apiRootUrl)
        let ws_protocol = url.protocol == 'http:' ? 'ws:': 'wss:'
        url.protocol = ws_protocol
        return `${url.origin}/ws`
    }
}
