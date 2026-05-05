let map;
let farmId = "local"; // Default from setup
let paddockToFieldMap = {}; // Dynamic map for grazing resolution

document.addEventListener('DOMContentLoaded', async () => {
    map = L.map('admin-map').setView([39.8283, -98.5795], 4);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom: 19,
        attribution: '&copy; OpenStreetMap'
    }).addTo(map);

    await loadMapData();
    setupForms();
    loadPendingNodes();
    setupProvisionForm();
    loadRoleTemplates();

    const tokenInput = document.getElementById('admin_token_input');
    if (tokenInput) {
        tokenInput.value = getAdminToken();
    }
});

async function loadRoleTemplates() {
    try {
        const res = await fetch('/api/nodes/roles', {
            headers: { 'Authorization': `Bearer ${getAdminToken()}` }
        });
        if (res.status === 401) {
            const token = prompt("Admin Token required:");
            if (token) {
                setAdminToken(token);
                return loadRoleTemplates();
            }
        }
        const data = await res.json();
        const select = document.getElementById('prov-role');
        if (select) {
            select.innerHTML = '';
            Object.keys(data.roles).forEach(key => {
                const role = data.roles[key];
                const opt = document.createElement('option');
                opt.value = key;
                opt.textContent = role.name;
                select.appendChild(opt);
            });
        }
    } catch (e) { console.error("Failed to load role templates", e); }
}

function getAdminToken() {
    return sessionStorage.getItem('sais_admin_token') || '';
}

function setAdminToken(token) {
    sessionStorage.setItem('sais_admin_token', token);
}

window.saveTokenFromInput = () => {
    const input = document.getElementById('admin_token_input');
    if (input) {
        setAdminToken(input.value);
        alert("Token saved to session.");
        location.reload(); // Refresh to apply to all fetches
    }
};

async function loadPendingNodes() {
    try {
        const res = await fetch('/api/nodes/pending', {
            headers: { 'Authorization': `Bearer ${getAdminToken()}` }
        });
        if (res.status === 401) {
            const token = prompt("Admin Token required:");
            if (token) {
                setAdminToken(token);
                return loadPendingNodes();
            }
        }
        const data = await res.json();
        const body = document.getElementById('pending-nodes-body');
        body.innerHTML = '';
        
        data.nodes.forEach(node => {
            const row = document.createElement('tr');
            
            // WP25.1: XSS Remediation - TextContent only
            const tdId = document.createElement('td');
            const bId = document.createElement('b');
            bId.textContent = node.id;
            tdId.appendChild(bId);
            row.appendChild(tdId);
            
            const tdStatus = document.createElement('td');
            const spanStatus = document.createElement('span');
            spanStatus.className = 'badge badge-status-pending';
            spanStatus.textContent = 'DISCOVERED';
            tdStatus.appendChild(spanStatus);
            row.appendChild(tdStatus);
            
            const tdSignal = document.createElement('td');
            const rssi = node.payload?.rssi_dbm || node.payload?.rssi || 'N/A';
            const batt = node.payload?.battery_mv || node.payload?.battery || 'N/A';
            
            const spanRssi = document.createElement('span');
            spanRssi.className = 'badge badge-rssi';
            spanRssi.textContent = `${rssi} dBm`;
            tdSignal.appendChild(spanRssi);
            
            const spanBatt = document.createElement('span');
            spanBatt.className = 'badge badge-battery';
            spanBatt.textContent = `${batt} mV`;
            tdSignal.appendChild(spanBatt);
            row.appendChild(tdSignal);
            
            const tdActions = document.createElement('td');
            const btnProv = document.createElement('button');
            btnProv.className = 'btn btn-small';
            btnProv.textContent = 'Provision';
            btnProv.onclick = () => openProvisionModal(node.id);
            tdActions.appendChild(btnProv);
            
            const btnReject = document.createElement('button');
            btnReject.className = 'btn btn-small';
            btnReject.style.background = '#ef4444';
            btnReject.textContent = 'Reject';
            btnReject.onclick = () => rejectNode(node.id);
            tdActions.appendChild(btnReject);
            
            row.appendChild(tdActions);
            body.appendChild(row);
        });
    } catch (e) { console.error("Failed to load pending nodes", e); }
}

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
        return data;
    } catch (e) { console.error("Failed to load cards", e); }
}

function openProvisionModal(nodeId) {
    document.getElementById('modal-node-id').textContent = `Provision Node: ${nodeId}`;
    document.getElementById('prov-node-id').value = nodeId;
    document.getElementById('provision-modal').style.display = 'block';
}

