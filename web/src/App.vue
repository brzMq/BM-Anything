<script setup lang="ts">
import { onMounted, ref } from 'vue'

interface Health {
  status: string
  service: string
  version: string
}

interface Ready {
  status: string
  profile: string
  database: { ok: boolean; url: string; detail: string | null }
}

const health = ref<Health | null>(null)
const ready = ref<Ready | null>(null)
const error = ref<string | null>(null)
const loading = ref(true)

async function probe() {
  loading.value = true
  error.value = null
  try {
    const [h, r] = await Promise.all([
      fetch('/api/health').then((x) => x.json() as Promise<Health>),
      fetch('/api/health/ready').then((x) => x.json() as Promise<Ready>),
    ])
    health.value = h
    ready.value = r
  } catch (e) {
    error.value = e instanceof Error ? e.message : String(e)
  } finally {
    loading.value = false
  }
}

onMounted(probe)
</script>

<template>
  <main class="shell">
    <header>
      <h1>BM-Anything</h1>
      <p class="sub">Local-first AI Capability Platform · P0 Foundation</p>
    </header>

    <section class="card">
      <h2>后端健康检查</h2>
      <button :disabled="loading" @click="probe">
        {{ loading ? '探测中…' : '重新探测' }}
      </button>

      <p v-if="error" class="err">无法连接后端：{{ error }}</p>

      <dl v-if="health">
        <dt>状态</dt><dd>{{ health.status }}</dd>
        <dt>服务</dt><dd>{{ health.service }}</dd>
        <dt>版本</dt><dd>{{ health.version }}</dd>
      </dl>

      <dl v-if="ready">
        <dt>Profile</dt><dd>{{ ready.profile }}</dd>
        <dt>数据库</dt>
        <dd>
          {{ ready.database.ok ? '可达' : '不可达' }}
          <code>{{ ready.database.url }}</code>
        </dd>
      </dl>
    </section>

    <footer>
      <span>前端：Vue 3 + TypeScript + Vite</span>
      <span>后端：FastAPI + SQLAlchemy + SQLite</span>
    </footer>
  </main>
</template>

<style scoped>
.shell {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  max-width: 720px;
  margin: 0 auto;
  padding: 2rem 1.5rem;
  color: #1f2937;
}
header h1 {
  margin: 0;
  font-size: 1.75rem;
}
.sub {
  margin: 0.25rem 0 1.5rem;
  color: #6b7280;
}
.card {
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  padding: 1.25rem 1.5rem;
  background: #fff;
}
.card h2 {
  margin-top: 0;
  font-size: 1.1rem;
}
button {
  background: #6d28d9;
  color: #fff;
  border: 0;
  border-radius: 8px;
  padding: 0.5rem 1rem;
  font-size: 0.9rem;
  cursor: pointer;
}
button:hover:not(:disabled) {
  background: #5b21b6;
}
button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
dl {
  display: grid;
  grid-template-columns: max-content 1fr;
  gap: 0.4rem 1rem;
  margin: 1rem 0 0;
}
dt {
  color: #6b7280;
}
dd {
  margin: 0;
}
code {
  background: #f3f4f6;
  padding: 0.1rem 0.35rem;
  border-radius: 4px;
  font-size: 0.85em;
}
.err {
  color: #b91c1c;
  margin-top: 0.75rem;
}
footer {
  margin-top: 1.5rem;
  display: flex;
  gap: 1rem;
  justify-content: space-between;
  color: #9ca3af;
  font-size: 0.8rem;
}
</style>
