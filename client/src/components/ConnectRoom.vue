<template>
  <div v-if="showPopup" class="popup-overlay">
    <div class="popup-content">
      <h3>Подключиться к комнате</h3>
      <input  type="text" class="input-group" placeholder="Ссылка на комнату"/>
      <div class="popup-actions">
        <button class="btn btn-success">Подключиться</button>
        <button class="btn btn-dark" @click="$emit('closePopup')">Закрыть</button>
      </div>
    </div>
  </div>
</template>
<script setup>
defineProps({
  showPopup: Boolean,
  closePopup: Boolean,
})
</script>
<style scoped>
.popup-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
}
.popup-content {
  background-color: #fff;
  padding: 20px;
  border-radius: 5px;
  width: 500px;
  height: 200px;
  text-align: center;
}
.popup-actions {
  margin-top: 15px;
}
.popup-actions button {
  margin: 5px;
}
</style>