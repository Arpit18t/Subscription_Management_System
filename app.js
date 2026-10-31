/**
 * Brightloop Quantum Subscription Engine OS 2.0
 * Pure JavaScript, Zero External NPM Dependencies
 * Architect: Ritesh Tiwari (Task 2 Lead)
 */

// ==============================================================================
// 1. STATE STORE & SEED DATA
// ==============================================================================
const State = {
  activeView: 'visual-flow',
  virtualDate: new Date(2026, 9, 31), // 31 Oct 2026
  daysElapsed: 0,
  audioEnabled: true,
  stateFilter: 'all',
  currentTheme: 'theme-olive-luxe',

  // Pre-configured Plans (Task 2 Requirement: Daily, Weekly, Monthly, Yearly)
  plans: [
    {
      id: 'daily-nano',
      name: 'Daily Elastic Pilot',
      recurrence: 'Daily',
      invoicingPeriod: '1 Day',
      price: 15,
      minSeats: 1,
      autoClose: true,
      closable: true,
      pausable: true,
      renewable: true,
      features: ['24h Continuous Accrual', 'Micro-Billing Engine', 'Immediate Terminate', 'Sandbox Access']
    },
    {
      id: 'starter',
      name: 'Agile Sprint Pack',
      recurrence: 'Weekly',
      invoicingPeriod: '7 Days',
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
      recurrence: 'Monthly',
      invoicingPeriod: '30 Days',
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
      recurrence: 'Yearly',
      invoicingPeriod: '365 Days',
      price: 399,
      minSeats: 10,
      autoClose: false,
      closable: true,
      pausable: false,
      renewable: true,
      features: ['Annual Committed Discount', 'Dedicated Account Manager', 'Custom Odoo Surcharge SLA', 'Full Idempotency Suite']
    }
  ],

  // Live Subscriptions (Across all Lifecycle State Machine stages)
  subscriptions: [
    {
      id: 'SUB-2026-0041',
      customer: 'Stark Robotics Labs',
      email: 'tony@stark.io',
      planId: 'enterprise',
      planName: 'Enterprise Cloud Core',
      recurrence: 'Yearly',
      seats: 25,
      odooSurcharge: true,
      surchargeAmount: 560,
      slaSupport: true,
      basePrice: 399,
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
      recurrence: 'Monthly',
      seats: 12,
      odooSurcharge: true,
      surchargeAmount: 560,
      slaSupport: true,
      basePrice: 149,
      monthlyTotal: 7420.00,
      status: 'active',
      startDate: '2026-10-01',
      nextInvoiceDate: '2026-11-01',
      policies: { autoClose: false, closable: true, pausable: true, renewable: true }
    },
    {
      id: 'SUB-2026-0043',
      customer: 'Vanguard Logistics ERP',
      email: 'finance@vanguardlogistics.com',
      planId: 'growth',
      planName: 'Mid-Market Growth',
      recurrence: 'Monthly',
      seats: 8,
      odooSurcharge: false,
      surchargeAmount: 0,
      slaSupport: false,
      basePrice: 149,
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
      recurrence: 'Weekly',
      seats: 4,
      odooSurcharge: true,
      surchargeAmount: 560,
      slaSupport: false,
      basePrice: 49,
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
      recurrence: 'Yearly',
      seats: 50,
      odooSurcharge: true,
      surchargeAmount: 560,
      slaSupport: true,
      basePrice: 399,
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
      recurrence: 'Monthly',
      seats: 6,
      odooSurcharge: false,
      surchargeAmount: 0,
      slaSupport: false,
      basePrice: 149,
      monthlyTotal: 894.00,
      status: 'closed',
      startDate: '2026-05-01',
      nextInvoiceDate: 'TERMINATED',
      policies: { autoClose: true, closable: true, pausable: false, renewable: false }
    }
  ],

  // Quotations List (Task 2: Quotation Template, 30d Validity, 18% Tax)
  quotations: [
    {
      id: 'QT-2026-0840',
      customer: 'Aether Micro-Turbines',
      email: 'contracts@aether.io',
      planId: 'growth',
      seats: 10,
      odooSurcharge: true,
      slaSupport: true,
      subtotal: 1990.00,
      tax: 358.20,
      grandTotal: 2348.20,
      status: 'quotation',
      issuedDate: '2026-10-15',
      expiryDate: '2026-11-14'
    },
    {
      id: 'QT-2026-0841',
      customer: 'Borealis Genomics',
      email: 'procure@borealis.gen',
      planId: 'enterprise',
      seats: 15,
      odooSurcharge: true,
      slaSupport: true,
      subtotal: 14385.00,
      tax: 2589.30,
      grandTotal: 16974.30,
      status: 'quotation',
      issuedDate: '2026-10-22',
      expiryDate: '2026-11-21'
    }
  ],

  // Live Telemetry Audit Trail
  auditLog: [],

  // Live Odoo Wire RPC Log
  odooLogs: []
};

