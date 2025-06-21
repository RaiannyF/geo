document.addEventListener("DOMContentLoaded", async function () {
    // Obtem bbox da URL
    const params = new URLSearchParams(window.location.search);
    const bboxStr = params.get('bbox');
    const bbox = bboxStr.split(',').map(parseFloat);
    const bounds = [[bbox[1], bbox[0]], [bbox[3], bbox[2]]];

    // Inicializa o mapa
    const map = L.map('map').fitBounds(bounds);

    let layerAtual = null;

    async function carregarBanda(valor) {
        try {
            // Remove camada atual, se houver
            if (layerAtual) {
                map.removeLayer(layerAtual);
                layerAtual = null;
            }

            if (valor === "original") {
                // Camada RGB padrão do ArcGIS
                layerAtual = L.tileLayer(
                    'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}'
                ).addTo(map);

            } else {
                // TIFF local via georaster
                const response = await fetch('/bandas/' + valor);
                const arrayBuffer = await response.arrayBuffer();
                const georaster = await parseGeoraster(arrayBuffer);

                layerAtual = new GeoRasterLayer({
                    georaster,
                    opacity: 1,
                    resolution: 256
                }).addTo(map);

                map.fitBounds(layerAtual.getBounds());
            }
        } catch (error) {
            console.error("Erro ao carregar a banda:", error);
        }
    }

    // Carrega a banda inicial (RGB)
    await carregarBanda(document.getElementById("band-options").value);

    // Atualiza a banda ao mudar a opção no <select>
    document.getElementById("band-options").addEventListener("change", function (e) {
        carregarBanda(e.target.value);
    });

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