function closeModal() {
    document.getElementById('provision-modal').style.display = 'none';
}

function setupProvisionForm() {
    document.getElementById('provision-form').onsubmit = async (e) => {
        e.preventDefault();
        const nodeId = document.getElementById('prov-node-id').value;
        const payload = {
            role: document.getElementById('prov-role').value,
            paddock_id: document.getElementById('prov-target').value,
            farm_id: farmId,
            location: {
                lat: parseFloat(document.getElementById('prov-lat').value),
                lng: parseFloat(document.getElementById('prov-lng').value)
            }
        };
        
        // 1. Accept
        await fetch(`/api/nodes/${nodeId}/accept`, { 
            method: 'POST',
            headers: { 'Authorization': `Bearer ${getAdminToken()}` }
        });
        // 2. Assign
        await submitApi(`/api/nodes/${nodeId}/assignment`, 'PUT', payload);
        
        closeModal();
        loadPendingNodes();
    };
}

async function rejectNode(nodeId) {
    if (confirm(`Reject node ${nodeId}? Data will be blocked.`)) {
        await fetch(`/api/nodes/${nodeId}/reject`, { 
            method: 'POST',
            headers: { 'Authorization': `Bearer ${getAdminToken()}` }
        });
        loadPendingNodes();
    }
}

async function loadMapData() {
    try {
        const res = await fetch('/api/graph', {
            headers: { 'Authorization': `Bearer ${getAdminToken()}` }
        });
        if (res.status === 401) {
            const token = prompt("Admin Token required:");
            if (token) {
                setAdminToken(token);
                return loadMapData();
            }
        }
        const data = await res.json();
        
        // Clear old layers
        map.eachLayer((layer) => {
            if (layer.feature) {
                map.removeLayer(layer);
            }
        });
        
        let boundaries = [];
        data.nodes.forEach(node => {
            if (node.payload && node.payload.boundary_geojson) {
                const geojson = node.payload.boundary_geojson;
                boundaries.push(geojson);
                
                let color = "#3b82f6"; // Default blue
                if (node.labels.includes("Farm")) color = "#10b981"; // Green
                if (node.labels.includes("ManagementZone")) color = "#06b6d4"; // Cyan
                if (node.labels.includes("Paddock")) color = "#f59e0b"; // Amber
                
                L.geoJSON(geojson, {
                    style: { color: color, weight: 2, fillOpacity: 0.1 }
                }).bindPopup(`<b>${node.name}</b><br>${node.labels.join(', ')}`).addTo(map);
            }
        });
        
        if (boundaries.length > 0) {
            const group = new L.featureGroup();
            map.eachLayer((layer) => {
                if (layer.feature) { group.addLayer(layer); }
            });
            map.fitBounds(group.getBounds(), { padding: [50, 50] });
        }

        // Water Asset Form
        const waterAssetForm = document.getElementById('water-asset-form');
        if (waterAssetForm) {
            waterAssetForm.onsubmit = async (e) => {
                e.preventDefault();
                const payload = {
                    id: document.getElementById('wa_id').value,
                    farm_id: farmId,
                    asset_type: document.getElementById('wa_type').value,
                    name: document.getElementById('wa_name').value,
                    location: {
                        lat: parseFloat(document.getElementById('wa_lat').value),
                        lng: parseFloat(document.getElementById('wa_lng').value)
                    }
                };
                await submitApi('/api/infrastructure/water', 'POST', payload);
                waterAssetForm.reset();
            };
        }

        // Populate Paddock Dropdown for Grazing Form
        const paddockSelect = document.getElementById('grazing_paddock_id');
        if (paddockSelect) {
            paddockSelect.innerHTML = '<option value="">Select Paddock...</option>';
            paddockToFieldMap = {}; // Reset
            data.nodes.filter(n => n.labels.includes("Paddock")).forEach(p => {
                const opt = document.createElement('option');
                opt.value = p.id;
                opt.textContent = p.name || p.id;
                paddockSelect.appendChild(opt);
                
                // Track parent field (via edges)
                const edge = data.edges.find(e => e.target === p.id && e.type === "CONTAINS");
                if (edge) {
                    paddockToFieldMap[p.id] = edge.source;
                }
            });
        }

        // Set default start time
        const startInput = document.getElementById('grazing_start');
        if (startInput && !startInput.value) {
            startInput.value = new Date().toISOString();
        }

    } catch (e) {
        console.error("Failed to load map data", e);
    }
}

