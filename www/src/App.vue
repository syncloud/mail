<template>
  <el-container class="page">
    <el-header class="header">
      <h2 data-testid="admin-title">Mail admin</h2>
      <el-link href="/" data-testid="nav-mail">&larr; Back to mail</el-link>
    </el-header>
    <el-main>
      <RelayForm />
    </el-main>
  </el-container>
</template>

<script setup>
import RelayForm from './components/RelayForm.vue'
</script>

<style>
.page {
  max-width: 640px;
  margin: 0 auto;
}
.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
</style>
