<script setup>

</script>

<template>
  <div class="container mt-5">
    <div class="row justify-content-center">
      <div class="col-md-6">
        <div class="card">
          <div class="card-header">
            <h3 class="text-center">Войти</h3>
          </div>
          <div class="card-body">
            <form @submit.prevent="handleSubmit">
              <div class="form-group mb-3">
                <label for="username">Имя пользователя</label>
                <input
                    type="text"
                    id="username"
                    class="form-control"
                    v-model="username"
                    required
                />
              </div>
              <div class="form-group mb-3">
                <label for="password">Пароль</label>
                <input
                    type="password"
                    id="password"
                    class="form-control"
                    v-model="password"
                    required
                />
              </div>
              <button type="submit" class="btn btn-primary w-100">Login</button>
            </form>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>

</style>