function parseGeoJSON(val) {
    if (!val || val.trim() === "") return null;
    try {
        return JSON.parse(val);
    } catch (e) {
        alert("Invalid GeoJSON formatting.");
        throw e;
    }
}

function setupForms() {
    document.getElementById('farm-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        farmId = document.getElementById('farm_id').value;
        const payload = {
            id: farmId,
            name: document.getElementById('farm_name').value,
            boundary_geojson: parseGeoJSON(document.getElementById('farm_geojson').value)
        };
        await submitApi('/api/farm/profile', 'PUT', payload);
    });

    document.getElementById('field-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        const payload = {
            id: document.getElementById('field_id').value,
            farm_id: farmId,
            name: document.getElementById('field_name').value,
            boundary_geojson: parseGeoJSON(document.getElementById('field_geojson').value)
        };
        await submitApi('/api/farm/fields', 'POST', payload);
    });

    document.getElementById('zone-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        const payload = {
            id: document.getElementById('zone_id').value,
            field_id: document.getElementById('zone_field_id').value,
            name: document.getElementById('zone_name').value,
            boundary_geojson: parseGeoJSON(document.getElementById('zone_geojson').value)
        };
        await submitApi('/api/farm/zones', 'POST', payload);
    });

    document.getElementById('paddock-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        const payload = {
            id: document.getElementById('paddock_id').value,
            field_id: document.getElementById('paddock_field_id').value,
            name: document.getElementById('paddock_name').value,
            boundary_geojson: parseGeoJSON(document.getElementById('paddock_geojson').value),
            rest_target_days: parseInt(document.getElementById('paddock_rest').value) || null
        };
        await submitApi('/api/farm/paddocks', 'POST', payload);
    });

    document.getElementById('water-asset-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        const payload = {
            id: document.getElementById('wa_id').value,
            farm_id: farmId,
            asset_type: document.getElementById('wa_type').value,
            name: document.getElementById('wa_name').value,
            location: {
                lat: parseFloat(document.getElementById('wa_lat').value),
                lng: parseFloat(document.getElementById('wa_lng').value)
            }
        };
        await submitApi('/api/infrastructure/water', 'POST', payload);
        e.target.reset();
    });

    document.getElementById('infra-reg-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        const payload = {
            id: document.getElementById('reg_inf_id').value,
            farm_id: farmId,
            asset_type: document.getElementById('reg_inf_type').value,
            status: "unknown",
            location_geojson: parseGeoJSON(document.getElementById('reg_inf_geojson').value)
        };
        await submitApi('/api/infrastructure/asset', 'POST', payload);
    });

    document.getElementById('sensor-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        const target_id = document.getElementById('sensor_target_id').value;
        let loc = null;
        const lat = document.getElementById('sensor_lat').value;
        const lng = document.getElementById('sensor_lng').value;
        if (lat && lng) {
            loc = { lat: parseFloat(lat), lng: parseFloat(lng) };
        }
        const payload = {
            id: document.getElementById('sensor_id').value,
            farm_id: farmId,
            node_type: document.getElementById('sensor_type').value,
            zone_id: target_id.startsWith('zone-') ? target_id : null,
            field_id: target_id.startsWith('field-') ? target_id : null,
            location: loc
        };
        await submitApi('/api/farm/sensor-nodes', 'POST', payload);
    });

    document.getElementById('grazing-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        const paddockId = document.getElementById('grazing_paddock_id').value;
        const payload = {
            schema: "sais.grazing_event.v1",
            event_id: `graze-${paddockId}-${Date.now()}`,
            farm_id: farmId,
            field_id: paddockToFieldMap[paddockId] || "field-a", // Dynamic lookup
            paddock_id: paddockId,
            started_at: document.getElementById('grazing_start').value,
            animal_count: parseInt(document.getElementById('grazing_count').value),
            notes: document.getElementById('grazing_notes').value
        };
        await submitApi('/api/grazing/events', 'POST', payload);
    });
}

async function submitApi(url, method, payload) {
    try {
        const res = await fetch(url, {
            method: method,
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${getAdminToken()}`
            },
            body: JSON.stringify(payload)
        });
        if (res.status === 401) {
            const token = prompt("Admin Token required:");
            if (token) {
                setAdminToken(token);
                return submitApi(url, method, payload);
            }
        }
        if (!res.ok) {
            const txt = await res.text();
            alert("Error: " + txt);
            return;
        }
        alert("Success!");
        loadMapData();
    } catch (e) {
        alert("Network error.");
    }
}