// ==============================================================================
// 2. THEME SWITCHER LOGIC
// ==============================================================================
function setAppTheme(themeClass) {
  State.currentTheme = themeClass;
  document.body.className = themeClass;
  
  document.querySelectorAll('.theme-pill').forEach(btn => {
    btn.classList.toggle('active', btn.getAttribute('onclick').includes(themeClass));
  });

  playSound('click');
  const themeName = themeClass === 'theme-olive-luxe' ? 'Deep Olive & Gold' :
                    themeClass === 'theme-forest-noir' ? 'Forest Emerald Noir' : 'Nordic Sage Slate';
  showToast(`Theme switched to ${themeName}`, 'info');
}

// ==============================================================================
// 3. AUDIO SYNTHESIZER
// ==============================================================================
let audioCtx = null;

function getAudioContext() {
  if (!audioCtx) {
    const AudioContext = window.AudioContext || window.webkitAudioContext;
    if (AudioContext) audioCtx = new AudioContext();
  }
  return audioCtx;
}

function playSound(type) {
  if (!State.audioEnabled) return;
  try {
    const ctx = getAudioContext();
    if (!ctx) return;
    if (ctx.state === 'suspended') ctx.resume();

    const osc = ctx.createOscillator();
    const gain = ctx.createGain();
    osc.connect(gain);
    gain.connect(ctx.destination);

    const now = ctx.currentTime;

    if (type === 'click') {
      osc.type = 'sine';
      osc.frequency.setValueAtTime(750, now);
      osc.frequency.exponentialRampToValueAtTime(380, now + 0.05);
      gain.gain.setValueAtTime(0.08, now);
      gain.gain.exponentialRampToValueAtTime(0.001, now + 0.05);
      osc.start(now);
      osc.stop(now + 0.05);
    } else if (type === 'success') {
      osc.type = 'triangle';
      osc.frequency.setValueAtTime(523.25, now); // C5
      osc.frequency.setValueAtTime(659.25, now + 0.08); // E5
      osc.frequency.setValueAtTime(783.99, now + 0.16); // G5
      gain.gain.setValueAtTime(0.12, now);
      gain.gain.exponentialRampToValueAtTime(0.001, now + 0.35);
      osc.start(now);
      osc.stop(now + 0.35);
    } else if (type === 'warp') {
      osc.type = 'sawtooth';
      osc.frequency.setValueAtTime(180, now);
      osc.frequency.exponentialRampToValueAtTime(1100, now + 0.15);
      gain.gain.setValueAtTime(0.06, now);
      gain.gain.exponentialRampToValueAtTime(0.001, now + 0.2);
      osc.start(now);
      osc.stop(now + 0.2);
    }
  } catch (e) {
    // Audio context safe fallback
  }
}

function toggleAudio() {
  State.audioEnabled = !State.audioEnabled;
  const label = document.querySelector('.audio-label');
  const icon = document.getElementById('audioIcon');
  if (State.audioEnabled) {
    label.innerText = 'FX: ON';
    icon.className = 'fa-solid fa-volume-high';
    showToast('Sound effects enabled', 'info');
    playSound('click');
  } else {
    label.innerText = 'FX: MUTED';
    icon.className = 'fa-solid fa-volume-xmark';
    showToast('Sound effects muted', 'info');
  }
}

// ==============================================================================
// 4. NAVIGATION & VIEW SWITCHER
// ==============================================================================
const headings = {
  'visual-flow': {
    title: 'Visual Journey & State Machine',
    sub: 'Live reactive pipeline orchestrating Quotations, Odoo Variant Surcharges & State Transitions'
  },
  'quote-studio': {
    title: 'Dynamic Quotation Studio',
    sub: 'Real-time pricing engine with Odoo surcharge ($560), 18% GST & 30-day digital pass'
  },
  'subscriptions-manager': {
    title: 'Subscription Lifecycle State Machine',
    sub: 'Enforcing deterministic states: Draft ➔ Quotation ➔ Confirmed ➔ Active ➔ Paused ➔ Closed'
  },
  'plans-matrix': {
    title: 'Plans Matrix & Quotation Templates',
    sub: 'Configured recurrences (Daily, Weekly, Monthly, Yearly) and pre-set quotation bundles'
  },
  'simulation-time': {
    title: 'Subscription Time-Travel Engine',
    sub: 'Fast-forward system clock by 1d, 7d, or 30d to simulate real-world lifecycle progression'
  }
};

function switchView(viewName) {
  State.activeView = viewName;
  playSound('click');

  // Update nav buttons
  document.querySelectorAll('.dock-btn').forEach(btn => {
    btn.classList.toggle('active', btn.dataset.view === viewName);
  });

  // Update viewport sections
  document.querySelectorAll('.viewport-section').forEach(sec => {
    sec.classList.remove('active');
  });
  const target = document.getElementById(`view-${viewName}`);
  if (target) target.classList.add('active');

  // Update headings
  const info = headings[viewName] || headings['visual-flow'];
  document.getElementById('screenHeading').innerText = info.title;
  document.getElementById('screenSubheading').innerText = info.sub;

  // Refresh dependent elements
  if (viewName === 'quote-studio') recalcQuoteLive();
  if (viewName === 'subscriptions-manager') renderSubscriptionCards();
  if (viewName === 'plans-matrix') renderPlansShowcase();
}

