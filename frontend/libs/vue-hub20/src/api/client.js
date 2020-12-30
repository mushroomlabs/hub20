import axios from 'axios'

const client = axios.create({
  headers: {
    Accept: 'application/json',
    'Content-Type': 'application/json'
  }
})

export default client
