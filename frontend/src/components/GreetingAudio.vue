<script setup lang="ts">
defineProps<{
  src: string
  title: string
}>()
</script>

<template>
  <div class="greetings">
    <h3 style="color: #2b2f3a">{{ title }}</h3>
    <audio class="greetings-audio" controls :src="src"></audio>
  </div>
</template>

<style scoped>
h1 {
  font-weight: 500;
  font-size: 2.6rem;
  top: -10px;
}

h3 {
  font-size: 1.2rem;
}

.greetings {
  position: fixed;
  bottom: 0;
  right: 30px;
  background-color: #3498db;
  box-shadow: 0 0 10px rgba(0, 0, 0, 0.5);
  border-radius: 10px;
  color: #fff;
  padding: 10px;
}

.greetings h3 {
  text-align: left;
  margin: 10px;
}

@media (min-width: 1024px) {
  .greetings h3 {
    text-align: left;
  }
}
</style>
