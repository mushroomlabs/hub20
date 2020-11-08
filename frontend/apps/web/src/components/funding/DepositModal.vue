<template>
  <Modal :title="title" :id="modalId" label="deposit-modal" @modalClosed="onClose()">
    <template>
      <PaymentRequest :paymentRequest='deposit' />
    </template>
  </Modal>
</template>

<script>
import {mapGetters, mapMutations} from 'vuex'
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
    },
  },
  methods: {
    ...mapMutations('funding', {cancelDeposit: 'FUNDING_DEPOSIT_SET_CLOSED'}),
    onClose() {
      this.cancelDeposit(this.deposit.id)
    }
  }
}
</script>
