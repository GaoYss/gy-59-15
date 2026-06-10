<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { Search } from 'lucide-vue-next'

import { scoreApi } from '../api/modules'
import DataTable from '../components/DataTable.vue'
import EmptyState from '../components/EmptyState.vue'
import MessageBar from '../components/MessageBar.vue'
import StatusBadge from '../components/StatusBadge.vue'
import { subjects } from '../constants/options'

const scores = ref([])
const stats = ref([])
const loading = ref(false)
const message = reactive({ text: '', type: 'info' })
const filters = reactive({ studentName: '', subject: '' })

const columns = [
  { key: 'studentName', label: '学员' },
  { key: 'subject', label: '科目' },
  { key: 'score', label: '分数' },
  { key: 'correctCount', label: '答对' },
  { key: 'passed', label: '结果' },
  { key: 'submittedAt', label: '提交时间' }
]

const isStudentFiltered = computed(() => Boolean(filters.studentName.trim()))

const hasAnyStudentRecord = computed(() => {
  if (!isStudentFiltered.value) return false
  return scores.value.length > 0
})

const statsTitle = computed(() => {
  if (isStudentFiltered.value) {
    return `${filters.studentName.trim()} 科目成绩`
  }
  return '科目统计'
})

const studentSubjectRecords = computed(() => {
  if (!isStudentFiltered.value) return []
  const grouped = new Map()
  for (const record of scores.value) {
    if (!grouped.has(record.subject)) {
      grouped.set(record.subject, [])
    }
    grouped.get(record.subject).push(record)
  }
  return subjects
    .filter((s) => !filters.subject || s === filters.subject)
    .map((subject) => {
      const records = (grouped.get(subject) || []).slice().sort(
        (a, b) => new Date(b.submittedAt) - new Date(a.submittedAt)
      )
      return {
        subject,
        records
      }
    })
    .filter((group) => group.records.length > 0)
})

async function loadScores() {
  loading.value = true
  message.text = ''
  try {
    const params = {}
    if (filters.studentName) params.studentName = filters.studentName
    if (filters.subject) params.subject = filters.subject

    const requests = [scoreApi.list(params)]
    if (!isStudentFiltered.value) {
      requests.push(scoreApi.stats(params))
    }

    const [scoreList, statsList] = await Promise.all(requests)
    scores.value = scoreList
    if (statsList !== undefined) {
      stats.value = statsList
    }
  } catch (error) {
    message.text = error.message
    message.type = 'error'
  } finally {
    loading.value = false
  }
}

onMounted(loadScores)
</script>

<template>
  <section class="panel">
    <div class="panel-heading">
      <div>
        <h3>成绩查询</h3>
        <p>按学员或科目筛选模拟考试记录。</p>
      </div>
    </div>

    <form class="toolbar" @submit.prevent="loadScores">
      <label>
        <span>学员姓名</span>
        <input v-model.trim="filters.studentName" placeholder="输入姓名检索" />
      </label>
      <label>
        <span>科目</span>
        <select v-model="filters.subject">
          <option value="">全部科目</option>
          <option v-for="subject in subjects" :key="subject">{{ subject }}</option>
        </select>
      </label>
      <button class="primary-button inline-button" type="submit" :disabled="loading">
        <Search :size="18" />
        <span>查询</span>
      </button>
    </form>

    <MessageBar :message="message.text" :type="message.type" />

    <div class="stats-section" :class="{ 'is-loading': loading }">
      <div class="stats-heading">
        <h4>{{ statsTitle }}</h4>
        <span v-if="loading" class="stats-loading">加载中...</span>
      </div>

      <div v-if="!isStudentFiltered && stats.length" class="stats-grid">
        <div
          v-for="item in stats"
          :key="item.subject"
          class="stat-card"
          :class="{ 'stat-card--danger': item.passRate < 60 }"
        >
          <div class="stat-card-header">
            <span class="stat-subject">{{ item.subject }}</span>
            <span class="stat-total">共 {{ item.total }} 人</span>
          </div>
          <div class="stat-metrics">
            <div class="stat-metric">
              <span class="stat-value">{{ item.avgScore }}</span>
              <span class="stat-label">平均分</span>
            </div>
            <div class="stat-metric">
              <span class="stat-value">{{ item.maxScore }}</span>
              <span class="stat-label">最高分</span>
            </div>
            <div class="stat-metric">
              <span class="stat-value stat-value--danger">{{ item.failCount }}</span>
              <span class="stat-label">未通过</span>
            </div>
            <div class="stat-metric">
              <span
                class="stat-value"
                :class="item.passRate < 60 ? 'stat-value--danger' : 'stat-value--success'"
              >{{ item.passRate }}%</span>
              <span class="stat-label">及格率</span>
            </div>
          </div>
        </div>
      </div>

      <div v-else-if="isStudentFiltered && hasAnyStudentRecord" class="stats-grid">
        <div
          v-for="group in studentSubjectRecords"
          :key="group.subject"
          class="stat-card"
          :class="{ 'stat-card--danger': group.records.some(r => !r.passed) }"
        >
          <div class="stat-card-header">
            <span class="stat-subject">{{ group.subject }}</span>
            <span class="stat-total">共 {{ group.records.length }} 次</span>
          </div>
          <div class="attempt-list">
            <div
              v-for="(record, index) in group.records"
              :key="record.id"
              class="attempt-row"
            >
              <span class="attempt-index">第 {{ index + 1 }} 次</span>
              <span
                class="attempt-score"
                :class="record.passed ? 'stat-value--success' : 'stat-value--danger'"
              >{{ record.score }} 分</span>
              <StatusBadge :status="record.passed ? '合格' : '不合格'" />
              <span class="attempt-time">{{ record.submittedAt }}</span>
            </div>
          </div>
        </div>
      </div>

      <div v-else-if="isStudentFiltered && !hasAnyStudentRecord" class="stats-empty">
        该学员暂无成绩
      </div>

      <div v-else class="stats-empty">暂无统计数据</div>
    </div>

    <EmptyState v-if="!loading && scores.length === 0" title="暂无成绩" description="模拟考试提交后会生成成绩。" />
    <DataTable v-else :columns="columns" :rows="scores">
      <template #passed="{ row }">
        <StatusBadge :status="row.passed ? '合格' : '不合格'" />
      </template>
      <template #correctCount="{ row }">
        {{ row.correctCount }} / {{ row.totalQuestions }}
      </template>
    </DataTable>
  </section>
</template>
