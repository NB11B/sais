document.addEventListener('DOMContentLoaded', () => {
    
    function getAdminToken() {
        return sessionStorage.getItem('sais_admin_token') || '';
    }

    function setAdminToken(token) {
        sessionStorage.setItem('sais_admin_token', token);
    }
    
    // Elements
    const cardsContainer = document.getElementById('cards-container');
    const cardsCount = document.getElementById('cards-count');
    
    const obsContainer = document.getElementById('obs-container');
    const obsCount = document.getElementById('obs-count');
    
    const graphNodesCount = document.getElementById('graph-nodes-count');
    const graphEdgesCount = document.getElementById('graph-edges-count');
    const graphDetails = document.getElementById('graph-details');

    const priorityStrip = document.getElementById('priority-strip');
    const domainStatusContainer = document.getElementById('domain-status-container');
    const toggleOkBtn = document.getElementById('toggle-ok-btn');
    
    let showOkCards = false;

    if (toggleOkBtn) {
        toggleOkBtn.onclick = () => {
            showOkCards = !showOkCards;
            toggleOkBtn.classList.toggle('active', showOkCards);
            toggleOkBtn.textContent = showOkCards ? 'Hide OK' : 'Show OK';
            fetchCards();
        };
    }

    // Livestock Modal Elements
    const lsModal = document.getElementById('livestock-modal');
    const openLsBtn = document.getElementById('open-livestock-btn');
    const closeLsBtn = document.querySelector('.close-modal');
    const lsForm = document.getElementById('livestock-form');
    const lsPaddockSelect = document.getElementById('ls_paddock_id');

    const waterModal = document.getElementById('water-modal');
    const openWaterBtn = document.getElementById('open-water-btn');
    const waterForm = document.getElementById('water-form');

    const plantModal = document.getElementById('plant-modal');
    const openPlantBtn = document.getElementById('open-plant-btn');
    const plantForm = document.getElementById('plant-form');
    const plPaddockSelect = document.getElementById('pl_paddock_id');

    const soilModal = document.getElementById('soil-modal');
    const openSoilBtn = document.getElementById('open-soil-btn');
    const soilForm = document.getElementById('soil-form');
    const slPaddockSelect = document.getElementById('sl_paddock_id');

    const infraModal = document.getElementById('infra-modal');
    const openInfraBtn = document.getElementById('open-infra-btn');
    const infraForm = document.getElementById('infra-form');

    // Modal Control
    if (openLsBtn) {
        openLsBtn.onclick = (e) => {
            e.preventDefault();
            lsModal.style.display = 'block';
            populatePaddocks(lsPaddockSelect);
        };
    }

    if (openWaterBtn) {
        openWaterBtn.onclick = (e) => {
            e.preventDefault();
            waterModal.style.display = 'block';
        };
    }

    if (openPlantBtn) {
        openPlantBtn.onclick = (e) => {
            e.preventDefault();
            plantModal.style.display = 'block';
            populatePaddocks(plPaddockSelect);
        };
    }

    if (openSoilBtn) {
        openSoilBtn.onclick = (e) => {
            e.preventDefault();
            soilModal.style.display = 'block';
            populatePaddocks(slPaddockSelect);
        };
    }

    if (openInfraBtn) {
        openInfraBtn.onclick = (e) => {
            e.preventDefault();
            infraModal.style.display = 'block';
        };
    }

    // Generic close for all modals
    document.querySelectorAll('.close-modal').forEach(btn => {
        btn.onclick = () => {
            lsModal.style.display = 'none';
            waterModal.style.display = 'none';
            plantModal.style.display = 'none';
            soilModal.style.display = 'none';
            infraModal.style.display = 'none';
        };
    });

    window.onclick = (event) => {
        if (event.target == lsModal) lsModal.style.display = 'none';
        if (event.target == waterModal) waterModal.style.display = 'none';
        if (event.target == plantModal) plantModal.style.display = 'none';
        if (event.target == soilModal) soilModal.style.display = 'none';
        if (event.target == infraModal) infraModal.style.display = 'none';
    };

    if (soilForm) {
        soilForm.onsubmit = async (e) => {
            e.preventDefault();
            const paddockId = slPaddockSelect.value;
            const payload = {
                schema: "sais.soil_observation.v1",
                id: `soil-${paddockId}-${Date.now()}`,
                farm_id: "local",
                paddock_id: paddockId,
                timestamp: new Date().toISOString(),
                infiltration_mm_hr: parseFloat(document.getElementById('sl_rate').value),
                notes: document.getElementById('sl_notes').value
            };

            try {
                const res = await fetch('/api/soil/observations', {
                    method: 'POST',
                    headers: { 
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${getAdminToken()}`
                    },
                    body: JSON.stringify(payload)
                });
                if (res.ok) {
                    soilModal.style.display = 'none';
                    soilForm.reset();
                    fetchCards();
                    fetchObservations();
                }
            } catch (e) { console.error(e); }
        };
    }

    if (infraForm) {
        infraForm.onsubmit = async (e) => {
            e.preventDefault();
            const assetId = document.getElementById('inf_id').value;
            const payload = {
                id: assetId,
                farm_id: "local",
                asset_type: document.getElementById('inf_type').value,
                status: document.getElementById('inf_status').value
            };

            try {
                const res = await fetch('/api/infrastructure/status', {
                    method: 'POST',
                    headers: { 
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${getAdminToken()}`
                    },
                    body: JSON.stringify(payload)
                });
                if (res.ok) {
                    infraModal.style.display = 'none';
                    infraForm.reset();
                    fetchCards();
                    fetchObservations();
                }
            } catch (e) { console.error(e); }
        };
    }

    if (plantForm) {
        plantForm.onsubmit = async (e) => {
            e.preventDefault();
            const paddockId = plPaddockSelect.value;
            const payload = {
                schema: "sais.plant_observation.v1",
                id: `plant-${paddockId}-${Date.now()}`,
                farm_id: "local",
                paddock_id: paddockId,
                timestamp: new Date().toISOString(),
                forage_mass_kg_ha: parseFloat(document.getElementById('pl_mass').value),
                height_cm: parseFloat(document.getElementById('pl_height').value),
                recovery_score: parseInt(document.getElementById('pl_recovery').value)
            };

            try {
                const res = await fetch('/api/plant/observations', {
                    method: 'POST',
                    headers: { 
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${getAdminToken()}`
                    },
                    body: JSON.stringify(payload)
                });
                if (res.ok) {
                    plantModal.style.display = 'none';
                    plantForm.reset();
                    fetchCards();
                    fetchObservations();
                }
            } catch (e) { console.error(e); }
        };
    }

    if (waterForm) {
        waterForm.onsubmit = async (e) => {
            e.preventDefault();
            const assetId = document.getElementById('water_asset_id').value;
            const level = parseFloat(document.getElementById('water_level').value);
            
            // Post as a standard observation for PFKR-1
            const payload = {
                schema: "sais.observation.v1",
                node_id: assetId,
                farm_id: "local",
                timestamp: new Date().toISOString(),
                measurement_id: "water.tank.level_percent",
                layer: "Water Infrastructure",
                value: level,
                unit: "%",
                source: { id: "manual_observation" }
            };

            try {
                const res = await fetch('/api/observations', {
                    method: 'POST',
                    headers: { 
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${getAdminToken()}`
                    },
                    body: JSON.stringify(payload)
                });
                if (res.ok) {
                    waterModal.style.display = 'none';
                    waterForm.reset();
                    fetchCards();
                    fetchObservations();
                }
            } catch (e) { console.error(e); }
        };
    }

    async function populatePaddocks(selectEl) {
        if (!selectEl) return;
        try {
            const res = await fetch('/api/graph', {
                headers: { 'Authorization': `Bearer ${getAdminToken()}` }
            });
            if (res.status === 401) {
                const token = prompt("Admin Token required:");
                if (token) {
                    setAdminToken(token);
                    return populatePaddocks(selectEl);
                }
            }
            const data = await res.json();
            const paddocks = data.nodes.filter(n => n.labels.includes("Paddock"));
            
            selectEl.innerHTML = '<option value="">Select Paddock...</option>';
            paddocks.forEach(p => {
                const opt = document.createElement('option');
                opt.value = p.id;
                opt.innerText = p.name;
                selectEl.appendChild(opt);
            });
        } catch (e) { console.error(e); }
    }

    if (lsForm) {
        lsForm.onsubmit = async (e) => {
            e.preventDefault();
            const payload = {
                id: `ls-check-${Date.now()}`,
                farm_id: 'local',
                paddock_id: lsPaddockSelect.value,
                timestamp: new Date().toISOString(),
                bcs: parseFloat(document.getElementById('ls_bcs').value) || null,
                manure_score: parseInt(document.getElementById('ls_manure').value) || null,
                health_notes: document.getElementById('ls_notes').value
            };

            try {
                const res = await fetch('/api/livestock/observations', {
                    method: 'POST',
                    headers: { 
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${getAdminToken()}`
                    },
                    body: JSON.stringify(payload)
                });
                if (res.ok) {
                    lsModal.style.display = 'none';
                    lsForm.reset();
                    fetchCards();
                    fetchObservations();
                }
            } catch (e) { console.error(e); }
        };
    }

    // Fetch Cards
    async function fetchCards() {
        try {
            const res = await fetch('/api/cards', {
                headers: { 'Authorization': `Bearer ${getAdminToken()}` }
            });
            if (res.status === 401) {
                const token = prompt("Admin Token required:");
                if (token) {
                    setAdminToken(token);
                    return fetchCards();
                }
            }
            const data = await res.json();
            
            cardsCount.textContent = data.cards.length;
            
            if (data.cards.length === 0) {
            // 1. Handle RanchHealthCard (Summary Panel)
            const healthCard = data.cards.find(c => c.card_type === 'RanchHealthCard');
            const summaryPanel = document.getElementById('summary-panel');
            if (healthCard && summaryPanel) {
                summaryPanel.style.display = 'block';
                const statusClass = `status-${healthCard.status}`;
                let scoreHtml = '';
                if (healthCard.score !== undefined) {
                    scoreHtml = `<div class="health-score">${healthCard.score}%</div>`;
                }
                
                const container = document.getElementById('ranch-health-container');
                container.innerHTML = `
                    <div class="health-header">
                        <div class="health-title">${healthCard.observation}</div>
                        <div class="health-status-badge ${statusClass}">${healthCard.status.toUpperCase()}</div>
                    </div>
                    ${scoreHtml}
                    <div class="health-context">${healthCard.context.join(' &middot; ')}</div>
                `;
            } else if (summaryPanel) {
                summaryPanel.style.display = 'none';
            }

            // 2. Clear Containers
            if (priorityStrip) priorityStrip.innerHTML = '';
            cardsContainer.innerHTML = '';
            if (domainStatusContainer) domainStatusContainer.innerHTML = '';

            // 3. Filter and Sort
            const operationalCards = data.cards.filter(c => c.card_type !== 'RanchHealthCard');
            
            // Priority Cards (Alert/Watch)
            const priorityCards = operationalCards.filter(c => ['alert', 'watch', 'action'].includes(c.status));
            // OK Cards
            const okCards = operationalCards.filter(c => !['alert', 'watch', 'action'].includes(c.status));

            // 4. Render Priority Strip (Top actionable items)
            priorityCards.forEach(card => {
                const el = createCardElement(card, false);
                if (priorityStrip) priorityStrip.appendChild(el);
            });

            // 5. Render Operational Feed
            // Priority cards are shown in full in the feed too
            priorityCards.forEach(card => {
                const el = createCardElement(card, false);
                cardsContainer.appendChild(el);
            });

            // OK cards are shown based on toggle and are collapsed
            if (showOkCards) {
                okCards.forEach(card => {
                    const el = createCardElement(card, true);
                    cardsContainer.appendChild(el);
                });
            }

            // 6. Update Domain Status Scorecard
            renderDomainScorecard(data.cards);

        } catch (err) {
            console.error('Error fetching cards', err);
        }
    }

    function createCardElement(card, collapsed) {
        const el = document.createElement('div');
        el.className = 'card-item';
        if (collapsed) el.classList.add('collapsed');
        
        if (card.action_status === 'resolved') {
            el.style.opacity = '0.5';
            el.style.pointerEvents = 'none';
        }
        
        const statusClass = `status-${card.status}`;
        const statusText = card.status.replace('_', ' ');
        
        let evidenceHtml = '';
        if (card.evidence && card.evidence.length > 0) {
            evidenceHtml = '<ul class="evidence-list">';
            card.evidence.forEach(ev => {
                evidenceHtml += `<li>${ev}</li>`;
            });
            evidenceHtml += '</ul>';
        }

        const notesHtml = card.notes ? `<div class="card-notes-display"><strong>Farmer Note:</strong> ${card.notes}</div>` : '';
        
        el.innerHTML = `
            <div class="card-header">
                <div class="pfkr-id">${card.pfkr_id || ''}</div>
                <div class="card-title">${card.card_type}</div>
                <div class="card-status ${statusClass}">${statusText}</div>
            </div>
            <div class="pfkr-domain">${card.pfkr_domain || ''}</div>
            <div class="card-meaning">${card.farmer_meaning || ''}</div>
            <div class="card-inspection">${card.suggested_inspection || ''}</div>
            <div class="card-evidence">
                <div style="font-size: 0.75rem; color: var(--text-muted); font-weight: 600;">EVIDENCE CHAIN</div>
                ${evidenceHtml}
            </div>
            ${notesHtml}
            <div class="card-actions">
                <button class="btn-action btn-primary" onclick="takeAction('${card.id}', 'resolved')">Resolve</button>
                <button class="btn-action" onclick="toggleNotes('${card.id}')">Add Note</button>
            </div>
            <div id="notes-area-${card.id}" class="card-notes-area" style="display:none;">
                <textarea class="card-notes-input" placeholder="Enter field observation..."></textarea>
                <button class="btn-action btn-primary" onclick="saveNote('${card.id}')">Save Note</button>
            </div>
        `;
        return el;
    }

    function renderDomainScorecard(cards) {
        if (!domainStatusContainer) return;
        
        const domains = [
            { id: 'water', label: 'Water', pfkr: 'PFKR-1' },
            { id: 'plant', label: 'Plant', pfkr: 'PFKR-4' },
            { id: 'livestock', label: 'Livestock', pfkr: 'PFKR-5' },
            { id: 'infra', label: 'Infra', pfkr: 'PFKR-8' }
        ];

        domains.forEach(dom => {
            const domainCards = cards.filter(c => c.pfkr_id === dom.pfkr);
            let status = 'ok';
            if (domainCards.some(c => c.status === 'alert')) status = 'alert';
            else if (domainCards.some(c => c.status === 'watch' || c.status === 'action')) status = 'watch';

            const el = document.createElement('div');
            el.className = 'domain-status-item';
            el.innerHTML = `
                <div class="domain-info">
                    <span class="domain-label">${dom.label}</span>
                    <span class="domain-value">${dom.pfkr}</span>
                </div>
                <div class="dot pulse" style="background-color: var(--status-${status});"></div>
            `;
            domainStatusContainer.appendChild(el);
        });
    }

    // Card Actions
    window.takeAction = async (cardId, status) => {
        try {
            const res = await fetch(`/api/cards/${cardId}/action`, {
                method: 'POST',
                headers: { 
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${getAdminToken()}`
                },
                body: JSON.stringify({ status })
            });
            if (res.status === 401) {
                const token = prompt("Admin Token required:");
                if (token) {
                    setAdminToken(token);
                    return takeAction(cardId, status);
                }
            }
            fetchCards();
        } catch (err) {
            console.error('Error taking action', err);
        }
    };

    window.toggleNotes = (cardId) => {
        const area = document.getElementById(`notes-area-${cardId}`);
        area.style.display = area.style.display === 'none' ? 'block' : 'none';
    };

    window.saveNote = async (cardId) => {
        const area = document.getElementById(`notes-area-${cardId}`);
        const input = area.querySelector('textarea');
        const notes = input.value;
        
        try {
            const res = await fetch(`/api/cards/${cardId}/action`, {
                method: 'POST',
                headers: { 
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${getAdminToken()}`
                },
                body: JSON.stringify({ notes })
            });
            if (res.status === 401) {
                const token = prompt("Admin Token required:");
                if (token) {
                    setAdminToken(token);
                    return saveNote(cardId);
                }
            }
            fetchCards();
        } catch (err) {
            console.error('Error saving note', err);
        }
    };

    // Fetch Observations
    async function fetchObservations() {
        try {
            const res = await fetch('/api/observations', {
                headers: { 'Authorization': `Bearer ${getAdminToken()}` }
            });
            if (res.status === 401) {
                const token = prompt("Admin Token required:");
                if (token) {
                    setAdminToken(token);
                    return fetchObservations();
                }
            }
            const data = await res.json();
            
            obsCount.textContent = data.observations.length;
            
            if (data.observations.length === 0) {
                obsContainer.innerHTML = '<div class="loading">No recent observations.</div>';
                return;
            }
            
            obsContainer.innerHTML = '';
            data.observations.forEach(obs => {
                const el = document.createElement('div');
                el.className = 'obs-item';
                
                const date = new Date(obs.timestamp);
                const timeStr = date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
                
                el.innerHTML = `
                    <div class="obs-meta">
                        <div class="obs-measurement">${obs.measurement_id}</div>
                        <div class="obs-time">${timeStr} &middot; ${obs.node_id}</div>
                    </div>
                    <div class="obs-val">${obs.value !== null ? obs.value : '--'}</div>
                `;
                obsContainer.appendChild(el);
            });
            
        } catch (err) {
            console.error('Error fetching observations', err);
        }
    }

    // Fetch Graph State
    async function fetchGraphState() {
        try {
            const res = await fetch('/api/graph', {
                headers: { 'Authorization': `Bearer ${getAdminToken()}` }
            });
            if (res.status === 401) {
                const token = prompt("Admin Token required:");
                if (token) {
                    setAdminToken(token);
                    return fetchGraphState();
                }
            }
            const data = await res.json();
            
            graphNodesCount.textContent = data.counts.nodes;
            graphEdgesCount.textContent = data.counts.edges;
            
            if (data.nodes.length === 0) {
                graphDetails.innerHTML = '<div class="loading">Graph is empty.</div>';
                return;
            }
            
            graphDetails.innerHTML = '<div class="node-list"></div>';
            const nodeList = graphDetails.querySelector('.node-list');
            
            // Show only first 15 nodes to avoid clutter
            const displayNodes = data.nodes.slice(0, 15);
            
            displayNodes.forEach(node => {
                const el = document.createElement('div');
                el.className = 'node-item';
                el.innerHTML = `
                    <span class="node-id">${node.id}</span>
                    <span class="node-label">${node.labels.join(', ')}</span>
                `;
                nodeList.appendChild(el);
            });
            
            if (data.nodes.length > 15) {
                const more = document.createElement('div');
                more.className = 'loading';
                more.textContent = `+ ${data.nodes.length - 15} more nodes...`;
                nodeList.appendChild(more);
            }
            
        } catch (err) {
            console.error('Error fetching graph', err);
        }
    }

    // Initial fetch
    fetchCards();
    fetchObservations();
    fetchGraphState();
    
    // Poll every 5 seconds
    setInterval(() => {
        fetchCards();
        fetchObservations();
        fetchGraphState();
    }, 5000);
});
