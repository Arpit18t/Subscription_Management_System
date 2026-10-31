/**
 * Brightloop Subscriptions — ZeBeyond Platform Engine
 * Architect: Ritesh Tiwari (Task 2 Lead)
 */

const AppState = {
  currentView: 'overview',
  virtualDate: new Date(2026, 9, 31),
  daysElapsed: 0,
  lifecycleFilter: 'all',
  chosenPlan: 'growth',

  plans: [
    {
      id: 'daily',
      name: 'Daily Elastic Pilot',
      interval: 'Daily',
      days: 1,
      price: 15,
      minSeats: 1,
      autoClose: true,
      closable: true,
      pausable: true,
      renewable: true,
      features: ['24h Continuous Accrual', '1 Seat Min Guarantee', 'Immediate Terminate', 'Sandbox Access']
    },
    {
      id: 'starter',
      name: 'Agile Sprint Pack',
      interval: 'Weekly',
      days: 7,
      price: 49,
      minSeats: 1,
      autoClose: false,
      closable: true,
      pausable: true,
      renewable: true,
      features: ['Weekly Invoice Auto-Debit', '1 Seat Min Guarantee', 'Standard API Access', 'Email Support']
    },
    {
      id: 'growth',
      name: 'Mid-Market Growth',
      interval: 'Monthly',
      days: 30,
      price: 149,
      minSeats: 5,
      autoClose: false,
      closable: true,
      pausable: true,
      renewable: true,
      featured: true,
      features: ['Monthly Recurring Billing', 'Min 5 Seats Safeguard', 'Odoo Variant Ready', 'Audit Log Access']
    },
    {
      id: 'enterprise',
      name: 'Enterprise Cloud Core',
      interval: 'Yearly',
      days: 365,
      price: 399,
      minSeats: 10,
      autoClose: false,
      closable: true,
      pausable: false,
      renewable: true,
      features: ['Annual Committed Discount', 'Dedicated Account Manager', 'Custom Odoo Surcharge SLA', 'Full Idempotency Suite']
    }
  ],

  subscriptions: [
    {
      id: 'SUB-2026-0041',
      customer: 'Stark Robotics Labs',
      email: 'tony@stark.io',
      planId: 'enterprise',
      planName: 'Enterprise Cloud Core',
      interval: 'Yearly',
      seats: 25,
      odooSurcharge: true,
      surchargeAmount: 560,
      slaSupport: true,
      monthlyTotal: 18450.00,
      status: 'active',
      startDate: '2026-09-15',
      nextInvoiceDate: '2027-09-15',
      policies: { autoClose: false, closable: true, pausable: false, renewable: true }
    },
    {
      id: 'SUB-2026-0042',
      customer: 'Nexus Cybernetics',
      email: 'ops@nexuscyber.org',
      planId: 'growth',
      planName: 'Mid-Market Growth',
      interval: 'Monthly',
      seats: 12,
      odooSurcharge: true,
      surchargeAmount: 560,
      slaSupport: true,
      monthlyTotal: 7420.00,
      status: 'active',
      startDate: '2026-10-01',
      nextInvoiceDate: '2026-11-01',
      policies: { autoClose: false, closable: true, pausable: true, renewable: true }
    },
    {
      id: 'SUB-2026-0043',
      customer: 'Vanguard Logistics ERP',
      email: 'finance@vanguard.com',
      planId: 'growth',
      planName: 'Mid-Market Growth',
      interval: 'Monthly',
      seats: 8,
      odooSurcharge: false,
      surchargeAmount: 0,
      slaSupport: false,
      monthlyTotal: 1192.00,
      status: 'paused',
      startDate: '2026-08-10',
      nextInvoiceDate: 'PAUSED',
      policies: { autoClose: false, closable: true, pausable: true, renewable: true }
    },
    {
      id: 'SUB-2026-0044',
      customer: 'Hyperion BioTech',
      email: 'cloud@hyperionbio.com',
      planId: 'starter',
      planName: 'Agile Sprint Pack',
      interval: 'Weekly',
      seats: 4,
      odooSurcharge: true,
      surchargeAmount: 560,
      slaSupport: false,
      monthlyTotal: 2436.00,
      status: 'confirmed',
      startDate: '2026-10-28',
      nextInvoiceDate: '2026-11-04',
      policies: { autoClose: true, closable: true, pausable: true, renewable: true }
    },
    {
      id: 'SUB-2026-0045',
      customer: 'Orbital Dynamics Global',
      email: 'it@orbitaldyn.net',
      planId: 'enterprise',
      planName: 'Enterprise Cloud Core',
      interval: 'Yearly',
      seats: 50,
      odooSurcharge: true,
      surchargeAmount: 560,
      slaSupport: true,
      monthlyTotal: 34500.00,
      status: 'active',
      startDate: '2026-01-10',
      nextInvoiceDate: '2027-01-10',
      policies: { autoClose: false, closable: true, pausable: false, renewable: true }
    },
    {
      id: 'SUB-2026-0046',
      customer: 'Solaria Solar Grids',
      email: 'energy@solaria.io',
      planId: 'growth',
      planName: 'Mid-Market Growth',
      interval: 'Monthly',
      seats: 6,
      odooSurcharge: false,
      surchargeAmount: 0,
      slaSupport: false,
      monthlyTotal: 894.00,
      status: 'closed',
      startDate: '2026-05-01',
      nextInvoiceDate: 'TERMINATED',
      policies: { autoClose: true, closable: true, pausable: false, renewable: false }
    }
  ],

  quotations: [
    {
      id: 'QT-2026-0840',
      customer: 'Aether Micro-Turbines',
      planId: 'growth',
      seats: 10,
      total: 2348.20,
      status: 'quotation'
    },
    {
      id: 'QT-2026-0841',
      customer: 'Borealis Genomics',
      planId: 'enterprise',
      seats: 15,
      total: 16974.30,
      status: 'quotation'
    }
  ],

  telemetry: []
};

