<script setup>

</script>

<template>
  <div class="game">
    <h1>Игра</h1>
    <div class="game-quiz">
      <div class="game-quiz__question">
        <h3>Вопрос</h3>
        <p>Какой город является столицей России?</p>
      </div>
      <div class="game-quiz__answers">
        <button class="btn btn-light">Москва</button>
        <button class="btn btn-light">Санкт-Петербург</button>
        <button class="btn btn-light">Казань</button>
        <button class="btn btn-light">Сочи</button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.game {
  display: flex;
  justify-content: center;
  align-content: center;
  align-items: center;
  height: 100vh;
  width: 100vh;
  flex-direction: column;
  color: white;
}
</style>