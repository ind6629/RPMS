<script setup>
import { onMounted, ref, watch } from 'vue'
import http from '@/api/http'
import RpmsPagination from '@/components/RpmsPagination.vue'
import { unwrapPaginated } from '@/utils/unwrapPaginated'

const list = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(10)

const filterType = ref('')
const filterSearch = ref('')
const filterBuilding = ref('')
const filterOwner = ref('')

const opDialog = ref({
  show: false,
  type: 'success',
  title: '',
  lines: [],
})

const showImportModal = ref(false)
const importJsonText = ref('')
const importFileHint = ref('')

const bindPid = ref('')
const bindUid = ref('')

function showOpDialog(type, title, lines = []) {
  opDialog.value = {
    show: true,
    type,
    title,
    lines: Array.isArray(lines) ? lines : [String(lines)],
  }
}

function closeOpDialog() {
  opDialog.value.show = false
}

function emptyDraft() {
  return {
    key: `${Date.now()}-${Math.random().toString(36).slice(2, 9)}`,
    name: '',
    property_type: 'room',
    parent: '',
    building_number: '',
    unit_number: '',
    room_number: '',
    area: '',
    owner: '',
  }
}

const draftCards = ref([])

function addDraftCard() {
  draftCards.value.push(emptyDraft())
}

function removeDraft(key) {
  draftCards.value = draftCards.value.filter((d) => d.key !== key)
}

const typeLabel = {
  building: '楼栋',
  unit: '单元',
  room: '房屋',
}

async function loadList() {
  try {
    const params = {
      page: page.value,
      page_size: pageSize.value,
    }
    if (filterType.value) params.type = filterType.value
    if (filterSearch.value.trim()) params.search = filterSearch.value.trim()
    if (filterBuilding.value.trim()) params.building = filterBuilding.value.trim()
    if (filterOwner.value.trim()) params.owner = filterOwner.value.trim()
    const { data } = await http.get('/api/users/properties/', { params })
    const u = unwrapPaginated(data)
    list.value = u.list
    total.value = u.count
  } catch (e) {
    showOpDialog('error', '加载房产列表失败', [JSON.stringify(e.response?.data || e.message)])
  }
}

function onSearch() {
  page.value = 1
  loadList()
}

function resetFilters() {
  filterType.value = ''
  filterSearch.value = ''
  filterBuilding.value = ''
  filterOwner.value = ''
  page.value = 1
  loadList()
}

onMounted(loadList)

watch([page, pageSize], loadList)

async function batchCreateProperties() {
  if (!draftCards.value.length) {
    showOpDialog('warn', '请先添加卡片', ['请点击「新增」生成至少一张输入卡片后再执行一键添加。'])
    return
  }
  let ok = 0
  const errors = []
  for (let i = 0; i < draftCards.value.length; i++) {
    const d = draftCards.value[i]
    try {
      await http.post('/api/users/properties/', {
        name: d.name.trim() || `${d.building_number}-${d.unit_number}-${d.room_number}`.trim() || '未命名',
        property_type: d.property_type,
        parent: d.parent ? Number(d.parent) : null,
        building_number: d.building_number,
        unit_number: d.unit_number,
        room_number: d.room_number,
        area: d.area === '' ? null : Number(d.area) || null,
        owner: d.owner ? Number(d.owner) : null,
        status: true,
      })
      ok++
    } catch (e) {
      const detail = e.response?.data
      errors.push(
        `卡片 ${i + 1}：${typeof detail === 'object' ? JSON.stringify(detail) : e.message || '失败'}`,
      )
    }
  }
  if (ok && !errors.length) {
    showOpDialog('success', '新增完成', [`已成功添加 ${ok} 条房产。`])
  } else if (ok && errors.length) {
    showOpDialog('warn', '部分添加成功', [`成功 ${ok} 条，失败 ${errors.length} 条。`, ...errors])
  } else {
    showOpDialog('error', '新增失败', errors.length ? errors : ['未成功添加任何房产。'])
  }
  draftCards.value = []
  page.value = 1
  await loadList()
}

