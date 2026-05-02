document.addEventListener('DOMContentLoaded', () => {
    
    // Elements
    const cardsContainer = document.getElementById('cards-container');
    const cardsCount = document.getElementById('cards-count');
    
    const obsContainer = document.getElementById('obs-container');
    const obsCount = document.getElementById('obs-count');
    
    const graphNodesCount = document.getElementById('graph-nodes-count');
    const graphEdgesCount = document.getElementById('graph-edges-count');
    const graphDetails = document.getElementById('graph-details');

    // Fetch Cards
    async function fetchCards() {
        try {
            const res = await fetch('/api/cards');
            const data = await res.json();
            
            cardsCount.textContent = data.cards.length;
            
            if (data.cards.length === 0) {
                cardsContainer.innerHTML = '<div class="loading">No cards generated yet.</div>';
                return;
            }
            
            cardsContainer.innerHTML = '';
            data.cards.forEach(card => {
                const el = document.createElement('div');
                el.className = 'card-item';
                
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
                
                el.innerHTML = `
                    <div class="card-header">
                        <div class="card-title">${card.card_type}</div>
                        <div class="card-status ${statusClass}">${statusText}</div>
                    </div>
                    <div class="card-meaning">${card.farmer_meaning || ''}</div>
                    <div class="card-inspection">${card.suggested_inspection || ''}</div>
                    <div class="card-evidence">
                        <div style="font-size: 0.75rem; color: var(--text-muted); font-weight: 600;">EVIDENCE CHAIN</div>
                        ${evidenceHtml}
                    </div>
                `;
                cardsContainer.appendChild(el);
            });
            
        } catch (err) {
            console.error('Error fetching cards', err);
        }
    }

    // Fetch Observations
    async function fetchObservations() {
        try {
            const res = await fetch('/api/observations');
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
            const res = await fetch('/api/graph');
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
