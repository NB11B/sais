document.addEventListener('DOMContentLoaded', async () => {
    const map = L.map('map').setView([39.8283, -98.5795], 4);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom: 19,
        attribution: '&copy; OpenStreetMap'
    }).addTo(map);

    const layerToggles = document.getElementById('layer-toggles');
    const layers = {}; // Store references to Leaflet layers by category
    
    // Group categories
    const categories = {
        "Farm": { color: "#10b981", weight: 3, opacity: 0.1 },
        "Field": { color: "#3b82f6", weight: 2, opacity: 0.1 },
        "ManagementZone": { color: "#06b6d4", weight: 1, opacity: 0.2 },
        "Paddock": { color: "#f59e0b", weight: 1, opacity: 0.2 },
        "SensorNode": { color: "#ef4444" }, // markers
        "WaterAsset": { color: "#0ea5e9" } // sky blue markers
    };

    // Initialize layer groups
    Object.keys(categories).forEach(cat => {
        layers[cat] = new L.featureGroup();
        
        // Build UI Toggle
        const wrapper = document.createElement('div');
        wrapper.style.display = 'flex';
        wrapper.style.alignItems = 'center';
        wrapper.style.gap = '10px';
        wrapper.style.marginBottom = '12px';
        
        const checkbox = document.createElement('input');
        checkbox.type = 'checkbox';
        checkbox.checked = true; // default on
        checkbox.dataset.category = cat;
        
        const label = document.createElement('label');
        label.innerText = cat;
        label.style.flex = "1";
        
        const badge = document.createElement('div');
        badge.style.width = '12px';
        badge.style.height = '12px';
        badge.style.background = categories[cat].color;
        badge.style.borderRadius = '50%';
        
        wrapper.appendChild(checkbox);
        wrapper.appendChild(badge);
        wrapper.appendChild(label);
        layerToggles.appendChild(wrapper);

        // Toggle Event Listener
        checkbox.addEventListener('change', (e) => {
            if (e.target.checked) {
                map.addLayer(layers[cat]);
            } else {
                map.removeLayer(layers[cat]);
            }
        });
    });

    try {
        const res = await fetch('/api/graph');
        const data = await res.json();
        let boundaries = [];

        data.nodes.forEach(node => {
            // Find the category this node belongs to
            let category = Object.keys(categories).find(c => node.labels.includes(c));
            
            if (category && node.payload && node.payload.boundary_geojson) {
                const geojson = node.payload.boundary_geojson;
                boundaries.push(geojson);
                
                const lLayer = L.geoJSON(geojson, {
                    style: {
                        color: categories[category].color,
                        weight: categories[category].weight,
                        fillOpacity: categories[category].opacity
                    }
                }).bindPopup(`<b>${node.name}</b><br>${node.labels.join(', ')}`);
                
                layers[category].addLayer(lLayer);
            }
            
            // Render Sensor Nodes as Markers if they have a location
            if (category === "SensorNode" && node.payload && node.payload.location) {
                const loc = node.payload.location; // assumed {lat, lng}
                if (loc.lat && loc.lng) {
                    const marker = L.circleMarker([loc.lat, loc.lng], {
                        color: categories.SensorNode.color,
                        radius: 6,
                        fillOpacity: 1
                    }).bindPopup(`<b>Sensor: ${node.name}</b><br>Type: ${node.payload.node_type}`);
                    layers.SensorNode.addLayer(marker);
                }
            }

            // Render Water Assets as Markers
            if (category === "WaterAsset" && node.payload && node.payload.location) {
                const loc = node.payload.location;
                if (loc.lat && loc.lng) {
                    const icon = node.payload.asset_type === 'tank' ? '🛢️' : '🚰';
                    const marker = L.marker([loc.lat, loc.lng], {
                        icon: L.divIcon({
                            html: `<div style="font-size: 20px;">${icon}</div>`,
                            className: 'water-icon',
                            iconSize: [20, 20]
                        })
                    }).bindPopup(`<b>${node.name}</b><br>Type: ${node.payload.asset_type}`);
                    layers.WaterAsset.addLayer(marker);
                }
            }
        });

        // Add all layer groups to map initially
        Object.keys(layers).forEach(cat => map.addLayer(layers[cat]));

        // --- NEW: Load Auxiliary GIS Assets ---
        const gisRes = await fetch('/api/gis/assets');
        const gisData = await gisRes.json();
        
        for (const asset of gisData.assets) {
            const assetLayer = new L.featureGroup();
            
            // UI Toggle
            const wrapper = document.createElement('div');
            wrapper.className = 'layer-item'; // Use existing panel style
            wrapper.style.display = 'flex';
            wrapper.style.alignItems = 'center';
            wrapper.style.gap = '10px';
            
            const checkbox = document.createElement('input');
            checkbox.type = 'checkbox';
            checkbox.checked = true;
            
            const label = document.createElement('label');
            label.innerHTML = `<div class="layer-type">${asset.name}</div><div class="layer-path">${asset.description || ''}</div>`;
            label.style.flex = "1";
            
            const badge = document.createElement('div');
            badge.style.width = '12px';
            badge.style.height = '12px';
            badge.style.background = asset.style.color;
            badge.style.borderRadius = '2px'; // Square for assets
            
            wrapper.appendChild(checkbox);
            wrapper.appendChild(badge);
            wrapper.appendChild(label);
            layerToggles.appendChild(wrapper);
            
            // Fetch and render data
            try {
                const dataRes = await fetch(`/api/gis/data/${asset.id}`);
                const geojson = await dataRes.json();
                
                L.geoJSON(geojson, {
                    style: {
                        color: asset.style.color,
                        weight: asset.style.weight || 2,
                        dashArray: asset.style.dashArray || null,
                        fillOpacity: 0.1
                    }
                }).bindPopup(`<b>${asset.name}</b>`).addTo(assetLayer);
                
                map.addLayer(assetLayer);
            } catch (e) {
                console.error(`Failed to load GIS data for ${asset.id}`, e);
            }
            
            checkbox.addEventListener('change', (e) => {
                if (e.target.checked) map.addLayer(assetLayer);
                else map.removeLayer(assetLayer);
            });
        }

        if (boundaries.length > 0) {
            const group = new L.featureGroup();
            Object.keys(layers).forEach(cat => {
                layers[cat].eachLayer(l => group.addLayer(l));
            });
            if (group.getLayers().length > 0) {
                map.fitBounds(group.getBounds(), { padding: [50, 50] });
            }
        }

    } catch (err) {
        console.error("Failed to load map layers", err);
    }
});
