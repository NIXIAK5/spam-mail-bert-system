<template>
  <div class="page-header">
    <h3>{{ title }}</h3>
    <p v-if="subtitle" class="subtitle">{{ subtitle }}</p>
  </div>
</template>

<script setup>
defineProps({
  title: { type: String, required: true },
  subtitle: { type: String, default: '' },
})
</script>

<style scoped>
.page-header {
  margin-bottom: 20px;
}
.page-header h3 {
  margin: 0 0 4px 0;
  color: #303133;
}
.subtitle {
  color: #909399;
  font-size: 14px;
  margin: 0;
}
</style>
