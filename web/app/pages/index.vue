<script setup lang="ts">
const cop = useContractCop()

const composer = ref<InstanceType<typeof ClaimComposer> | null>(null)
const trDlg = ref<InstanceType<typeof TranscriptDialog> | null>(null)
const rDlg = ref<InstanceType<typeof ReportDialog> | null>(null)

onMounted(() => {
  cop.loadHealth()
  cop.loadClauses()
})
</script>

<template>
  <div>
    <TopBar
      :session="cop.session.value"
      @transcript="trDlg?.open()"
      @report="rDlg?.open()"
    />
    <div class="frame">
      <ClauseRail
        :clauses="cop.clauses.value"
        :health="cop.health.value"
        :rail-error="cop.railError.value"
        @retry="cop.loadClauses"
      />
      <main class="content">
        <h1>Every claim, checked against the signed contract.</h1>
        <p class="sub">
          Paste what the rep said. The verdict cites the clause, the policy, the
          SQL and the model.
        </p>
        <ClaimComposer
          ref="composer"
          :checked="cop.checked.value"
          :contradictions="cop.contradictions.value"
          :session="cop.session.value"
          :busy="!!cop.pending.value && !cop.pending.value.progress"
          @submit="cop.checkClaim"
        />
        <section class="feed" aria-live="polite">
          <EmptyState
            v-if="!cop.events.value.length && !cop.pending.value"
            @suggest="composer?.fill($event)"
          />
          <ClaimRow v-for="(e, i) in cop.events.value" :key="i" :e="e" />
          <PendingRow v-if="cop.pending.value" :pending="cop.pending.value" />
        </section>
      </main>
    </div>
    <TranscriptDialog ref="trDlg" @run="cop.runTranscript" />
    <ReportDialog ref="rDlg" />
  </div>
</template>

<style scoped>
.frame { display: flex; min-height: calc(100vh - 52px); }
.content {
  flex: 1;
  min-width: 0;
  max-width: 760px;
  padding: 48px 40px 96px;
}
h1 {
  font-size: 56px;
  font-weight: 300;
  letter-spacing: -0.03em;
  line-height: 1;
  margin-bottom: 16px;
}
.sub {
  color: var(--ink-2);
  font-weight: 300;
  margin-bottom: 36px;
  max-width: 560px;
}
.feed {
  margin-top: 32px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}
@media (max-width: 900px) {
  .content { padding: 40px 20px 80px; }
  h1 { font-size: 40px; }
}
</style>
