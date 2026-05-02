let map;
let farmId = "local"; // Default from setup

document.addEventListener('DOMContentLoaded', async () => {
    map = L.map('admin-map').setView([39.8283, -98.5795], 4);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom: 19,
        attribution: '&copy; OpenStreetMap'
    }).addTo(map);

    await loadMapData();
    setupForms();
});

async function loadMapData() {
    try {
        const res = await fetch('/api/graph');
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

        // Populate Paddock Dropdown for Grazing Form
        const paddockSelect = document.getElementById('grazing_paddock_id');
        if (paddockSelect) {
            paddockSelect.innerHTML = '<option value="">Select Paddock...</option>';
            data.nodes.filter(n => n.labels.includes("Paddock")).forEach(p => {
                const opt = document.createElement('option');
                opt.value = p.id;
                opt.textContent = p.name || p.id;
                paddockSelect.appendChild(opt);
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
            field_id: "field-a", // Simplified for now
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
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(payload)
        });
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
