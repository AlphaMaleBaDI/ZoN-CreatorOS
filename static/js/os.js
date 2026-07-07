/* CreatorOS — Alpine.js Application */

document.addEventListener('alpine:init', () => {
  Alpine.data('os', () => ({
    // Boot state
    phase: 'boot',
    bootSteps: [
      { id: 'workspace', label: 'Loading Workspace...', done: false, time: 0 },
      { id: 'profile', label: 'Loading Creator Profile...', done: false, time: 0 },
      { id: 'memory', label: 'Restoring Memory...', done: false, time: 0 },
      { id: 'context', label: 'Assembling Context...', done: false, time: 0 },
    ],
    bootDone: false,
    bootReady: false,
    elapsed: 0,
    bootStart: 0,

    // Dashboard state
    ready: false,
    wsName: 'ZoN Labs',
    creatorName: '',
    projectName: '',
    vibra: 'Creative',
    brand: '',
    phase: 'ideation',
    phaseNext: '',
    momentum: 0,
    momentumTotal: 1,
    avgConfidence: 0,
    artifactCount: 0,
    artifacts: [],
    providers: [],
    blockers: [],
    requirements: [],
    canTransition: false,

    // Pipeline
    pipelineStage: '',
    pipelineMessage: '',
    pipelineProgress: 0,
    pipelinePolling: false,
    pipelineTimer: null,
    pipelineSteps: [
      { id: 'orchestration', label: 'Planning', done: false, active: false },
      { id: 'snapshot', label: 'Snapshot', done: false, active: false },
      { id: 'eval', label: 'Eval', done: false, active: false },
      { id: 'pie', label: 'PIE', done: false, active: false },
      { id: 'complete', label: 'Complete', done: false, active: false },
    ],

    // Shell
    command: '',
    history: [],

    async boot() {
      this.bootStart = performance.now();

      // Step 1: Load workspace
      try {
        const t = performance.now();
        const wsRes = await fetch('/workspaces');
        const wsData = await wsRes.json();
        if (wsData.length > 0) {
          const ws = wsData[wsData.length - 1];
          this.wsName = ws.name;
          this.markBootStep('workspace', performance.now() - t);
        } else {
          this.markBootStep('workspace', 0);
        }
      } catch { this.markBootStep('workspace', 0); }

      // Step 2: Load profile
      try {
        const t = performance.now();
        const profRes = await fetch('/profiles');
        const profiles = await profRes.json();
        if (profiles && profiles.length > 0) {
          const name = profiles[profiles.length - 1];
          this.creatorName = name;
          const pRes = await fetch(`/profiles/${encodeURIComponent(name)}`);
          if (pRes.ok) {
            const pData = await pRes.json();
            this.vibra = pData.personality || 'Creative';
            this.brand = pData.brand_voice || '';
          }
          this.markBootStep('profile', performance.now() - t);
        } else {
          this.markBootStep('profile', 0);
        }
      } catch { this.markBootStep('profile', 0); }

      // Step 3: Load artifacts (memory)
      try {
        const t = performance.now();
        const wsRes = await fetch('/workspaces');
        const wsData = await wsRes.json();
        if (wsData.length > 0) {
          const wsId = wsData[wsData.length - 1].workspace_id;
          const artRes = await fetch(`/workspaces/${wsId}/artifacts`);
          if (artRes.ok) {
            const artData = await artRes.json();
            this.artifacts = artData;
            this.artifactCount = artData.length;
            this.providers = [...new Set(artData.map(a => a.provider).filter(Boolean))];
            const confs = artData.map(a => a.confidence).filter(c => c != null);
            this.avgConfidence = confs.length > 0
              ? Math.round(confs.reduce((a, b) => a + b, 0) / confs.length * 100) / 100
              : 0;
          }
          this.markBootStep('memory', performance.now() - t);
        } else {
          this.markBootStep('memory', 0);
        }
      } catch { this.markBootStep('memory', 0); }

      // Step 4: Load state
      try {
        const t = performance.now();
        const wsRes = await fetch('/workspaces');
        const wsData = await wsRes.json();
        if (wsData.length > 0) {
          const wsId = wsData[wsData.length - 1].workspace_id;
          const stateRes = await fetch(`/workspaces/${wsId}/state`);
          if (stateRes.ok) {
            const stateData = await stateRes.json();
            const sa = stateData.state_assessment;
            this.phase = sa.current_state;
            this.phaseNext = sa.next_state || '';
            this.blockers = sa.blockers || [];
            this.requirements = sa.requirements || [];
            this.canTransition = sa.can_transition;
            const reqEvidence = sa.evidence.filter(e =>
              Object.values(MUSIC_ARTIFACT_MAP).some(m => m.required_for_transition && e.artifact_type === Object.keys(MUSIC_ARTIFACT_MAP)[Object.values(MUSIC_ARTIFACT_MAP).findIndex(v => v.state === sa.current_state)])
            );
          }
          // Get project
          const projRes = await fetch(`/workspaces/${wsId}/projects`);
          if (projRes.ok) {
            const projs = await projRes.json();
            if (projs.length > 0) this.projectName = projs[0].name;
          }
          this.markBootStep('context', performance.now() - t);
        } else {
          this.markBootStep('context', 0);
        }
      } catch { this.markBootStep('context', 0); }

      // All boot steps done
      this.elapsed = performance.now() - this.bootStart;
      this.bootDone = true;
      this.$nextTick(() => {
        setTimeout(() => { this.bootReady = true; }, 200);
      });
    },

    markBootStep(id, time) {
      const step = this.bootSteps.find(s => s.id === id);
      if (step) {
        step.done = true;
        step.time = Math.round(time);
      }
    },

    finishBoot() {
      this.phase = 'contextSummary';
    },

    finishContext() {
      this.phase = 'dashboard';
      this.ready = true;
    },

    // Pipeline stage helpers
    isPipelineDone(stage) {
      const order = ['orchestration', 'snapshot', 'eval', 'pie', 'complete'];
      const currentIdx = order.indexOf(this.pipelineStage);
      const stageIdx = order.indexOf(stage);
      return stageIdx < currentIdx;
    },

    isPipelineActive(stage) {
      return this.pipelineStage === stage;
    },

    async executeCommand() {
      if (!this.command.trim()) return;
      const cmd = this.command;
      this.command = '';

      this.history.push({ prompt: 'creator@workspace', text: cmd });

      // Determine intent from command text
      const lower = cmd.toLowerCase();
      let intent = '';
      if (lower.includes('campaign') || lower.includes('strategy')) intent = 'campaign';
      else if (lower.includes('content') || lower.includes('calendar')) intent = 'content';
      else if (lower.includes('launch') || lower.includes('plan')) intent = 'launch_plan';

      if (!intent) {
        this.history.push({ prompt: '', text: 'Error: Command not recognized. Try "Launch", "Campaign", or "Content".', output: true });
        return;
      }

      // Start pipeline polling
      this.pipelinePolling = true;
      this.pipelineStage = 'orchestration';
      this.pipelineMessage = 'Starting...';
      this.startPipelinePolling();

      try {
        const wsRes = await fetch('/workspaces');
        const wsData = await wsRes.json();
        const wsId = wsData[wsData.length - 1]?.workspace_id;

        const res = await fetch('/generate-launch-plan', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            workspace_id: wsId,
            user_request: cmd,
          }),
        });

        if (res.ok) {
          this.history.push({ prompt: '', text: 'Artifact generated successfully.', output: true });
          // Refresh dashboard
          setTimeout(() => window.location.reload(), 1500);
        } else {
          this.history.push({ prompt: '', text: 'Error: Generation failed.', output: true });
        }
      } catch (e) {
        this.history.push({ prompt: '', text: `Error: ${e.message}`, output: true });
      }

      this.stopPipelinePolling();
    },

    startPipelinePolling() {
      this.pipelineTimer = setInterval(async () => {
        try {
          const res = await fetch('/pipeline/progress');
          if (res.ok) {
            const data = await res.json();
            if (data.stage) {
              this.pipelineStage = data.stage;
              this.pipelineMessage = data.message;
              this.pipelineProgress = data.progress;
            }
          }
        } catch { /* ignore polling errors */ }
      }, 200);
    },

    stopPipelinePolling() {
      if (this.pipelineTimer) {
        clearInterval(this.pipelineTimer);
        this.pipelineTimer = null;
      }
      this.pipelinePolling = false;
    },
  }));
});

// Artifact state map (mirrors core/pie.py for frontend use)
const MUSIC_ARTIFACT_MAP = {
  launch_plan: { state: "planning", required_for_transition: true },
  campaign_plan: { state: "planning", required_for_transition: true },
  content_calendar: { state: "production", required_for_transition: true },
  asset_checklist: { state: "production", required_for_transition: false },
  publishing_checklist: { state: "publishing", required_for_transition: true },
  release_complete: { state: "released", required_for_transition: true },
  press_release: { state: "publishing", required_for_transition: false },
  budget_plan: { state: "planning", required_for_transition: false },
  content_script: { state: "production", required_for_transition: false },
  production_schedule: { state: "production", required_for_transition: false },
  media_kit: { state: "publishing", required_for_transition: false },
  press_distribution: { state: "publishing", required_for_transition: false },
  resource_allocation: { state: "production", required_for_transition: false },
};

const STATE_ORDER = ["ideation", "planning", "production", "publishing", "released", "archived"];