// Navigation
function navigate(viewId) {
  AppState.currentView = viewId;

  document.querySelectorAll('.nav-link').forEach(btn => {
    btn.classList.toggle('active', btn.dataset.view === viewId);
  });

  document.querySelectorAll('.view-pane').forEach(pane => {
    pane.classList.remove('active');
  });

  const target = document.getElementById(`view-${viewId}`);
  if (target) target.classList.add('active');

  if (viewId === 'quotes') recalcQuoteLive();
  if (viewId === 'subscriptions') renderLifecycleTable();
  if (viewId === 'plans') renderPlansShowcase();
  if (viewId === 'overview') renderOverviewTable();
}

// Pricing & Quotation Composer
function pickPlan(el, planKey) {
  AppState.chosenPlan = planKey;
  document.querySelectorAll('.plan-card').forEach(c => c.classList.remove('active'));
  el.classList.add('active');
  recalcQuoteLive();
}

function handleSeatRange(val) {
  document.getElementById('seatValBadge').innerText = `${val} Seats`;
  recalcQuoteLive();
}

function recalcQuoteLive() {
  const seats = parseInt(document.getElementById('seatSlider').value, 10);
  const plan = AppState.plans.find(p => p.id === AppState.chosenPlan) || AppState.plans[2];
  const odooSurcharge = document.getElementById('odooSurchargeToggle').checked;
  const slaSupport = document.getElementById('addonSLA').checked;
  const drBackup = document.getElementById('addonDR').checked;

  // Min seats validation
  const alertStrip = document.getElementById('minSeatsAlert');
  const alertText = document.getElementById('minSeatsAlertText');
  if (seats < plan.minSeats) {
    alertStrip.classList.remove('hidden');
    alertText.innerText = `Selected tier (${plan.name}) requires a minimum of ${plan.minSeats} seats.`;
  } else {
    alertStrip.classList.add('hidden');
  }

  // Base Calculation
  const baseRate = plan.price;
  const baseAmount = baseRate * seats;
  const slaAmount = slaSupport ? 500.00 : 0.0;
  const drAmount = drBackup ? 250.00 : 0.0;
  const subtotal = baseAmount + slaAmount + drAmount;

  // Volume Tier Discount
  let discountPct = 0;
  if (seats >= 50) discountPct = 0.15;
  else if (seats >= 25) discountPct = 0.10;
  else if (seats >= 10) discountPct = 0.05;

  const discountAmount = subtotal * discountPct;
  const discountedSubtotal = subtotal - discountAmount;

  // Odoo Enterprise Surcharge
  const surchargeTotal = odooSurcharge ? (560.00 * seats) : 0;
  const taxableBase = discountedSubtotal + surchargeTotal;

  // 18% GST (CGST 9% + SGST 9%)
  const gstRate = 0.18;
  const taxAmount = taxableBase * gstRate;
  const grandTotal = taxableBase + taxAmount;

  // Update Preview Document
  const clientName = document.getElementById('cfgCustomer').value || 'ZeBeyond Powertrain Dynamics';
  const clientEmail = document.getElementById('cfgEmail').value || 'licensing@zebeyond.engineering';
  document.getElementById('docCustomer').innerText = clientName;
  document.getElementById('docEmail').innerText = clientEmail;

  // Line items
  let lines = `
    <tr>
      <td><b>${plan.name}</b> (${plan.interval})</td>
      <td>${seats}</td>
      <td>$${baseRate.toFixed(2)}</td>
      <td class="text-right">$${baseAmount.toFixed(2)}</td>
    </tr>
  `;

  if (slaSupport) {
    lines += `
      <tr>
        <td>24/7 SLA Priority Mission-Critical Support</td>
        <td>1</td>
        <td>$500.00</td>
        <td class="text-right">$500.00</td>
      </tr>
    `;
  }

  if (drBackup) {
    lines += `
      <tr>
        <td>Multi-Region Hot-Failover Cloud DR</td>
        <td>1</td>
        <td>$250.00</td>
        <td class="text-right">$250.00</td>
      </tr>
    `;
  }

  document.getElementById('docLineItemsBody').innerHTML = lines;

  document.getElementById('docSubtotalVal').innerText = `$${subtotal.toLocaleString('en-US', { minimumFractionDigits: 2 })}`;

  const surchargeRow = document.getElementById('docSurchargeRow');
  if (odooSurcharge) {
    surchargeRow.style.display = 'flex';
    document.getElementById('docSurchargeSeats').innerText = seats;
    document.getElementById('docSurchargeVal').innerText = `+$${surchargeTotal.toLocaleString('en-US', { minimumFractionDigits: 2 })}`;
  } else {
    surchargeRow.style.display = 'none';
  }

  const discountRow = document.getElementById('docDiscountRow');
  if (discountPct > 0) {
    discountRow.style.display = 'flex';
    discountRow.querySelector('span:first-child').innerText = `Volume Tier Discount (${discountPct * 100}%):`;
    document.getElementById('docDiscountVal').innerText = `-$${discountAmount.toLocaleString('en-US', { minimumFractionDigits: 2 })}`;
  } else {
    discountRow.style.display = 'none';
  }

  document.getElementById('docTaxVal').innerText = `$${taxAmount.toLocaleString('en-US', { minimumFractionDigits: 2 })}`;
  document.getElementById('docGrandTotalVal').innerText = `$${grandTotal.toLocaleString('en-US', { minimumFractionDigits: 2 })}`;
}

