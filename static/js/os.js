document.addEventListener('alpine:init', () => {
  Alpine.data('os', () => ({
    // App mode: 'boot' | 'onboarding' | 'assembling' | 'dashboard'
    mode: 'boot',

    // Boot state
    showTagline: false,
    logoLit: false,
    bootSteps: [
      { id: 'kernel', label: 'Initializing Kernel...', done: false },
      { id: 'workspace', label: 'Mounting Workspace...', done: false },
      { id: 'identity', label: 'Loading Creator Identity...', done: false },
      { id: 'memory', label: 'Restoring Production Memory...', done: false },
      { id: 'context', label: 'Assembling Context...', done: false },
      { id: 'intelligence', label: 'Synchronizing Intelligence...', done: false },
    ],
    bootDone: false,
    bootReady: false,
    elapsed: 0,
    bootStart: 0,

    // Onboarding state
    sessionId: '',
    onboardingMessages: [],
    onboardingInput: '',
    onboardingDone: false,

    // Assembly state
    assemblySteps: [
      { label: 'Building workspace', done: false },
      { label: 'Creating profile', done: false },
      { label: 'Initializing project', done: false },
      { label: 'Connecting production memory', done: false },
      { label: 'Assembling context', done: false },
      { label: 'Synchronizing intelligence', done: false },
    ],

    // Dashboard state
    ready: false,
    wsName: 'ZoN Labs',
    wsId: '',
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

    // Computed: Creator State panel
    get mindUnderstanding() {
      const total = this.mind.beliefs.length + this.mind.tensions.length + Math.min(this.mind.version, 10);
      const active = this.mind.beliefs.filter(b => b.lifecycle === 'active').length;
      const tensions = this.mind.tensions.filter(t => t.status === 'active').length;
      if (total === 0) return 0;
      const raw = ((active * 15) + (tensions * -5) + (Math.min(this.mind.version, 10) * 5) + (Math.min(this.mind.observations.length, 20) * 2));
      return Math.max(0, Math.min(100, Math.round(raw)));
    },
    get mindConfidence() {
      const beliefs = this.mind.beliefs;
      if (beliefs.length === 0) return 0;
      const avg = beliefs.reduce((s, b) => s + b.confidence, 0) / beliefs.length;
      return Math.round(avg * 100);
    },
    get mindTensionsActive() {
      return this.mind.tensions.filter(t => t.status === 'active').length;
    },
    get recentTensions() {
      return this.mind.tensions.filter(t => t.status === 'active').slice(-3);
    },
    get recentBeliefs() {
      return this.mind.beliefs.filter(b => b.lifecycle === 'active' || b.lifecycle === 'challenged').slice(-3).reverse();
    },
    get confirmedBeliefs() {
      return this.mind.beliefs.filter(b => b.lifecycle === 'active').slice(0, 5);
    },

    // Artifact viewer
    selectedArtifact: { type: '', provider: '', confidence: '', data: {}, loaded: false },

    // Creator State (Observer Mode — Mission 016B)
    mind: { version: 0, observations: [], beliefs: [], tensions: [] },

    // Shadow Reasoning (Mission 017B)
    reasoning: { reflection: '', confidence: 0, suggested_action: '', reasoning_trace: [], unanswered_questions: [], risks: [], opportunities: [] },
    showTrace: false,

    // Shell
    command: '',
    history: [],
    pendingCheckpoint: null,
    pendingProposal: null,
    generatedArtifact: '',
    showArtifactViewer: false,
    autoScroll: true,
    recentlyGenerated: '',
    consoleHeight: parseInt(localStorage.getItem('command_console_height') || '220'),
    consoleDragging: false,
    dragStartY: 0,
    dragStartHeight: 0,

    // ─── BOOT ───────────────────────────────────────────

    async boot() {
      this.bootStart = performance.now();

      this.showTagline = true;
      await this.sleep(800);
      this.logoLit = true;
      await this.sleep(1200);

      await this.sleep(400);
      this.markBootStep('kernel');

      await this.sleep(300);

      // Check if onboarding is needed
      let needsOnboarding = false;
      try {
        const res = await fetch('/onboarding/status');
        const data = await res.json();
        needsOnboarding = data.needs_onboarding;
        if (!needsOnboarding && data.workspace_id) {
          this.wsId = data.workspace_id;
        }
      } catch { /* skip */ }

      this.markBootStep('workspace');
      await this.sleep(200);
      this.markBootStep('identity');
      await this.sleep(200);
      this.markBootStep('memory');
      await this.sleep(200);
      this.markBootStep('context');
      await this.sleep(200);
      this.markBootStep('intelligence');

      this.elapsed = performance.now() - this.bootStart;
      this.bootDone = true;
      setTimeout(() => { this.bootReady = true; }, 600);

      if (needsOnboarding) {
        await this.sleep(2000);
        this.startOnboarding();
      } else {
        await this.sleep(2000);
        this.finishBoot();
      }
    },

    sleep(ms) {
      return new Promise(r => setTimeout(r, ms));
    },

    markBootStep(id) {
      const step = this.bootSteps.find(s => s.id === id);
      if (step) step.done = true;
    },

    finishBoot() {
      this.mode = 'dashboard';
      setTimeout(() => {
        const el = document.getElementById('boot-screen');
        if (el) el.style.display = 'none';
        this.loadDashboard();
      }, 800);
    },

    // ─── ONBOARDING ──────────────────────────────────────

    async startOnboarding() {
      this.mode = 'onboarding';
      setTimeout(() => {
        const el = document.getElementById('boot-screen');
        if (el) el.style.display = 'none';
      }, 800);

      try {
        const res = await fetch('/onboarding/start', { method: 'POST' });
        const data = await res.json();
        this.sessionId = data.session_id;
        this.wsId = data.workspace_id;
        this.onboardingMessages.push({ role: 'system', text: data.first_message });
        await this.sleep(100);
        this.scrollOnboarding();
      } catch (e) {
        this.onboardingMessages.push({
          role: 'system',
          text: 'Something went wrong. Please refresh and try again.'
        });
      }
    },

    async sendOnboardingMessage() {
      if (!this.onboardingInput.trim() || !this.sessionId) return;
      const msg = this.onboardingInput.trim();
      this.onboardingInput = '';
      this.onboardingMessages.push({ role: 'user', text: msg });

      await this.sleep(300);

      try {
        const res = await fetch('/onboarding/message', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ session_id: this.sessionId, message: msg }),
        });
        const data = await res.json();

        if (data.done) {
          this.onboardingMessages.push({ role: 'system', text: data.response });
          this.scrollOnboarding();
          await this.sleep(3500);
          this.startAssembly();
        } else {
          this.onboardingMessages.push({ role: 'system', text: data.response });
        }
      } catch (e) {
        this.onboardingMessages.push({
          role: 'system',
          text: 'Something went wrong. Try again.'
        });
      }

      this.scrollOnboarding();
    },

    scrollOnboarding() {
      this.$nextTick(() => {
        const el = document.getElementById('onboarding-messages');
        if (el) el.scrollTop = el.scrollHeight;
      });
    },

    // ─── ASSEMBLY ────────────────────────────────────────

    async startAssembly() {
      this.mode = 'assembling';

      for (let i = 0; i < this.assemblySteps.length; i++) {
        await this.sleep(600);
        this.assemblySteps[i].done = true;
      }

      await this.sleep(800);
      this.finishBoot();
    },

    // ─── DASHBOARD ───────────────────────────────────────

    async loadDashboard() {
      this.ready = true;

      try {
        const wsRes = await fetch('/workspaces');
        const wsData = await wsRes.json();
        if (wsData.length > 0) {
          const ws = wsData[wsData.length - 1];
          this.wsName = ws.name;
          this.wsId = ws.workspace_id;
        }
      } catch { /* skip */ }

      try {
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
        }
      } catch { /* skip */ }

      if (this.wsId) {
        try {
          const artRes = await fetch(`/workspaces/${this.wsId}/artifacts`);
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
        } catch { /* skip */ }

        try {
          const stateRes = await fetch(`/workspaces/${this.wsId}/state`);
          if (stateRes.ok) {
            const stateData = await stateRes.json();
            const sa = stateData.state_assessment;
            this.phase = sa.current_state;
            this.phaseNext = sa.next_state || '';
            this.blockers = sa.blockers || [];
            this.requirements = sa.requirements || [];
            this.canTransition = sa.can_transition;
          }
          const projRes = await fetch(`/workspaces/${this.wsId}/projects`);
          if (projRes.ok) {
            const projs = await projRes.json();
            if (projs.length > 0) this.projectName = projs[0].name;
          }
          const mindRes = await fetch(`/workspaces/${this.wsId}/mind`);
          if (mindRes.ok) {
            const mindData = await mindRes.json();
            this.mind = mindData;
          }
          const reasonRes = await fetch(`/workspaces/${this.wsId}/reasoning`);
          if (reasonRes.ok) {
            const reasonData = await reasonRes.json();
            this.reasoning = reasonData;
          }
        } catch { /* skip */ }
      }
      this.$nextTick(() => this.initAutoScroll());
    },

    // ─── PIPELINE ────────────────────────────────────────

    isPipelineDone(stage) {
      const order = ['orchestration', 'snapshot', 'eval', 'pie', 'complete'];
      const currentIdx = order.indexOf(this.pipelineStage);
      const stageIdx = order.indexOf(stage);
      return stageIdx < currentIdx;
    },

    isPipelineActive(stage) {
      return this.pipelineStage === stage;
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
        } catch { /* ignore */ }
      }, 200);
    },

    stopPipelinePolling() {
      if (this.pipelineTimer) {
        clearInterval(this.pipelineTimer);
        this.pipelineTimer = null;
      }
      this.pipelinePolling = false;
    },

    // ─── ARTIFACT VIEWER ─────────────────────────────────

    async selectArtifact(artifactType) {
      const arts = this.artifacts.filter(a => a.artifact_type === artifactType);
      if (arts.length === 0) return;
      const art = arts[arts.length - 1];
      this.selectedArtifact = { type: artifactType, provider: art.provider, confidence: art.confidence, data: {}, loaded: false };
      try {
        const res = await fetch(`/workspaces/${this.wsId}/artifacts/${art.artifact_id}`);
        if (res.ok) {
          const full = await res.json();
          this.selectedArtifact.data = full.data || {};
          this.selectedArtifact.loaded = true;
        } else {
          this.selectedArtifact.loaded = true;
        }
      } catch {
        this.selectedArtifact.loaded = true;
      }
    },

    closeViewer() {
      this.selectedArtifact = null;
    },

    closeGeneratedArtifact() {
      this.showArtifactViewer = false;
      this.generatedArtifact = '';
      this.recentlyGenerated = '';
    },

    // ─── RESIZABLE CONSOLE ──────────────────────────────────

    startDragConsole(event) {
      this.consoleDragging = true;
      this.dragStartY = event.clientY;
      this.dragStartHeight = this.consoleHeight;
      event.preventDefault();
    },

    onDragConsole(event) {
      if (!this.consoleDragging) return;
      const delta = this.dragStartY - event.clientY;
      const maxHeight = Math.floor(window.innerHeight * 0.65);
      const newHeight = Math.max(180, Math.min(maxHeight, this.dragStartHeight + delta));
      this.consoleHeight = Math.round(newHeight);
    },

    stopDragConsole() {
      if (!this.consoleDragging) return;
      this.consoleDragging = false;
      localStorage.setItem('command_console_height', String(this.consoleHeight));
    },

    resetConsoleHeight() {
      this.consoleHeight = 220;
      localStorage.removeItem('command_console_height');
    },

    // ─── SHELL ───────────────────────────────────────────

    pushLog(text, type = 'output') {
      this.history.push({ prompt: '', text, type });
      this.scrollToLastMessage();
    },

    async startNewProject() {
      if (!this.wsId) return;
      this.history = [];
      this.pushLog('Starting a new project...', 'info');
      try {
        const res = await fetch(`/workspaces/${this.wsId}/new-project`, { method: 'POST' });
        if (res.ok) {
          const data = await res.json();
          this.projectName = data.project_name;
          this.mind = { version: 1, observations: [], beliefs: [], tensions: [], requirement_states: [] };
          this.reasoning = { reflection: '', confidence: 0, suggested_action: 'wait', reasoning_trace: [], unanswered_questions: [] };
          this.pushLog(data.message, 'output');
        } else {
          this.pushLog('Failed to create new project.', 'error');
        }
      } catch (e) {
        this.pushLog(`Error: ${e.message}`, 'error');
      }
    },

    scrollToLastMessage() {
      if (!this.autoScroll) return;
      this.$nextTick(() => {
        const container = document.getElementById('console-body');
        if (!container) return;
        const last = container.querySelector('.console-entry:last-child');
        if (last) last.scrollIntoView({ block: 'start', behavior: 'smooth' });
      });
    },

    initAutoScroll() {
      const container = document.getElementById('console-body');
      if (!container) return;
      container.addEventListener('scroll', () => {
        const atBottom = container.scrollHeight - container.scrollTop - container.clientHeight < 60;
        this.autoScroll = atBottom;
      }, { passive: true });
    },

    async executeCommand() {
      if (!this.command.trim()) return;
      const cmd = this.command;
      this.command = '';

      this.history.push({ prompt: 'creator@workspace', text: cmd, type: 'user' });
      this.scrollToLastMessage();

      const wsId = this.wsId;
      if (!wsId) {
        this.pushLog('Error: No workspace loaded.', 'error');
        return;
      }

      // Interruption: clear pending states
      if (this._isInterruption(cmd)) {
        this.pendingCheckpoint = null;
        this.pendingProposal = null;
      }

      // If we have a pending checkpoint and user says yes, show proposal
      if (this.pendingCheckpoint && this._isAffirmative(cmd)) {
        this.pushLog('Understanding confirmed. Building proposal...', 'info');
        this.pendingCheckpoint = null;
        const res = await fetch('/intent/resolve', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ workspace_id: wsId, input: 'proceed' }),
        });
        if (res.ok) {
          const decision = await res.json();
          if (decision.action === 'propose') {
            this.pushLog(decision.narrative, 'system');
            this.pendingProposal = decision.artifact_type;
            return;
          }
        }
        this.pendingProposal = null;
        return;
      }

      // If we have a pending proposal and user says yes, generate
      if (this.pendingProposal && this._isAffirmative(cmd)) {
        const atype = this.pendingProposal;
        this.pendingProposal = null;
        this.pushLog('Proceeding with generation...', 'info');
        await this.generateArtifact(atype, cmd);
        return;
      }
      this.pendingCheckpoint = null;
      this.pendingProposal = null;

      try {
        // Resolve intent via the backend
        const res = await fetch('/intent/resolve', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ workspace_id: wsId, input: cmd }),
        });

        if (!res.ok) {
          this.pushLog("Sorry, I couldn't process that. Please try again.", 'system');
          return;
        }

        const decision = await res.json();
        if (!decision || typeof decision !== 'object') {
          this.pushLog("I received an unexpected response. Let's try again.", 'system');
          return;
        }

        if (decision.action === 'chat') {
          this.pushLog(decision.narrative, 'system');
          return;
        }

        if (decision.action === 'ask' || decision.action === 'reflect') {
          this.pushLog(decision.narrative, 'system');
          return;
        }

        if (decision.action === 'checkpoint') {
          this.pushLog(decision.narrative, 'system');
          this.pendingCheckpoint = decision.artifact_type;
          return;
        }

        if (decision.action === 'propose') {
          this.pushLog(decision.narrative, 'system');
          this.pendingProposal = decision.artifact_type;
          return;
        }

        // Generation progress animation with staged reveal
        if (decision.action === 'generating') {
          const stages = [
            { working: 'Understanding intent...', done: '✓ Theme identified' },
            { working: 'Building world...', done: '✓ Character emerging' },
            { working: 'Designing story arc...', done: '✓ Visual language' },
            { working: 'Creating production artifact...', done: '✓ Film Concept ready' },
          ];
          for (const s of stages) {
            this.pushLog(s.working, 'info');
            await this.sleep(550);
            this.pushLog(s.done, 'info');
            await this.sleep(250);
          }
          await this.sleep(800);
          if (decision.review) {
            this.pushLog(decision.review, 'system');
            const words = decision.review.split(/\s+/).length;
            const readingTime = Math.max(2500, Math.min(6000, words * 180));
            await this.sleep(readingTime);
          }
          this.pushLog('Opening Film Concept...', 'info');
          await this.sleep(300);
          this.artifacts.push({ artifact_type: 'film_concept', confidence: 0.85, provider: 'creator-os', artifact_id: 'fc-' + Date.now() });
          this.artifactCount = this.artifacts.length;
          this.recentlyGenerated = 'film_concept';
          this.generatedArtifact = decision.narrative;
          this.showArtifactViewer = true;
          return;
        }

        this.pushLog(decision.narrative, 'info');

        if (decision.action === 'generate') {
          await this.generateArtifact(decision.artifact_type, cmd);
        }
      } catch (e) {
        this.pushLog(`Error: ${e.message}`, 'error');
      }
    },

    _isAffirmative(text) {
      const t = text.toLowerCase().trim();
      return ['yes', 'proceed', 'go ahead', 'start', 'generate', 'do it', 'ready', 'let\'s go', 'continue', 'ok', 'sure', 'yeah', 'yep'].includes(t) ||
        t.startsWith('yes') || t.startsWith('proceed') || t === 'y';
    },

    _isInterruption(text) {
      const t = text.toLowerCase().trim();
      return ['wait', 'actually', 'hold on', 'stop', 'no,', 'not quite', 'thats not'].some(k => t.startsWith(k)) ||
        t === 'no' || t.startsWith('no ');
    },

    async generateArtifact(artifactType, userRequest) {
      this.pushLog('Request received.', 'info');

      this.pipelinePolling = true;
      this.pipelineStage = 'orchestration';
      this.pipelineMessage = 'Starting...';
      this.startPipelinePolling();

      try {
        const wsId = this.wsId;
        if (!wsId) {
          this.pushLog('Error: No workspace loaded.', 'error');
          this.stopPipelinePolling();
          return;
        }

        this.pushLog(`Generating ${artifactType.split('_').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ')}...`, 'info');

        const res = await fetch('/generate-launch-plan', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ workspace_id: wsId, user_request: userRequest, artifact_type: artifactType }),
        });

        if (res.ok) {
          const data = await res.json();
          const metrics = data.metrics || {};

          if (metrics.total_ms) {
            if (metrics.provider) {
              const providerName = metrics.provider.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
              this.pushLog(`Generated via ${providerName}`, 'info');
            }

            const times = [];
            if (metrics.orchestration_ms) times.push(`Inference: ${Math.round(metrics.orchestration_ms)}ms`);
            if (metrics.eval_ms) times.push(`Eval: ${Math.round(metrics.eval_ms)}ms`);
            if (metrics.total_ms) times.push(`Total: ${Math.round(metrics.total_ms)}ms`);
            if (times.length > 0) this.pushLog(times.join(' | '), 'info');

            if (data.eval && data.eval.score) {
              const score = Math.round(data.eval.score * 100);
              this.pushLog(`Quality: ${score}%`, score >= 70 ? 'output' : 'error');
            }

            this.pushLog('Workspace updated.', 'output');
          } else {
            this.pushLog('Complete.', 'output');
          }

          // In-place refresh — no reboot
          this.stopPipelinePolling();
          await this.sleep(300);
          await this.loadDashboard();
        } else {
          this.pushLog('Error: Generation failed.', 'error');
          this.stopPipelinePolling();
        }
      } catch (e) {
        this.pushLog(`Error: ${e.message}`, 'error');
        this.stopPipelinePolling();
      }
    },
  }));
});

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