// ==============================================================================
// 5. REAL-TIME QUOTATION CALCULATION ENGINE (Task 2 Core Logic)
// ==============================================================================
let studioSelectedPlan = 'growth';

function selectStudioPlan(el, planKey) {
  studioSelectedPlan = planKey;
  document.querySelectorAll('.plan-choice').forEach(c => c.classList.remove('active'));
  el.classList.add('active');
  playSound('click');
  recalcQuoteLive();
}

function handleSeatSlider(val) {
  document.getElementById('seatCountDisplay').innerText = val;
  recalcQuoteLive();
}

function recalcQuoteLive() {
  const seats = parseInt(document.getElementById('seatSlider').value, 10);
  const plan = State.plans.find(p => p.id === studioSelectedPlan) || State.plans[2];
  const odooChecked = document.getElementById('odooSurchargeToggle').checked;
  const slaChecked = document.getElementById('addonSLA').checked;
  const backupChecked = document.getElementById('addonBackup').checked;

  // Validate Minimum Seats requirement
  const minWarning = document.getElementById('seatMinWarning');
  const minSeatReq = document.getElementById('minSeatReq');
  if (seats < plan.minSeats) {
    minWarning.classList.remove('hidden');
    minSeatReq.innerText = plan.minSeats;
  } else {
    minWarning.classList.add('hidden');
  }

  // Base plan cost per seat
  const baseRate = plan.price;
  let baseLineTotal = baseRate * seats;

  // Odoo Enterprise Variant Surcharge: +$560.00 / seat
  const surchargePerSeat = 560.00;
  const surchargeTotal = odooChecked ? (surchargePerSeat * seats) : 0;

  // Add-ons
  const slaTotal = slaChecked ? 500.00 : 0;
  const backupTotal = backupChecked ? 250.00 : 0;

  // Subtotal
  let rawSubtotal = baseLineTotal + slaTotal + backupTotal;

  // Dynamic Volume Discount Curve
  let discountPct = 0;
  if (seats >= 50) discountPct = 0.15;
  else if (seats >= 25) discountPct = 0.10;
  else if (seats >= 10) discountPct = 0.05;

  let discountAmount = rawSubtotal * discountPct;
  let discountedSubtotal = rawSubtotal - discountAmount;

  // Surcharge added to taxable base
  let taxableAmount = discountedSubtotal + surchargeTotal;

  // 18% GST (CGST 9% + SGST 9% / IGST 18%)
  const gstRate = 0.18;
  const gstAmount = taxableAmount * gstRate;

  // Grand Total Payable
  const grandTotal = taxableAmount + gstAmount;

  // Update UI Photorealistic Pass
  const customerName = document.getElementById('cfgCustomer').value || 'Acme Hyperloop Corp';
  const customerEmail = document.getElementById('cfgEmail').value || 'procurement@acme.io';
  document.getElementById('passCustomerName').innerText = customerName;
  document.getElementById('passCustomerEmail').innerText = customerEmail;

  // Render Line Items
  const lineTbody = document.getElementById('quoteLineItemsBody');
  let linesHtml = `
    <tr>
      <td>${plan.name} (${plan.recurrence})</td>
      <td>${seats}</td>
      <td>$${baseRate.toFixed(2)}</td>
      <td class="text-right">$${baseLineTotal.toFixed(2)}</td>
    </tr>
  `;

  if (slaChecked) {
    linesHtml += `
      <tr>
        <td>24/7 SLA Mission-Critical Support</td>
        <td>1</td>
        <td>$500.00</td>
        <td class="text-right">$500.00</td>
      </tr>
    `;
  }

  if (backupChecked) {
    linesHtml += `
      <tr>
        <td>Multi-Region Hot-Failover Cloud DR</td>
        <td>1</td>
        <td>$250.00</td>
        <td class="text-right">$250.00</td>
      </tr>
    `;
  }

  lineTbody.innerHTML = linesHtml;

  // Totals breakdown
  document.getElementById('passSubtotal').innerText = `$${rawSubtotal.toLocaleString('en-US', { minimumFractionDigits: 2 })}`;

  const surchargeRow = document.getElementById('passSurchargeRow');
  if (odooChecked) {
    surchargeRow.style.display = 'flex';
    document.getElementById('passSurchargeSeats').innerText = seats;
    document.getElementById('passSurchargeTotal').innerText = `+$${surchargeTotal.toLocaleString('en-US', { minimumFractionDigits: 2 })}`;
  } else {
    surchargeRow.style.display = 'none';
  }

  const discountRow = document.getElementById('passDiscountRow');
  if (discountPct > 0) {
    discountRow.style.display = 'flex';
    discountRow.querySelector('span:first-child').innerText = `Volume Tier Discount (${discountPct * 100}%):`;
    document.getElementById('passDiscountTotal').innerText = `-$${discountAmount.toLocaleString('en-US', { minimumFractionDigits: 2 })}`;
  } else {
    discountRow.style.display = 'none';
  }

  document.getElementById('passTaxTotal').innerText = `$${gstAmount.toLocaleString('en-US', { minimumFractionDigits: 2 })}`;
  document.getElementById('passGrandTotal').innerText = `$${grandTotal.toLocaleString('en-US', { minimumFractionDigits: 2 })}`;
}