function activateQuotationToSubscription() {
  const customer = document.getElementById('cfgCustomer').value || 'New Enterprise Client';
  const email = document.getElementById('cfgEmail').value || 'billing@client.com';
  const seats = parseInt(document.getElementById('seatSlider').value, 10);
  const plan = AppState.plans.find(p => p.id === AppState.chosenPlan) || AppState.plans[2];
  const odooSurcharge = document.getElementById('odooSurchargeToggle').checked;
  const slaSupport = document.getElementById('addonSLA').checked;

  const newId = `SUB-2026-${String(AppState.subscriptions.length + 42).padStart(4, '0')}`;
  const surchargeTotal = odooSurcharge ? (560.00 * seats) : 0;
  const slaTotal = slaSupport ? 500.00 : 0;
  const monthlyTotal = (plan.price * seats) + surchargeTotal + slaTotal;

  const newSub = {
    id: newId,
    customer: customer,
    email: email,
    planId: plan.id,
    planName: plan.name,
    interval: plan.interval,
    seats: seats,
    odooSurcharge: odooSurcharge,
    surchargeAmount: odooSurcharge ? 560 : 0,
    slaSupport: slaSupport,
    monthlyTotal: monthlyTotal,
    status: 'active',
    startDate: formatDate(AppState.virtualDate),
    nextInvoiceDate: formatDate(addDays(AppState.virtualDate, 30)),
    policies: {
      autoClose: document.getElementById('polAutoClose').checked,
      closable: document.getElementById('polClosable').checked,
      pausable: document.getElementById('polPausable').checked,
      renewable: document.getElementById('polRenewable').checked
    }
  };

  AppState.subscriptions.unshift(newSub);
  logEvent('STATE_CHANGE', `Quotation confirmed to Active Subscription: ${newId} (${customer})`);
  showToast(`Subscription ${newId} activated successfully.`);

  updateMetrics();
  renderOverviewTable();
  renderLifecycleTable();
}