async function bindOwner() {
  if (!bindPid.value.trim()) {
    showOpDialog('warn', '缺少必要参数', ['请填写房产 ID。'])
    return
  }
  const pid = Number(bindPid.value)
  if (!Number.isInteger(pid) || pid <= 0) {
    showOpDialog('warn', '房产 ID 不合法', ['房产 ID 必须是大于 0 的整数。'])
    return
  }
  let ownerValue = null
  if (bindUid.value.trim()) {
    const uid = Number(bindUid.value)
    if (!Number.isInteger(uid) || uid <= 0) {
      showOpDialog('warn', '业主 ID 不合法', ['业主用户 ID 需为空（解绑）或大于 0 的整数。'])
      return
    }
    ownerValue = uid
  }
  try {
    await http.patch(`/api/users/properties/${pid}/`, {
      owner: ownerValue,
    })
    showOpDialog('success', ownerValue ? '绑定成功' : '解绑成功', [
      `房产 ID：${pid}`,
      ownerValue ? `已绑定业主 ID：${ownerValue}` : '已清空该房产的业主绑定。',
      '请在列表中查看“业主ID”和“业主账号”两列确认结果。',
    ])
    bindPid.value = ''
    bindUid.value = ''
    await loadList()
  } catch (e) {
    showOpDialog('error', '绑定/解绑失败', [
      `房产 ID：${pid}`,
      ownerValue ? `目标业主 ID：${ownerValue}` : '操作：解绑业主',
      JSON.stringify(e.response?.data || e.message),
    ])
  }
}

function openImportModal() {
  showImportModal.value = true
  importJsonText.value = ''
  importFileHint.value = ''
}

function closeImportModal() {
  showImportModal.value = false
}

function onImportFileChange(e) {
  const file = e.target.files?.[0]
  importFileHint.value = ''
  if (!file) return
  if (!/\.json$/i.test(file.name) && file.type && !file.type.includes('json')) {
    importFileHint.value = '建议选择 .json 文件'
  }
  const reader = new FileReader()
  reader.onload = () => {
    importJsonText.value = String(reader.result || '')
    importFileHint.value = `已载入：${file.name}`
  }
  reader.onerror = () => {
    importFileHint.value = '文件读取失败'
  }
  reader.readAsText(file, 'UTF-8')
  e.target.value = ''
}

async function confirmImport() {
  const raw = importJsonText.value.trim()
  if (!raw) {
    showOpDialog('warn', '缺少导入内容', ['请粘贴 JSON 数据或选择本地 JSON 文件。'])
    return
  }
  try {
    const rows = JSON.parse(raw)
    if (!Array.isArray(rows)) {
      showOpDialog('warn', '导入格式错误', ['根节点必须是 JSON 数组，例如：[{...},{...}]'])
      return
    }
    const { data: imp } = await http.post('/api/users/properties/bulk_import/', { rows })
    const n = typeof imp?.created === 'number' ? imp.created : rows.length
    showOpDialog('success', '导入完成', [
      `提交记录数：${rows.length}`,
      `成功写入：${n}`,
      '无效行会自动跳过。',
    ])
    closeImportModal()
    page.value = 1
    await loadList()
  } catch (e) {
    showOpDialog('error', '导入失败', [
      e.response?.data ? JSON.stringify(e.response.data) : e.message || '解析失败，请检查 JSON 格式。',
    ])
  }
}

const IMPORT_FORMAT_HINT = `批量导入（快速建房屋）JSON 数组格式示例：
[
  { "building_number": "1", "unit_number": "1", "room_number": "101", "area": 89.5 },
  { "building_number": "1", "unit_number": "1", "room_number": "102", "area": 92 }
]
说明：每条需包含楼栋号、单元号、房号；area 可选。系统将自动创建/关联楼栋与单元节点。`
</script>