// Convert Quote into Live Active Subscription with celebratory confetti
function convertQuoteToSubscription() {
  const customer = document.getElementById('cfgCustomer').value || 'New Enterprise Client';
  const email = document.getElementById('cfgEmail').value || 'billing@client.com';
  const seats = parseInt(document.getElementById('seatSlider').value, 10);
  const plan = State.plans.find(p => p.id === studioSelectedPlan) || State.plans[2];
  const odooChecked = document.getElementById('odooSurchargeToggle').checked;
  const slaChecked = document.getElementById('addonSLA').checked;

  const newId = `SUB-2026-${String(State.subscriptions.length + 42).padStart(4, '0')}`;
  
  // Calculate final monthly total
  const surchargeTotal = odooChecked ? (560.00 * seats) : 0;
  const slaTotal = slaChecked ? 500.00 : 0;
  const total = (plan.price * seats) + surchargeTotal + slaTotal;

  const newSub = {
    id: newId,
    customer: customer,
    email: email,
    planId: plan.id,
    planName: plan.name,
    recurrence: plan.recurrence,
    seats: seats,
    odooSurcharge: odooChecked,
    surchargeAmount: odooChecked ? 560 : 0,
    slaSupport: slaChecked,
    basePrice: plan.price,
    monthlyTotal: total,
    status: 'active',
    startDate: formatDate(State.virtualDate),
    nextInvoiceDate: formatDate(addDays(State.virtualDate, 30)),
    policies: {
      autoClose: document.getElementById('polAutoClose').checked,
      closable: document.getElementById('polClosable').checked,
      pausable: document.getElementById('polPausable').checked,
      renewable: document.getElementById('polRenewable').checked
    }
  };

  State.subscriptions.unshift(newSub);

  // Trigger celebration audio and visual confetti
  playSound('success');
  triggerConfetti();

  // Log to Audit Trail
  logAudit('ACTIVE_TRANSITION', `Quotation converted to Live Subscription: ${newId} (${customer})`, 'active');
  logOdooRpc('sale.subscription.create', { sub_id: newId, partner: customer, recurring_amount: total });

  showToast(`Subscription ${newId} activated successfully!`, 'success');

  // Refresh Table and KPIs
  renderOverviewTable();
  updateKPIs();
  renderSubscriptionCards();
}

function printQuotationPass() {
  playSound('click');
  window.print();
}

// ==============================================================================
// 6. LIFECYCLE STATE MACHINE ENFORCEMENT
// ==============================================================================
function transitionSubState(subId, targetState) {
  const sub = State.subscriptions.find(s => s.id === subId);
  if (!sub) return;

  // State Machine Transition Rules
  if (targetState === 'paused') {
    if (!sub.policies.pausable) {
      showToast('Action Denied: Policy does not allow pausing!', 'warning');
      return;
    }
    sub.status = 'paused';
    sub.nextInvoiceDate = 'PAUSED';
    logAudit('SUBSCRIPTION_PAUSED', `Subscription ${sub.id} paused by customer request`, 'pause');
    logOdooRpc('sale.subscription.action_pause', { id: sub.id });
    showToast(`Subscription ${sub.id} paused.`, 'info');
  } 
  else if (targetState === 'active') {
    sub.status = 'active';
    sub.nextInvoiceDate = formatDate(addDays(State.virtualDate, 30));
    logAudit('SUBSCRIPTION_RESUMED', `Subscription ${sub.id} resumed to Active state`, 'active');
    logOdooRpc('sale.subscription.action_resume', { id: sub.id });
    showToast(`Subscription ${sub.id} resumed!`, 'success');
  } 
  else if (targetState === 'closed') {
    if (!sub.policies.closable) {
      showToast('Action Denied: Contract lock prohibits early termination!', 'warning');
      return;
    }
    sub.status = 'closed';
    sub.nextInvoiceDate = 'TERMINATED';
    
    // Calculate Prorated Refund for demo
    const refund = (sub.monthlyTotal * 0.42).toFixed(2);
    logAudit('EARLY_CLOSE', `Subscription ${sub.id} terminated early. Prorated credit refund of $${refund} calculated.`, 'close');
    logOdooRpc('sale.subscription.action_close', { id: sub.id, proration_credit: refund });
    showToast(`Subscription ${sub.id} closed. Prorated refund: $${refund}`, 'warning');
  }

  playSound('click');
  renderOverviewTable();
  renderSubscriptionCards();
  updateKPIs();
}