// State Machine Enforcement
function transitionSubState(subId, target) {
  const sub = AppState.subscriptions.find(s => s.id === subId);
  if (!sub) return;

  if (target === 'paused') {
    if (!sub.policies.pausable) {
      showToast('Policy Denied: Contract lock prohibits pausing.', true);
      return;
    }
    sub.status = 'paused';
    sub.nextInvoiceDate = 'PAUSED';
    logEvent('STATE_CHANGE', `Subscription ${sub.id} paused by customer request.`, 'warn');
    showToast(`Subscription ${sub.id} paused.`);
  } else if (target === 'active') {
    sub.status = 'active';
    sub.nextInvoiceDate = formatDate(addDays(AppState.virtualDate, 30));
    logEvent('STATE_CHANGE', `Subscription ${sub.id} resumed to Active.`);
    showToast(`Subscription ${sub.id} resumed.`);
  } else if (target === 'closed') {
    if (!sub.policies.closable) {
      showToast('Policy Denied: Contract lock prohibits early termination.', true);
      return;
    }
    sub.status = 'closed';
    sub.nextInvoiceDate = 'TERMINATED';
    const refund = (sub.monthlyTotal * 0.42).toFixed(2);
    logEvent('EARLY_CLOSE', `Subscription ${sub.id} terminated early. Prorated credit refund of $${refund} credited.`, 'danger');
    showToast(`Subscription ${sub.id} closed. Prorated credit: $${refund}`);
  }

  updateMetrics();
  renderOverviewTable();
  renderLifecycleTable();
}

