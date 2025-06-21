document.addEventListener("DOMContentLoaded", function () {
    // Obtem bbox da URL
    const params = new URLSearchParams(window.location.search);
    const bboxStr = params.get('bbox');
    const bbox = bboxStr.split(',').map(parseFloat);
    const bounds = [[bbox[1], bbox[0]], [bbox[3], bbox[2]]];

    // Inicializa o mapa centrado no bbox
    const map = L.map('map').fitBounds(bounds);

    // Camada RGB (World Imagery da Esri)
    const rgbLayer = L.tileLayer(
        'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}');

    rgbLayer.addTo(map);  // Adiciona a camada RGB

    // Carrega o GeoJSON da segmentação
    fetch('/resultado_geojson')
        .then(res => res.json())
        .then(data => {
            L.geoJSON(data, {
                style: {
                    color: 'yellow',
                    weight: 1,
                    fillOpacity: 0.1
                }
            }).addTo(map);
        })
        .catch(err => console.error("Erro ao carregar GeoJSON:", err));
});