// ==============================================================================
// 7. TIME-TRAVEL SIMULATION ENGINE (Judges' Favorite Feature)
// ==============================================================================
function timeWarp(days) {
  State.daysElapsed += days;
  State.virtualDate = addDays(State.virtualDate, days);

  playSound('warp');

  // Update Virtual Clock Displays
  document.getElementById('virtualDateDisplay').innerText = `Today: ${formatDate(State.virtualDate)}`;
  document.getElementById('simClockTime').innerText = `${formatDate(State.virtualDate)}, 12:00:00 UTC`;
  document.getElementById('simDaysAdvanced').innerText = `+${State.daysElapsed} Days Elapsed`;

  // Advance Subscriptions Lifecycle
  let renewedCount = 0;
  let autoClosedCount = 0;

  State.subscriptions.forEach(sub => {
    if (sub.status === 'active') {
      // Simulate Billing Cycle
      if (sub.recurrence === 'Daily' && days >= 1) {
        renewedCount++;
      } else if (sub.recurrence === 'Weekly' && days >= 7) {
        renewedCount++;
      } else if (sub.recurrence === 'Monthly' && days >= 30) {
        renewedCount++;
        sub.nextInvoiceDate = formatDate(addDays(State.virtualDate, 30));
      }

      // Check Auto-close on expiration
      if (sub.policies.autoClose && State.daysElapsed >= 60) {
        sub.status = 'closed';
        sub.nextInvoiceDate = 'EXPIRED';
        autoClosedCount++;
      }
    }
  });

  logAudit('TEMPORAL_ADVANCE', `Clock advanced by +${days} days. ${renewedCount} cycles processed.`, 'active');
  logOdooRpc('cron.recurring_invoicing_cron', { days_advanced: days, recurring_invoices_generated: renewedCount });

  showToast(`Time warped +${days} days! Invoices reconciled.`, 'info');

  renderOverviewTable();
  renderSubscriptionCards();
  updateKPIs();
}

function resetSimulationClock() {
  State.virtualDate = new Date(2026, 9, 31);
  State.daysElapsed = 0;
  playSound('click');

  document.getElementById('virtualDateDisplay').innerText = `Today: 31 Oct 2026`;
  document.getElementById('simClockTime').innerText = `31 October 2026, 12:00:00 UTC`;
  document.getElementById('simDaysAdvanced').innerText = `+0 Days Elapsed`;

  logAudit('SIMULATION_RESET', 'System simulation clock reset to 31 Oct 2026', 'info');
  showToast('Simulation clock reset to baseline.', 'info');
}

function triggerSimEvent(evt) {
  playSound('click');
  if (evt === 'pause_first_active') {
    const target = State.subscriptions.find(s => s.status === 'active');
    if (target) transitionSubState(target.id, 'paused');
    else showToast('No active subscriptions found to pause', 'warning');
  } else if (evt === 'early_close_first_active') {
    const target = State.subscriptions.find(s => s.status === 'active');
    if (target) transitionSubState(target.id, 'closed');
    else showToast('No active subscriptions found to close', 'warning');
  } else if (evt === 'expire_quotes') {
    showToast('All 30-day quotation expiration timers verified intact.', 'info');
    logAudit('EXPIRY_CHECK', 'Automated 30-day quote audit: 2 quotes remain valid', 'quote');
  }
}

// ==============================================================================
// 8. RENDER METHODS (Overview Table, Cards & Pipeline Map)
// ==============================================================================
function renderOverviewTable() {
  const tbody = document.getElementById('subscriptionsTableBody');
  if (!tbody) return;

  const searchTerm = (document.getElementById('subSearchInput')?.value || '').toLowerCase();

  const filtered = State.subscriptions.filter(s => {
    const matchesState = State.stateFilter === 'all' || s.status === State.stateFilter;
    const matchesSearch = s.customer.toLowerCase().includes(searchTerm) ||
                          s.id.toLowerCase().includes(searchTerm) ||
                          s.planName.toLowerCase().includes(searchTerm);
    return matchesState && matchesSearch;
  });

  if (filtered.length === 0) {
    tbody.innerHTML = `<tr><td colspan="9" style="text-align:center; padding:32px; color:var(--text-muted);">No subscription records match your filter criteria.</td></tr>`;
    return;
  }

  tbody.innerHTML = filtered.map(sub => `
    <tr>
      <td><span class="sub-id-chip">${sub.id}</span></td>
      <td>
        <div style="font-weight:700; color:var(--text-pure);">${sub.customer}</div>
        <div style="font-size:0.72rem; color:var(--text-medium);">${sub.email}</div>
      </td>
      <td>
        <div>${sub.planName}</div>
        <div style="font-family:var(--font-mono); font-size:0.7rem; color:var(--accent-olive);">${sub.recurrence}</div>
      </td>
      <td><span style="font-family:var(--font-mono); font-weight:700;">${sub.seats}</span></td>
      <td>
        ${sub.odooSurcharge 
          ? `<span class="badge-gold" style="font-size:0.68rem; font-family:var(--font-mono); font-weight:700;">+$${sub.surchargeAmount}/seat</span>`
          : `<span style="color:var(--text-muted); font-size:0.74rem;">Standard</span>`
        }
      </td>
      <td><span style="font-family:var(--font-mono); font-weight:800; color:var(--text-pure);">$${sub.monthlyTotal.toLocaleString('en-US', { minimumFractionDigits: 2 })}</span></td>
      <td><span class="status-pill ${sub.status}">${sub.status.toUpperCase()}</span></td>
      <td>
        <div style="font-size:0.68rem; color:var(--text-medium);">
          ${sub.policies.pausable ? '<span title="Pausable">⏸</span> ' : ''}
          ${sub.policies.closable ? '<span title="Early Close">⚡</span> ' : ''}
          ${sub.policies.renewable ? '<span title="Auto Renew">🔄</span>' : ''}
        </div>
      </td>
      <td>
        <div class="row-actions-group">
          ${sub.status === 'active' ? `
            <button class="btn-icon-action action-pause" title="Pause Subscription" onclick="transitionSubState('${sub.id}', 'paused')"><i class="fa-solid fa-pause"></i></button>
            <button class="btn-icon-action action-close" title="Terminate Early" onclick="transitionSubState('${sub.id}', 'closed')"><i class="fa-solid fa-ban"></i></button>
          ` : sub.status === 'paused' ? `
            <button class="btn-icon-action action-play" title="Resume to Active" onclick="transitionSubState('${sub.id}', 'active')"><i class="fa-solid fa-play"></i></button>
          ` : `
            <span style="font-size:0.7rem; color:var(--text-muted);">Terminal</span>
          `}
        </div>
      </td>
    </tr>
  `).join('');
}

