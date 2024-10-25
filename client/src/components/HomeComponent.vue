<template>
  <div class="buttons">
    <button @click="popupCreate" class="btn btn-light"><i class="bi bi-plus-square"></i> Создать комнату</button>
    <br/>
    <button @click="popupConnect" class="btn btn-light"><i class="bi bi-box-arrow-in-right"></i> Подключиться к комнате</button>
  </div>
  <create-room :show-popup="showPopupCreate" @closePopup="showPopupCreate = false" v-if="showPopupCreate" />
  <connect-room :show-popup="showPopupConnect" @closePopup="showPopupConnect = false" v-if="showPopupConnect"/>
</template>
<script setup>
import CreateRoom from "@/components/CreateRoom.vue";
import { ref } from "vue";
import ConnectRoom from "@/components/ConnectRoom.vue";
const showPopupCreate = ref(false)
const showPopupConnect = ref(false)

function popupCreate() {
  showPopupCreate.value = !showPopupCreate.value;
}

function popupConnect() {
  showPopupConnect.value = !showPopupConnect.value;
}
</script>
<style scoped>
.btn-light {
  width: 50%;
  height: 100px;
  font-size: 32px;
}
.buttons {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100vh;
  flex-direction: column;
}
</style>