<template>
  <el-card>
    <template #header>
      <span>Outbound relay (smarthost)</span>
    </template>
    <el-alert
      type="info"
      :closable="false"
      show-icon
      title="Send outbound mail through an authenticated relay"
      description="Many providers (Gmail, Outlook) reject mail sent directly from home/self-hosted IPs, and some ISPs block port 25. Route outbound mail through a trusted relay to fix delivery."
    />
    <el-form label-width="140px" class="form">
      <el-form-item label="Enabled">
        <el-switch v-model="relay.enabled" data-testid="relay-enabled" />
      </el-form-item>
      <el-form-item label="Relay host">
        <el-input
          v-model="relay.host"
          data-testid="relay-host"
          placeholder="smtp.gmail.com"
          :disabled="!relay.enabled"
        />
      </el-form-item>
      <el-form-item label="Port">
        <el-input
          v-model.number="relay.port"
          data-testid="relay-port"
          type="number"
          :disabled="!relay.enabled"
        />
      </el-form-item>
      <el-form-item label="Username">
        <el-input
          v-model="relay.user"
          data-testid="relay-user"
          placeholder="user@gmail.com"
          :disabled="!relay.enabled"
        />
      </el-form-item>
      <el-form-item label="Password">
        <el-input
          v-model="relay.password"
          data-testid="relay-password"
          type="password"
          show-password
          placeholder="leave blank to keep current"
          :disabled="!relay.enabled"
        />
      </el-form-item>
      <el-form-item>
        <el-button
          type="primary"
          data-testid="relay-save"
          :loading="saving"
          @click="save"
        >
          Save
        </el-button>
      </el-form-item>
    </el-form>
  </el-card>
</template>

<script setup>
import { reactive, ref, onMounted } from 'vue'
import axios from 'axios'
import { ElMessage } from 'element-plus'

const relay = reactive({ enabled: false, host: '', port: 587, user: '', password: '' })
const saving = ref(false)

async function load () {
  try {
    const { data } = await axios.get('/api/relay')
    Object.assign(relay, data.data)
  } catch (err) {
    ElMessage.error(message(err))
  }
}

async function save () {
  saving.value = true
  try {
    await axios.post('/api/relay', relay)
    ElMessage.success('Saved')
    await load()
  } catch (err) {
    ElMessage.error(message(err))
  } finally {
    saving.value = false
  }
}

function message (err) {
  return err.response?.data?.message ?? err.message
}

onMounted(load)
</script>

<style>
.form {
  margin-top: 20px;
}
</style>