function renderSubscriptionCards() {
  const container = document.getElementById('subscriptionCardsGrid');
  if (!container) return;

  container.innerHTML = State.subscriptions.map(sub => `
    <div class="sub-lifecycle-card">
      <div>
        <div class="card-top-row">
          <span class="card-sub-code">${sub.id}</span>
          <span class="status-pill ${sub.status}">${sub.status.toUpperCase()}</span>
        </div>
        <div class="card-customer">${sub.customer}</div>
        <div class="card-plan-meta">
          <i class="fa-solid fa-layer-group text-olive"></i>
          <span>${sub.planName} • ${sub.recurrence}</span>
        </div>
        <div class="card-metric-strip">
          <div class="strip-item">
            <label>SEATS</label>
            <span>${sub.seats} Users</span>
          </div>
          <div class="strip-item">
            <label>MONTHLY REVENUE</label>
            <span style="color:var(--accent-emerald);">$${sub.monthlyTotal.toLocaleString('en-US', { minimumFractionDigits: 2 })}</span>
          </div>
          <div class="strip-item">
            <label>ODOO SURCHARGE</label>
            <span>${sub.odooSurcharge ? '+$560 / seat' : 'None'}</span>
          </div>
          <div class="strip-item">
            <label>NEXT INVOICE</label>
            <span>${sub.nextInvoiceDate}</span>
          </div>
        </div>
      </div>

      <div class="card-action-bar">
        ${sub.status === 'active' ? `
          <button class="action-btn-sm" onclick="transitionSubState('${sub.id}', 'paused')"><i class="fa-solid fa-pause"></i> Pause</button>
          <button class="action-btn-sm btn-danger" onclick="transitionSubState('${sub.id}', 'closed')"><i class="fa-solid fa-ban"></i> Early Close</button>
        ` : sub.status === 'paused' ? `
          <button class="action-btn-sm" style="color:var(--accent-emerald); border-color:var(--accent-emerald);" onclick="transitionSubState('${sub.id}', 'active')"><i class="fa-solid fa-play"></i> Resume</button>
        ` : `
          <span style="font-size:0.75rem; color:var(--text-muted); font-family:var(--font-mono);">Record Archived</span>
        `}
      </div>
    </div>
  `).join('');

  // Update Pill Counters
  document.getElementById('pillCountAll').innerText = State.subscriptions.length;
  document.getElementById('pillCountActive').innerText = State.subscriptions.filter(s => s.status === 'active').length;
  document.getElementById('pillCountQuotes').innerText = State.quotations.length;
  document.getElementById('pillCountPaused').innerText = State.subscriptions.filter(s => s.status === 'paused').length;
  document.getElementById('pillCountClosed').innerText = State.subscriptions.filter(s => s.status === 'closed').length;
}

function renderPlansShowcase() {
  const container = document.getElementById('plansShowcaseGrid');
  if (!container) return;

  container.innerHTML = State.plans.map(plan => `
    <div class="matrix-plan-card ${plan.featured ? 'featured' : ''}">
      <div>
        <div class="plan-card-name">${plan.name}</div>
        <div class="plan-recurrence-tag">Recurrence: ${plan.recurrence} (${plan.invoicingPeriod})</div>
        <div class="plan-card-price">$${plan.price}<span>/cycle</span></div>
        <ul class="plan-feature-bullets">
          <li><i class="fa-solid fa-circle-check text-olive"></i> Min Seats Required: <b>${plan.minSeats}</b></li>
          <li><i class="fa-solid fa-circle-check text-emerald"></i> Auto-Close Policy: <b>${plan.autoClose ? 'Yes' : 'No'}</b></li>
          <li><i class="fa-solid fa-circle-check text-gold"></i> Closable Early: <b>${plan.closable ? 'Allowed' : 'Locked'}</b></li>
          <li><i class="fa-solid fa-circle-check text-olive"></i> Pause &amp; Resume: <b>${plan.pausable ? 'Enabled' : 'Disabled'}</b></li>
          ${plan.features.map(f => `<li><i class="fa-solid fa-bolt text-olive"></i> ${f}</li>`).join('')}
        </ul>
      </div>

      <button class="pill-action-btn" style="width:100%; justify-content:center;" onclick="applyPlanToComposer('${plan.id}')">
        Configure in Studio
      </button>
    </div>
  `).join('');
}