<template>
  <div class="admin-props">
    <div class="rpms-panel admin-props__main">
      <div class="admin-props__toolbar">
        <h2 class="rpms-panel-title admin-props__title">房产管理</h2>
        <div class="admin-props__toolbar-actions">
          <a
            class="rpms-btn rpms-btn--secondary"
            href="/api/users/properties/export_csv/"
            target="_blank"
            rel="noreferrer"
        >导出表格</a
          >
          <button type="button" class="rpms-btn rpms-btn--secondary" @click="openImportModal">导入</button>
        </div>
      </div>

      <div class="admin-props__filters">
        <select v-model="filterType" class="rpms-select admin-props__filter">
          <option value="">全部类型</option>
          <option value="building">楼栋</option>
          <option value="unit">单元</option>
          <option value="room">房屋</option>
        </select>
        <input v-model="filterSearch" class="rpms-input admin-props__filter" placeholder="名称 / 楼栋 / 单元 / 房号" />
        <input
          v-model="filterBuilding"
          class="rpms-input admin-props__filter--narrow"
          placeholder="楼栋节点 ID"
        />
        <input v-model="filterOwner" class="rpms-input admin-props__filter--narrow" placeholder="业主用户 ID" />
        <button type="button" class="rpms-btn rpms-btn--primary" @click="onSearch">查询</button>
        <button type="button" class="rpms-btn rpms-btn--secondary" @click="resetFilters">重置</button>
      </div>

      <div class="rpms-table-wrap">
        <table class="rpms-table">
          <thead>
            <tr>
              <th>编号</th>
              <th>类型</th>
              <th>名称</th>
              <th>楼栋</th>
              <th>单元</th>
              <th>房号</th>
              <th>面积</th>
              <th>业主ID</th>
              <th>业主账号</th>
              <th>状态</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="p in list" :key="p.id">
              <td>{{ p.id }}</td>
              <td>{{ typeLabel[p.property_type] || p.property_type }}</td>
              <td>{{ p.name || '—' }}</td>
              <td>{{ p.building_number || '—' }}</td>
              <td>{{ p.unit_number || '—' }}</td>
              <td>{{ p.room_number || '—' }}</td>
              <td>{{ p.area ?? '—' }}</td>
              <td>{{ p.owner ?? '—' }}</td>
              <td>{{ p.owner_name || '—' }}</td>
              <td>{{ p.status ? '启用' : '禁用' }}</td>
            </tr>
          </tbody>
        </table>
      </div>
      <RpmsPagination
        :page="page"
        :page-size="pageSize"
        :total="total"
        @update:page="page = $event"
        @update:page-size="pageSize = $event"
      />

      <div class="admin-props__add-section">
        <div class="admin-props__add-head">
          <h3 class="admin-props__sub-title">新增房产</h3>
          <button type="button" class="rpms-btn rpms-btn--secondary" @click="addDraftCard">新增</button>
        </div>
        <p class="rpms-muted admin-props__add-tip">
          可多次点击「新增」生成多张卡片，分别填写后点击「一键添加」依次提交；留空名称时将自动组合楼栋-单元-房号。
        </p>
        <div v-if="draftCards.length" class="admin-props__draft-grid">
          <div v-for="d in draftCards" :key="d.key" class="admin-props__draft-card">
            <div class="admin-props__draft-card-head">
              <span>新建项</span>
              <button type="button" class="admin-props__draft-remove" title="移除此卡片" @click="removeDraft(d.key)">
                ×
              </button>
            </div>
            <label class="admin-props__mini-label">类型</label>
            <select v-model="d.property_type" class="rpms-select admin-props__draft-input">
              <option value="building">楼栋</option>
              <option value="unit">单元</option>
              <option value="room">房屋</option>
            </select>
            <label class="admin-props__mini-label">名称（可空）</label>
            <input v-model="d.name" class="rpms-input admin-props__draft-input" placeholder="显示名称" />
            <label class="admin-props__mini-label">父节点 ID（可空）</label>
            <input v-model="d.parent" class="rpms-input admin-props__draft-input" placeholder="上级房产 ID" />
            <label class="admin-props__mini-label">楼栋号</label>
            <input v-model="d.building_number" class="rpms-input admin-props__draft-input" placeholder="如 1" />
            <label class="admin-props__mini-label">单元号</label>
            <input v-model="d.unit_number" class="rpms-input admin-props__draft-input" placeholder="如 1" />
            <label class="admin-props__mini-label">房号</label>
            <input v-model="d.room_number" class="rpms-input admin-props__draft-input" placeholder="如 101" />
            <label class="admin-props__mini-label">面积（可空）</label>
            <input v-model="d.area" class="rpms-input admin-props__draft-input" placeholder="㎡" />
            <label class="admin-props__mini-label">业主用户 ID（可空）</label>
            <input v-model="d.owner" class="rpms-input admin-props__draft-input" placeholder="用户 ID" />
          </div>
        </div>
        <div v-if="draftCards.length" class="admin-props__batch-actions">
          <button type="button" class="rpms-btn rpms-btn--primary" @click="batchCreateProperties">一键添加</button>
        </div>
      </div>

      <div class="admin-props__bind">
        <h3 class="admin-props__sub-title">快捷绑定业主</h3>
        <div class="rpms-form-row" style="margin: 0">
          <input v-model="bindPid" class="rpms-input" placeholder="房产 ID" />
          <input v-model="bindUid" class="rpms-input" placeholder="业主用户 ID（可空表示解绑）" />
          <button type="button" class="rpms-btn rpms-btn--secondary" @click="bindOwner">绑定</button>
        </div>
      </div>
    </div>

    <Teleport to="body">
      <div v-if="showImportModal" class="admin-props__modal-root" role="dialog" aria-modal="true" aria-labelledby="import-title">
        <div class="admin-props__modal-backdrop" @click="closeImportModal" />
        <div class="admin-props__modal">
          <h2 id="import-title" class="admin-props__modal-title">导入房产数据</h2>
          <p class="admin-props__modal-format">{{ IMPORT_FORMAT_HINT }}</p>
          <label class="admin-props__mini-label">粘贴 JSON</label>
          <textarea
            v-model="importJsonText"
            class="rpms-textarea admin-props__modal-textarea"
            rows="10"
            placeholder="将 JSON 数组粘贴到此处…"
          />
          <label class="admin-props__mini-label">或选择本地 JSON 文件</label>
          <input type="file" accept=".json,application/json" class="admin-props__file" @change="onImportFileChange" />
          <p v-if="importFileHint" class="rpms-muted" style="margin: 8px 0 0">{{ importFileHint }}</p>
          <div class="admin-props__modal-actions">
            <button type="button" class="rpms-btn rpms-btn--secondary" @click="closeImportModal">取消</button>
            <button type="button" class="rpms-btn rpms-btn--primary" @click="confirmImport">开始导入</button>
          </div>
        </div>
      </div>
    </Teleport>
    <Teleport to="body">
      <div v-if="opDialog.show" class="admin-props__modal-root" role="dialog" aria-modal="true" aria-labelledby="op-title">
        <div class="admin-props__modal-backdrop" @click="closeOpDialog" />
        <div class="admin-props__modal admin-props__modal--result">
          <h2 id="op-title" class="admin-props__modal-title">
            <span
              class="admin-props__result-tag"
              :class="{
                'admin-props__result-tag--ok': opDialog.type === 'success',
                'admin-props__result-tag--warn': opDialog.type === 'warn',
                'admin-props__result-tag--err': opDialog.type === 'error',
              }"
            >
              {{ opDialog.type === 'success' ? '成功' : opDialog.type === 'warn' ? '提示' : '失败' }}
            </span>
            {{ opDialog.title }}
          </h2>
          <ul v-if="opDialog.lines.length" class="admin-props__result-lines">
            <li v-for="(line, idx) in opDialog.lines" :key="idx">{{ line }}</li>
          </ul>
          <div class="admin-props__modal-actions">
            <button type="button" class="rpms-btn rpms-btn--primary" @click="closeOpDialog">我知道了</button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<style scoped>