// Table Renderers
function renderOverviewTable() {
  const tbody = document.getElementById('overviewTableBody');
  if (!tbody) return;

  const q = (document.getElementById('overviewSearchInput')?.value || '').toLowerCase();
  const list = AppState.subscriptions.filter(s => 
    s.id.toLowerCase().includes(q) ||
    s.customer.toLowerCase().includes(q) ||
    s.planName.toLowerCase().includes(q)
  );

  if (list.length === 0) {
    tbody.innerHTML = `<tr><td colspan="9" style="text-align:center; padding:24px; color:var(--zb-text-muted);">No subscription records match your search.</td></tr>`;
    return;
  }

  tbody.innerHTML = list.map(s => `
    <tr>
      <td><span class="sub-id-code">${s.id}</span></td>
      <td>
        <div style="font-weight:700; color:#fff;">${s.customer}</div>
        <div style="font-size:0.72rem; color:var(--zb-text-dim);">${s.email}</div>
      </td>
      <td>
        <div>${s.planName}</div>
        <div style="font-family:var(--font-mono); font-size:0.7rem; color:var(--zb-green);">${s.interval}</div>
      </td>
      <td><span style="font-family:var(--font-mono); font-weight:700;">${s.seats}</span></td>
      <td>
        ${s.odooSurcharge 
          ? `<span style="font-family:var(--font-mono); font-size:0.72rem; color:var(--zb-gold); font-weight:700;">+$${s.surchargeAmount}/seat</span>`
          : `<span style="color:var(--zb-text-muted); font-size:0.72rem;">None</span>`}
      </td>
      <td><span style="font-family:var(--font-mono); font-weight:800; color:#fff;">$${s.monthlyTotal.toLocaleString('en-US', { minimumFractionDigits: 2 })}</span></td>
      <td><span class="state-chip ${s.status}">${s.status.toUpperCase()}</span></td>
      <td style="font-family:var(--font-mono); font-size:0.75rem;">${s.nextInvoiceDate}</td>
      <td class="text-right">
        <div class="tbl-actions">
          ${s.status === 'active' ? `
            <button class="btn-mini" onclick="transitionSubState('${s.id}', 'paused')">Pause</button>
            <button class="btn-mini danger" onclick="transitionSubState('${s.id}', 'closed')">Cancel</button>
          ` : s.status === 'paused' ? `
            <button class="btn-mini" style="color:var(--zb-green);" onclick="transitionSubState('${s.id}', 'active')">Resume</button>
          ` : `<span style="color:var(--zb-text-muted); font-size:0.72rem;">Archived</span>`}
        </div>
      </td>
    </tr>
  `).join('');
}

function renderLifecycleTable() {
  const tbody = document.getElementById('lifecycleTableBody');
  if (!tbody) return;

  const q = (document.getElementById('subSearchInput')?.value || '').toLowerCase();
  const list = AppState.subscriptions.filter(s => {
    const matchState = AppState.lifecycleFilter === 'all' || s.status === AppState.lifecycleFilter;
    const matchSearch = s.id.toLowerCase().includes(q) || s.customer.toLowerCase().includes(q);
    return matchState && matchSearch;
  });

  tbody.innerHTML = list.map(s => `
    <tr>
      <td><span class="sub-id-code">${s.id}</span></td>
      <td>
        <div style="font-weight:700; color:#fff;">${s.customer}</div>
      </td>
      <td>${s.planName}</td>
      <td style="font-family:var(--font-mono); font-size:0.74rem;">${s.interval}</td>
      <td><span style="font-family:var(--font-mono); font-weight:700;">${s.seats}</span></td>
      <td><span style="font-family:var(--font-mono); font-weight:800; color:#fff;">$${s.monthlyTotal.toLocaleString('en-US', { minimumFractionDigits: 2 })}</span></td>
      <td><span class="state-chip ${s.status}">${s.status.toUpperCase()}</span></td>
      <td style="font-size:0.72rem; color:var(--zb-text-dim);">
        ${s.policies.autoClose ? 'Auto-close | ' : ''}
        ${s.policies.pausable ? 'Pausable | ' : ''}
        ${s.policies.closable ? 'Closable' : ''}
      </td>
      <td class="text-right">
        <div class="tbl-actions">
          ${s.status === 'active' ? `
            <button class="btn-mini" onclick="transitionSubState('${s.id}', 'paused')">Pause</button>
            <button class="btn-mini danger" onclick="transitionSubState('${s.id}', 'closed')">Cancel</button>
          ` : s.status === 'paused' ? `
            <button class="btn-mini" style="color:var(--zb-green);" onclick="transitionSubState('${s.id}', 'active')">Resume</button>
          ` : `<span style="color:var(--zb-text-muted); font-size:0.72rem;">Locked</span>`}
        </div>
      </td>
    </tr>
  `).join('');

  document.getElementById('pillAll').innerText = AppState.subscriptions.length;
  document.getElementById('pillActive').innerText = AppState.subscriptions.filter(s => s.status === 'active').length;
  document.getElementById('pillQuotes').innerText = AppState.quotations.length;
  document.getElementById('pillPaused').innerText = AppState.subscriptions.filter(s => s.status === 'paused').length;
  document.getElementById('pillClosed').innerText = AppState.subscriptions.filter(s => s.status === 'closed').length;
}