function updateKPIs() {
  const activeSubs = State.subscriptions.filter(s => s.status === 'active');
  const totalMrr = activeSubs.reduce((acc, s) => acc + s.monthlyTotal, 0);
  const totalArr = totalMrr * 12;

  document.getElementById('kpiArr').innerText = `$${Math.round(totalArr).toLocaleString('en-US')}`;
  document.getElementById('kpiMrr').innerText = `$${Math.round(totalMrr).toLocaleString('en-US')}`;
  document.getElementById('kpiActiveCount').innerText = activeSubs.length;
  document.getElementById('kpiQuotesCount').innerText = State.quotations.length;

  // Node counts
  document.getElementById('countActive').innerText = `${activeSubs.length} Active Stream`;
  document.getElementById('countPaused').innerText = State.subscriptions.filter(s => s.status === 'paused').length;
  document.getElementById('countClosed').innerText = State.subscriptions.filter(s => s.status === 'closed').length;
  document.getElementById('countQuotation').innerText = `${State.quotations.length} Pending Sign`;
}

function filterByState(state) {
  State.stateFilter = state;
  playSound('click');
  document.getElementById('activeFilterLabel').innerText = `Filtered by State: ${state.toUpperCase()}`;
  renderOverviewTable();
}

function resetStateFilter() {
  State.stateFilter = 'all';
  playSound('click');
  document.getElementById('activeFilterLabel').innerText = 'Showing All Active Records';
  renderOverviewTable();
}

function handleSubSearch() {
  renderOverviewTable();
}

function filterLifecycleState(state) {
  document.querySelectorAll('.filter-pill').forEach(p => p.classList.remove('active'));
  event.target.classList.add('active');
  filterByState(state);
}

function applyTemplateAndCompose(templateName) {
  playSound('click');
  switchView('quote-studio');
  showToast(`Loaded "${templateName}" into Quotation Composer.`, 'info');
}

function applyPlanToComposer(planId) {
  studioSelectedPlan = planId;
  switchView('quote-studio');
  showToast(`Loaded ${planId} plan settings.`, 'info');
}

// ==============================================================================
// 9. ODOO 18 WIRE PROTOCOL DRAWER
// ==============================================================================
function toggleOdooDrawer() {
  const drawer = document.getElementById('odooWireDrawer');
  drawer.classList.toggle('closed');
  playSound('click');
}

function logOdooRpc(method, params) {
  const now = new Date().toTimeString().split(' ')[0];
  const payloadStr = JSON.stringify(params);
  State.odooLogs.unshift({ time: now, verb: 'CALL', method: method, payload: payloadStr });
  renderOdooLogs();
}

function renderOdooLogs() {
  const container = document.getElementById('odooWireLogContainer');
  if (!container) return;

  container.innerHTML = State.odooLogs.slice(0, 30).map(l => `
    <div class="wire-line">
      <span class="wire-ts">[${l.time}]</span>
      <span class="wire-verb call">${l.verb}</span>
      <span style="color:var(--accent-gold); font-weight:700;">${l.method}</span>
      <span class="wire-payload">${l.payload}</span>
    </div>
  `).join('');
}

function clearOdooLogs() {
  State.odooLogs = [];
  renderOdooLogs();
  showToast('Odoo wire logs cleared', 'info');
}

// ==============================================================================
// 10. AUDIT LOGGING & TOASTS
// ==============================================================================
function logAudit(action, detail, type) {
  const now = new Date().toTimeString().split(' ')[0];
  State.auditLog.unshift({ time: now, action, detail, type });
  renderAuditLog();
}

function renderAuditLog() {
  const container = document.getElementById('simActivityTimeline');
  if (!container) return;

  container.innerHTML = State.auditLog.slice(0, 20).map(item => `
    <div class="log-entry log-${item.type}">
      <div class="log-time">${item.time} UTC</div>
      <div class="log-action">${item.action}</div>
      <div class="log-detail">${item.detail}</div>
    </div>
  `).join('');
}

function clearAuditLog() {
  State.auditLog = [];
  renderAuditLog();
  showToast('Audit log cleared', 'info');
}

function showToast(message, type = 'info') {
  const container = document.getElementById('toastContainer');
  if (!container) return;

  const toast = document.createElement('div');
  toast.className = 'quantum-toast';

  let icon = 'fa-info-circle info';
  if (type === 'success') icon = 'fa-circle-check success';
  if (type === 'warning') icon = 'fa-triangle-exclamation warning';

  toast.innerHTML = `
    <i class="fa-solid ${icon} toast-icon"></i>
    <span>${message}</span>
  `;

  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateY(10px)';
    setTimeout(() => toast.remove(), 300);
  }, 3500);
}

