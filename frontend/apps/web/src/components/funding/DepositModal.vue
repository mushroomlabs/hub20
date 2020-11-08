<template>
  <Modal :title="title" :hidden="false" :id="modalId" label="deposit-modal">
    <template>
      <PaymentRequest :paymentRequest='deposit' />
    </template>
  </Modal>
</template>

<script>
import {mapGetters} from 'vuex'
import {default as hub20lib} from 'vue-hub20'

import Modal from '@/widgets/dialogs/Modal'

const {PaymentRequest} = hub20lib.components

export default {
  components: {
    Modal,
    PaymentRequest
  },
  props: {
    deposit: {
      type: Object
    }
  },
  computed: {
    ...mapGetters('tokens', ['tokensByAddress']),
    token() {
      return this.tokensByAddress[this.deposit.token]
    },
    title() {
      return `Deposit ${this.token.code}`
    },
    modalId() {
      return `modal-${this.deposit.id}`
    }
  }
}
</script>
