export const toWei = function(token, amount) {
  return Math.floor(amount * 10 ** token.decimals)
}

export const formattedAmount = function(amount, token) {
  if (amount == 0) {
    return '0'
  }

  let formatter = new Intl.NumberFormat([], {maximumSignificantDigits: token.decimals})
  let formattedAmount = formatter.format(amount)
  return `${formattedAmount} ${token.code}`
}

export default {toWei, formattedAmount}