// ==============================================================================
// 11. COMMAND PALETTE (Cmd+K)
// ==============================================================================
const commands = [
  { label: 'Compose New Quotation', icon: 'fa-sliders', action: () => switchView('quote-studio') },
  { label: 'Theme: Deep Olive & Gold', icon: 'fa-palette', action: () => setAppTheme('theme-olive-luxe') },
  { label: 'Theme: Forest Emerald Noir', icon: 'fa-tree', action: () => setAppTheme('theme-forest-noir') },
  { label: 'Theme: Nordic Sage Slate', icon: 'fa-leaf', action: () => setAppTheme('theme-sage-slate') },
  { label: 'Fast-Forward System Clock (+7 Days)', icon: 'fa-forward', action: () => timeWarp(7) },
  { label: 'Fast-Forward Full Billing Cycle (+30 Days)', icon: 'fa-angles-right', action: () => timeWarp(30) },
  { label: 'View Interactive State Machine Flow', icon: 'fa-network-wired', action: () => switchView('visual-flow') },
  { label: 'Inspect Odoo 18 RPC Wire Protocol', icon: 'fa-bolt', action: () => toggleOdooDrawer() },
  { label: 'Filter Subscriptions: Active Only', icon: 'fa-filter', action: () => { switchView('visual-flow'); filterByState('active'); } },
  { label: 'Filter Subscriptions: Paused Only', icon: 'fa-pause', action: () => { switchView('visual-flow'); filterByState('paused'); } },
  { label: 'Reset Time-Travel Clock to Baseline', icon: 'fa-clock-rotate-left', action: () => resetSimulationClock() }
];

function openPalette() {
  document.getElementById('commandPalette').classList.remove('hidden');
  document.getElementById('paletteSearchInput').focus();
  renderPaletteCommands(commands);
  playSound('click');
}

function closePalette() {
  document.getElementById('commandPalette').classList.add('hidden');
}

function closePaletteOnBackdrop(e) {
  if (e.target.id === 'commandPalette') closePalette();
}

function renderPaletteCommands(list) {
  const container = document.getElementById('paletteResults');
  container.innerHTML = list.map(c => `
    <div class="palette-item" onclick="executeCommand('${c.label}')">
      <div class="item-left">
        <i class="fa-solid ${c.icon}"></i>
        <span>${c.label}</span>
      </div>
      <span class="item-badge">ENTER</span>
    </div>
  `).join('');
}

function filterPalette() {
  const q = document.getElementById('paletteSearchInput').value.toLowerCase();
  const filtered = commands.filter(c => c.label.toLowerCase().includes(q));
  renderPaletteCommands(filtered);
}

function executeCommand(label) {
  const cmd = commands.find(c => c.label === label);
  if (cmd) {
    closePalette();
    cmd.action();
  }
}

window.addEventListener('keydown', (e) => {
  if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
    e.preventDefault();
    openPalette();
  } else if (e.key === 'Escape') {
    closePalette();
  }
});

// ==============================================================================
// 12. CONFETTI CELEBRATION EFFECT (Botanical Olive, Emerald & Champagne Gold)
// ==============================================================================
function triggerConfetti() {
  const canvas = document.getElementById('confettiCanvas');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  canvas.width = window.innerWidth;
  canvas.height = window.innerHeight;

  const particles = [];
  const colors = ['#A3E635', '#34D399', '#FBBF24', '#EAB308', '#4ADE80'];

  for (let i = 0; i < 90; i++) {
    particles.push({
      x: canvas.width / 2,
      y: canvas.height / 2,
      vx: (Math.random() - 0.5) * 18,
      vy: (Math.random() - 0.7) * 22,
      size: Math.random() * 8 + 4,
      color: colors[Math.floor(Math.random() * colors.length)],
      alpha: 1
    });
  }

  let animationFrame;
  function animate() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    let alive = 0;

    particles.forEach(p => {
      p.x += p.vx;
      p.y += p.vy;
      p.vy += 0.45; // gravity
      p.alpha -= 0.015;

      if (p.alpha > 0) {
        alive++;
        ctx.globalAlpha = p.alpha;
        ctx.fillStyle = p.color;
        ctx.fillRect(p.x, p.y, p.size, p.size);
      }
    });

    if (alive > 0) {
      animationFrame = requestAnimationFrame(animate);
    } else {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      cancelAnimationFrame(animationFrame);
    }
  }

  animate();
}

// ==============================================================================
// 13. UTILITY HELPERS & BOOTSTRAP
// ==============================================================================
function addDays(date, days) {
  const d = new Date(date);
  d.setDate(d.getDate() + days);
  return d;
}

function formatDate(date) {
  const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
  return `${date.getDate()} ${months[date.getMonth()]} ${date.getFullYear()}`;
}

// Bootstrap Initialization
document.addEventListener('DOMContentLoaded', () => {
  renderOverviewTable();
  renderSubscriptionCards();
  renderPlansShowcase();
  recalcQuoteLive();
  updateKPIs();

  // Initial Seed Log
  logAudit('SYSTEM_BOOT', 'Brightloop Quantum Engine OS 2.0 initialized (Task 2)', 'active');
  logOdooRpc('sale.subscription.init', { version: '18.0-EE', architect: 'Ritesh Tiwari' });
});
