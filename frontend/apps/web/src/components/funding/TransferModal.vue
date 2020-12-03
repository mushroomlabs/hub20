<template>
  <Modal :title="title" :id="modalId" label="transfer-modal" v-on="$listeners">
    <template>
      <TransferForm :token='token' />
    </template>
  </Modal>
</template>

<script>
import Modal from '@/widgets/dialogs/Modal'

import TransferForm from './TransferForm'

export default {
  components: {
    Modal,
    TransferForm
  },
  props: {
    token: {
      type: Object
    }
  },
  computed: {
    title() {
      return `Transfer ${this.token.code}`
    },
    modalId() {
      return `modal-transfer-${this.token.address}`
    },
  }
}
</script>