function setLifecycleFilter(st, btn) {
  AppState.lifecycleFilter = st;
  document.querySelectorAll('.pill-tab').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  renderLifecycleTable();
}

function filterOverviewTable() {
  renderOverviewTable();
}

function filterLifecycleTable() {
  renderLifecycleTable();
}

// Plans Grid
function renderPlansShowcase() {
  const container = document.getElementById('plansMatrixGrid');
  if (!container) return;

  container.innerHTML = AppState.plans.map(p => `
    <div class="zb-plan-box ${p.featured ? 'featured' : ''}">
      <div>
        <div class="z-plan-title">${p.name}</div>
        <div class="z-plan-interval">Billing Frequency: ${p.interval} (${p.days}d)</div>
        <div class="z-plan-rate">$${p.price}<span>/cycle</span></div>
        <ul class="z-bullets">
          <li><i class="fa-solid fa-check"></i> Min Seats Limit: <b>${p.minSeats}</b></li>
          <li><i class="fa-solid fa-check"></i> Auto-Close Policy: <b>${p.autoClose ? 'Yes' : 'No'}</b></li>
          <li><i class="fa-solid fa-check"></i> Early Termination: <b>${p.closable ? 'Allowed' : 'Locked'}</b></li>
          <li><i class="fa-solid fa-check"></i> Allow Pause: <b>${p.pausable ? 'Yes' : 'No'}</b></li>
          ${p.features.map(f => `<li><i class="fa-solid fa-check"></i> ${f}</li>`).join('')}
        </ul>
      </div>

      <button class="btn-zb-primary" style="width:100%; justify-content:center;" onclick="loadTemplateAndCompose('${p.id}')">
        Configure License
      </button>
    </div>
  `).join('');
}

function loadTemplateAndCompose(planId) {
  AppState.chosenPlan = planId;
  navigate('quotes');
  showToast(`Loaded ${planId} plan settings into Quote Studio.`);
}

// Simulation Cycle Engine
function advanceSimulation(days) {
  AppState.daysElapsed += days;
  AppState.virtualDate = addDays(AppState.virtualDate, days);

  document.getElementById('simDateDisplay').innerText = formatDate(AppState.virtualDate);

  let invoiced = 0;
  AppState.subscriptions.forEach(sub => {
    if (sub.status === 'active') {
      if (sub.interval === 'Daily' && days >= 1) invoiced++;
      else if (sub.interval === 'Weekly' && days >= 7) invoiced++;
      else if (sub.interval === 'Monthly' && days >= 30) {
        invoiced++;
        sub.nextInvoiceDate = formatDate(addDays(AppState.virtualDate, 30));
      }
    }
  });

  logEvent('CYCLE_ADVANCE', `Advanced clock +${days} days. Automated invoices generated for ${invoiced} active nodes.`);
  showToast(`Simulated +${days} days. ${invoiced} invoices generated.`);

  updateMetrics();
  renderOverviewTable();
  renderLifecycleTable();
}

