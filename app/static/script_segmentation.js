document.addEventListener("DOMContentLoaded", function () {
    // Initialize map
    var map = L.map('map').setView([-20.7664, -42.8696], 13);

    // Spectral band layers
    var bandLayers = {
        // Using arcGIS to RGB
        rgb: L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}'),
    };

    // Add default layer (RGB)
    bandLayers.rgb.addTo(map);

    // Change layer when user selects a band
    document.getElementById('band-options').addEventListener('change', function (e) {
        Object.values(bandLayers).forEach(layer => layer.remove());
        bandLayers[e.target.value].addTo(map);
    });

    // Configure search control 
    var searchControl = L.esri.Geocoding.geosearch({
        position: 'topright',
        placeholder: 'Search for places or addresses',
        useMapBounds: false
    }).addTo(map);

    // Create a layer group for search results
    var results = L.layerGroup().addTo(map);

    // Handle search results
    searchControl.on('results', function (data) {
        results.clearLayers();

        if (data.results.length === 0) {
            // Show message when no results found
            L.popup()
                .setLatLng(map.getCenter())
                .setContent('<p>No results found. Try a different search.</p>')
                .openOn(map);
            return;
        }

        // Process all results
        data.results.forEach(function (result) {
            var marker = L.marker(result.latlng, {
                //icon: customIcon,
                title: result.text
            }).addTo(results);

            // Add popup with more information
            marker.bindPopup(`
                <b>${result.text}</b><br>
            `);

            // Zoom to the first result with some padding
            if (result === data.results[0]) {
                map.setView(result.latlng, 20, {
                    animate: true,
                    duration: 1
                });
            }
        });
    });

    // Handle errors
    searchControl.on('error', function (e) {
        console.error('Geocoding error:', e.error);
        L.popup()
            .setLatLng(map.getCenter())
            .setContent('<p>Search service unavailable. Please try again later.</p>')
            .openOn(map);
    });


    // Grupo onde os desenhos serão adicionados
    var drawnItems = new L.FeatureGroup();
    map.addLayer(drawnItems);

    // Controle de desenho
    var drawControl = new L.Control.Draw({
        draw: {
            polyline: false,
            polygon: false,
            circle: false,
            marker: false,
            circlemarker: false,
            rectangle: true // habilita apenas o retângulo
        },
        edit: {
            featureGroup: drawnItems, // grupo a ser editado
            edit: true,
            remove: true
        }
    });
    map.addControl(drawControl);

    // Permitir apenas uma seleção por vez
    map.on('draw:created', function (e) {
        // Limpa qualquer seleção anterior
        drawnItems.clearLayers();

        // Adiciona a nova seleção
        var layer = e.layer;
        drawnItems.addLayer(layer);

        var bounds = layer.getBounds();
        console.log("Área selecionada:", bounds);
    });


    document.getElementById('btnSegmentar').addEventListener('click', () => {
    if (drawnItems.getLayers().length === 0) {
        alert("Por favor, selecione uma área antes de segmentar.");
        return;
    }

    const layer = drawnItems.getLayers()[0];
    const bounds = layer.getBounds();
    const bbox = [
        bounds.getWest(),
        bounds.getSouth(),
        bounds.getEast(),
        bounds.getNorth()
    ];

    // Salva no backend e depois redireciona
    fetch('/segmentar', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ bbox: bbox })
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'sucesso') {
            // Redireciona para a nova página passando o bbox como parâmetro
            const query = `?bbox=${bbox.join(',')}`;
            window.location.href = '/resultado' + query;
        } else {
            alert("Erro na segmentação: " + data.mensagem);
        }
    })
    .catch(error => {
        console.error("Erro na requisição:", error);
    });
});


});