.admin-props__main {
  padding-bottom: 28px;
}

.admin-props__toolbar {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 8px;
}

.admin-props__title {
  margin-bottom: 0;
  padding-bottom: 0;
  border: none;
}

.admin-props__toolbar-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.admin-props__filters {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  align-items: center;
  margin: 18px 0 16px;
  padding: 14px 16px;
  background: rgba(42, 110, 187, 0.04);
  border: 1px solid rgba(42, 110, 187, 0.1);
  border-radius: 14px;
}

.admin-props__filter {
  min-width: 160px;
  flex: 1;
}

.admin-props__filter--narrow {
  width: 140px;
  min-width: 120px;
}

.admin-props__add-section {
  margin-top: 28px;
  padding-top: 22px;
  border-top: 1px solid var(--rpms-card-border, #e2e8f0);
}

.admin-props__add-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
}

.admin-props__sub-title {
  margin: 0;
  font-size: 1rem;
  font-weight: 700;
  color: var(--rpms-text, #0f172a);
}

.admin-props__add-tip {
  margin: 10px 0 16px;
  font-size: 13px;
}

.admin-props__draft-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  gap: 14px;
  margin-bottom: 16px;
}

.admin-props__draft-card {
  padding: 14px 14px 16px;
  border-radius: 14px;
  border: 1px solid rgba(42, 110, 187, 0.18);
  background: linear-gradient(165deg, rgba(255, 255, 255, 0.95) 0%, rgba(248, 250, 252, 0.98) 100%);
  box-shadow: 0 4px 16px rgba(15, 23, 42, 0.05);
  transition:
    box-shadow 0.2s ease,
    border-color 0.2s ease;
}

