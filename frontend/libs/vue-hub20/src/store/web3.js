export const WEB3_CONNECT_BEGIN = 'WEB3_CONNECT_BEGIN'
export const WEB3_CONNECT_FAILURE = 'WEB3_CONNECT_FAILURE'
export const WEB3_TRANSFER_FAILURE = 'WEB3_TRANSFER_FAILURE'
export const WEB3_ADD_TRANSACTION = 'WEB3_ADD_TRANSACTION'

const EIP20_ABI = [
  {
    constant: true,
    inputs: [],
    name: 'name',
    outputs: [
      {
        name: '',
        type: 'string'
      }
    ],
    payable: false,
    stateMutability: 'view',
    type: 'function'
  },
  {
    constant: false,
    inputs: [
      {
        name: '_spender',
        type: 'address'
      },
      {
        name: '_value',
        type: 'uint256'
      }
    ],
    name: 'approve',
    outputs: [
      {
        name: '',
        type: 'bool'
      }
    ],
    payable: false,
    stateMutability: 'nonpayable',
    type: 'function'
  },
  {
    constant: true,
    inputs: [],
    name: 'totalSupply',
    outputs: [
      {
        name: '',
        type: 'uint256'
      }
    ],
    payable: false,
    stateMutability: 'view',
    type: 'function'
  },
  {
    constant: false,
    inputs: [
      {
        name: '_from',
        type: 'address'
      },
      {
        name: '_to',
        type: 'address'
      },
      {
        name: '_value',
        type: 'uint256'
      }
    ],
    name: 'transferFrom',
    outputs: [
      {
        name: '',
        type: 'bool'
      }
    ],
    payable: false,
    stateMutability: 'nonpayable',
    type: 'function'
  },
  {
    constant: true,
    inputs: [],
    name: 'decimals',
    outputs: [
      {
        name: '',
        type: 'uint8'
      }
    ],
    payable: false,
    stateMutability: 'view',
    type: 'function'
  },
  {
    constant: true,
    inputs: [
      {
        name: '_owner',
        type: 'address'
      }
    ],
    name: 'balanceOf',
    outputs: [
      {
        name: 'balance',
        type: 'uint256'
      }
    ],
    payable: false,
    stateMutability: 'view',
    type: 'function'
  },
  {
    constant: true,
    inputs: [],
    name: 'symbol',
    outputs: [
      {
        name: '',
        type: 'string'
      }
    ],
    payable: false,
    stateMutability: 'view',
    type: 'function'
  },
  {
    constant: false,
    inputs: [
      {
        name: '_to',
        type: 'address'
      },
      {
        name: '_value',
        type: 'uint256'
      }
    ],
    name: 'transfer',
    outputs: [
      {
        name: '',
        type: 'bool'
      }
    ],
    payable: false,
    stateMutability: 'nonpayable',
    type: 'function'
  },
  {
    constant: true,
    inputs: [
      {
        name: '_owner',
        type: 'address'
      },
      {
        name: '_spender',
        type: 'address'
      }
    ],
    name: 'allowance',
    outputs: [
      {
        name: '',
        type: 'uint256'
      }
    ],
    payable: false,
    stateMutability: 'view',
    type: 'function'
  },
  {
    payable: true,
    stateMutability: 'payable',
    type: 'fallback'
  },
  {
    anonymous: false,
    inputs: [
      {
        indexed: true,
        name: 'owner',
        type: 'address'
      },
      {
        indexed: true,
        name: 'spender',
        type: 'address'
      },
      {
        indexed: false,
        name: 'value',
        type: 'uint256'
      }
    ],
    name: 'Approval',
    type: 'event'
  },
  {
    anonymous: false,
    inputs: [
      {
        indexed: true,
        name: 'from',
        type: 'address'
      },
      {
        indexed: true,
        name: 'to',
        type: 'address'
      },
      {
        indexed: false,
        name: 'value',
        type: 'uint256'
      }
    ],
    name: 'Transfer',
    type: 'event'
  }
]

function makeTransferData(web3, amount, tokenAddress, recipientAddress) {
  let contract = web3.eth.contract(EIP20_ABI).at(tokenAddress)
  return contract.transfer.getData(recipientAddress, amount)
}

const initialState = {
  selectedAccount: null,
  web3Browser: null,
  connected: false,
  transactions: [],
  error: null
}

const getters = {
  hasWeb3Provider() {
    return window.ethereum || window.web3
  },
  connectedNetwork: state =>
    state.connected && state.web3Browser && state.web3Browser.version.network,
  isConnected: state => state.connected
}

const actions = {
  enableWeb3({commit}) {
    if (typeof window.ethereum !== 'undefined') {
      window.ethereum
        .request({method: 'eth_requestAccounts'})
        .then(accounts =>
          commit(WEB3_CONNECT_BEGIN, {w3: window.ethereum, accountAddress: accounts[0]})
        )
        .catch(error => commit(WEB3_CONNECT_FAILURE, error))
    }
  },
  requestTransfer({commit, state}, {token, amount, recipientAddress}) {
    let w3 = state.web3Browser

    if (!w3) {
      commit(WEB3_TRANSFER_FAILURE, 'Web wallet is not connected')
      return
    }

    let transactionData = {
      from: state.selectedAccount
    }

    if (!token.address) {
      // ETH transfer
      transactionData.to = recipientAddress
      transactionData.value = amount
    } else {
      transactionData.to = token.address
      transactionData.data = makeTransferData(w3, amount, token.address, recipientAddress)
    }

    w3.eth.sendTransaction(transactionData).then((error, tx) => {
      if (tx) {
        commit(WEB3_ADD_TRANSACTION, transactionData)
      }
      if (error) {
        commit(WEB3_TRANSFER_FAILURE, error)
      }
    })
  }
}

const mutations = {
  [WEB3_CONNECT_BEGIN](state, {w3, accountAddress}) {
    state.web3Browser = w3
    state.selectedAddress = accountAddress
    state.connected = true
    state.error = null
  },
  [WEB3_CONNECT_FAILURE](state, error) {
    state.web3Browser = null
    state.selectedAddress = null
    state.connected = false
    state.error = error
  },
  [WEB3_TRANSFER_FAILURE](state, error) {
    state.error = error
  },
  [WEB3_ADD_TRANSACTION](state, transactionData) {
    state.transactions.push(transactionData)
  }
}

export default {
  namespaced: true,
  state: initialState,
  actions,
  getters,
  mutations
}