function resetSimulation() {
  AppState.virtualDate = new Date(2026, 9, 31);
  AppState.daysElapsed = 0;
  document.getElementById('simDateDisplay').innerText = '31 October 2026';
  logEvent('CLOCK_RESET', 'Simulation clock reset to baseline: 31 Oct 2026.');
  showToast('Simulation clock reset to baseline.');
}

function triggerEdgeCase(type) {
  if (type === 'pause') {
    const target = AppState.subscriptions.find(s => s.status === 'active' && s.policies.pausable);
    if (target) transitionSubState(target.id, 'paused');
  } else if (type === 'early_close') {
    const target = AppState.subscriptions.find(s => s.status === 'active' && s.policies.closable);
    if (target) transitionSubState(target.id, 'closed');
  }
}

// Telemetry & Toasts
function logEvent(event, msg, level = '') {
  const now = new Date().toTimeString().split(' ')[0];
  AppState.telemetry.unshift({ time: now, event, msg, level });
  renderTelemetry();
}

function renderTelemetry() {
  const container = document.getElementById('telemetryFeed');
  if (!container) return;

  container.innerHTML = AppState.telemetry.slice(0, 20).map(t => `
    <div class="t-row">
      <span class="t-stamp">[${t.time}]</span>
      <span class="t-tag ${t.level}">${t.event}</span>
      <span class="t-text">${t.msg}</span>
    </div>
  `).join('');
}

function clearTelemetry() {
  AppState.telemetry = [];
  renderTelemetry();
}

function showToast(msg, isError = false) {
  const root = document.getElementById('toastRoot');
  if (!root) return;

  const t = document.createElement('div');
  t.className = 'zb-toast';
  t.innerHTML = `<i class="fa-solid ${isError ? 'fa-triangle-exclamation text-gold' : 'fa-circle-check text-green'}"></i> <span>${msg}</span>`;
  root.appendChild(t);

  setTimeout(() => {
    t.style.opacity = '0';
    setTimeout(() => t.remove(), 200);
  }, 3000);
}

// CSV Export
function exportSubscriptionsCSV() {
  let csv = 'Subscription ID,Customer,Email,Plan,Interval,Seats,Odoo Surcharge,Monthly Total,Status,Next Invoice Date\n';
  AppState.subscriptions.forEach(s => {
    csv += `"${s.id}","${s.customer}","${s.email}","${s.planName}","${s.interval}",${s.seats},${s.odooSurcharge ? 560 : 0},${s.monthlyTotal},"${s.status}","${s.nextInvoiceDate}"\n`;
  });
  const blob = new Blob([csv], { type: 'text/csv' });
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `zebeyond_subscriptions_${Date.now()}.csv`;
  a.click();
  showToast('Exported active subscriptions to CSV.');
}

function updateMetrics() {
  const active = AppState.subscriptions.filter(s => s.status === 'active');
  const mrr = active.reduce((acc, s) => acc + s.monthlyTotal, 0);
  const arr = mrr * 12;

  document.getElementById('arrMetric').innerText = `$${Math.round(arr).toLocaleString('en-US')}.00`;
  document.getElementById('mrrMetric').innerText = `$${Math.round(mrr).toLocaleString('en-US')}.00`;
  document.getElementById('activeNodesMetric').innerText = active.length;
  document.getElementById('navSubsCount').innerText = active.length;
}

function addDays(d, days) {
  const c = new Date(d);
  c.setDate(c.getDate() + days);
  return c;
}

function formatDate(d) {
  const m = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
  return `${d.getDate()} ${m[d.getMonth()]} ${d.getFullYear()}`;
}

// Init
document.addEventListener('DOMContentLoaded', () => {
  renderOverviewTable();
  renderLifecycleTable();
  renderPlansShowcase();
  recalcQuoteLive();
  updateMetrics();

  logEvent('SYSTEM_BOOT', 'Brightloop ZeBeyond Engineering Platform Initialized (Task 2).');
});
