export default {
  sortedByDate(arr) {
    return arr.sort((one, other) => new Date(one.created) - new Date(other.created))
  }
}