.admin-props__draft-card:hover {
  border-color: rgba(42, 110, 187, 0.35);
  box-shadow: 0 8px 22px rgba(42, 110, 187, 0.08);
}

.admin-props__draft-card-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 10px;
  font-size: 13px;
  font-weight: 600;
  color: var(--rpms-primary, #2a6ebb);
}

.admin-props__draft-remove {
  width: 28px;
  height: 28px;
  border: none;
  border-radius: 8px;
  background: rgba(220, 38, 38, 0.08);
  color: #b91c1c;
  font-size: 18px;
  line-height: 1;
  cursor: pointer;
  transition: background 0.15s ease;
}

.admin-props__draft-remove:hover {
  background: rgba(220, 38, 38, 0.18);
}

.admin-props__mini-label {
  display: block;
  font-size: 11px;
  font-weight: 600;
  color: var(--rpms-text-muted, #64748b);
  margin-top: 8px;
  margin-bottom: 4px;
}

.admin-props__mini-label:first-of-type {
  margin-top: 0;
}

.admin-props__draft-input {
  width: 100%;
}

.admin-props__batch-actions {
  display: flex;
  justify-content: flex-end;
}

.admin-props__bind {
  margin-top: 24px;
  padding-top: 20px;
  border-top: 1px dashed var(--rpms-card-border, #e2e8f0);
}

.admin-props__modal-root {
  position: fixed;
  inset: 0;
  z-index: 2000;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
}

.admin-props__modal-backdrop {
  position: absolute;
  inset: 0;
  background: rgba(15, 23, 42, 0.45);
  backdrop-filter: blur(4px);
}

.admin-props__modal {
  position: relative;
  z-index: 1;
  width: 100%;
  max-width: 560px;
  max-height: min(90vh, 720px);
  overflow: auto;
  padding: 24px 26px;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.96);
  border: 1px solid rgba(226, 232, 240, 0.95);
  box-shadow: 0 24px 48px rgba(15, 23, 42, 0.18);
  animation: modal-in 0.25s ease;
}

@keyframes modal-in {
  from {
    opacity: 0;
    transform: scale(0.96) translateY(8px);
  }
  to {
    opacity: 1;
    transform: none;
  }
}

.admin-props__modal-title {
  margin: 0 0 12px;
  font-size: 1.15rem;
  font-weight: 800;
  color: var(--rpms-text, #0f172a);
}

.admin-props__modal-format {
  margin: 0 0 16px;
  padding: 12px 14px;
  font-size: 12px;
  line-height: 1.55;
  color: #475569;
  background: rgba(42, 110, 187, 0.06);
  border-radius: 12px;
  border: 1px solid rgba(42, 110, 187, 0.12);
  white-space: pre-wrap;
}

.admin-props__modal-textarea {
  width: 100%;
  box-sizing: border-box;
  font-family: ui-monospace, 'Cascadia Code', monospace;
  font-size: 13px;
}

.admin-props__file {
  font-size: 14px;
}

.admin-props__modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 18px;
}

.admin-props__modal--result {
  max-width: 520px;
}

.admin-props__result-tag {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 52px;
  height: 28px;
  margin-right: 10px;
  padding: 0 10px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 700;
  vertical-align: middle;
}

.admin-props__result-tag--ok {
  color: #15803d;
  background: rgba(22, 163, 74, 0.12);
}

.admin-props__result-tag--warn {
  color: #c2410c;
  background: rgba(234, 88, 12, 0.14);
}

.admin-props__result-tag--err {
  color: #b91c1c;
  background: rgba(220, 38, 38, 0.12);
}

.admin-props__result-lines {
  margin: 0;
  padding: 0 0 0 18px;
  color: #334155;
  line-height: 1.6;
}
</style>
