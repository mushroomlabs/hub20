export const toWei = function(token, amount) {
  return Math.floor(amount * 10 ** token.decimals)
}

export default {toWei}
