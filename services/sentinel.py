import os
from datetime import datetime, timedelta
import numpy as np
import matplotlib.pyplot as plt
import rasterio
from rasterio.transform import from_origin
from sentinelhub import (
    SHConfig, BBox, CRS, SentinelHubRequest,
    DataCollection, MimeType, bbox_to_dimensions
) 

from samgeo import SamGeo
from skimage.segmentation import mark_boundaries


# === CONFIGURAÇÕES GERAIS ===
BANDAS_TODAS = ['B01', 'B02', 'B03', 'B04', 'B05', 'B06',
                'B07', 'B08', 'B8A', 'B09', 'B11', 'B12']
BANDAS_RGB = ['B02', 'B03', 'B04', 'B08']


# === BAIXAR BANDAS ===
def baixar_bandas_sentinel(output_dir='./SENTINEL2_BANDAS', dias=60, resolucao=30):
    config = SHConfig()
    config.sh_client_id = 'ea50939b-7284-4abe-bb28-5c0cb65225a9'
    config.sh_client_secret = 'KdHe961bmkLWfRbpD3wtZ51o6bSeiZCh'

    hoje = datetime.utcnow().date()
    aoi = BBox(bbox=[-44.0, -21.5, -43.4, -20.9], crs=CRS.WGS84)
    width, height = bbox_to_dimensions(aoi, resolution=resolucao)

    os.makedirs(output_dir, exist_ok=True)

    for banda in BANDAS_TODAS:
        request = SentinelHubRequest(
            evalscript=f"""
            //VERSION=3
            function setup() {{
                return {{
                    input: ["{banda}"],
                    output: {{
                        bands: 1,
                        sampleType: "UINT16"
                    }}
                }};
            }}
            function evaluatePixel(sample) {{
                return [sample.{banda} * 10000];
            }}
            """,
            input_data=[{
                'type': DataCollection.SENTINEL2_L1C.api_id,
                'dataFilter': {
                    'timeRange': {
                        'from': f'{hoje - timedelta(days=dias)}T00:00:00Z',
                        'to': f'{hoje}T23:59:59Z'
                    },
                    'mosaickingOrder': 'leastCC',
                    'maxCloudCoverage': 30
                }
            }],
            responses=[{
                'identifier': 'default',
                'format': {'type': MimeType.TIFF.get_string()}
            }],
            bbox=aoi,
            size=(width, height),
            config=config
        )

        image = request.get_data(save_data=False)[0]
        if image.ndim == 2:
            image = np.expand_dims(image, axis=0)

        _, h, w = image.shape
        transform = from_origin(aoi.lower_left[0], aoi.upper_right[1], resolucao, resolucao)
        path_out = os.path.join(output_dir, f'{banda}.tif')

        with rasterio.open(
            path_out, 'w',
            driver='GTiff',
            height=h,
            width=w,
            count=1,
            dtype='uint16',
            crs=aoi.crs.pyproj_crs(),
            transform=transform
        ) as dst:
            dst.write(image[0], 1)

    return f"✅ Todas as bandas foram salvas em: {output_dir}"


# === MULTIBANDA ===
def criar_multibanda(bandas, output_dir, output_path):
    arrays = []
    for banda in bandas:
        path = os.path.join(output_dir, f'{banda}.tif')
        with rasterio.open(path) as src:
            data = src.read(1).astype(np.float32)
            arrays.append(data)
            if 'profile' not in locals():
                profile = src.profile
                profile.update({
                    'count': len(bandas),
                    'dtype': 'float32',
                    'compress': 'lzw'
                })

    stack = np.stack(arrays)
    with rasterio.open(output_path, 'w', **profile) as dst:
        dst.write(stack)

    print(f"📦 Raster multibanda salvo em: {output_path}")


# === SEGMENTAÇÃO ===
def aplicar_segmentacao_multibanda(image_path, output_dir, compactness=5, min_area=8, step=15, output_filename='segments_slic.tif'):
    output_path = os.path.join(output_dir, output_filename)

    segments = slic(
        image_path=image_path,
        compactness=compactness,
        min_area=min_area,
        step=step,
        output=output_path
    )

    print(f"✅ Segmentação salva em: {output_path}")

    # Visualização (se houver imagem RGB gerada anteriormente)
    rgb_path = os.path.join(output_dir, 'RGB_composicao_8bit.tif')
    if os.path.exists(rgb_path):
        with rasterio.open(rgb_path) as rgb:
            rgb_data = rgb.read().astype(np.uint8)
            rgb_vis = np.moveaxis(rgb_data, 0, -1) / 255.0

        with rasterio.open(output_path) as seg_src:
            segments = seg_src.read(1)

        plt.figure(figsize=(10, 10))
        plt.imshow(mark_boundaries(rgb_vis, segments))
        plt.title(f"SLIC (compactness={compactness}, min_area={min_area}, step={step})")
        plt.axis('off')
        plt.show()


# === EXECUÇÃO COMPLETA ===
def processar_segmentacao_completa(output_dir='./SENTINEL2_BANDAS'):
    # Passo 1: Baixar bandas
    baixar_bandas_sentinel(output_dir)

    # Passo 2: Criar multibanda
    path_multibanda = os.path.join(output_dir, 'sentinel_multibanda.tif')
    criar_multibanda(BANDAS_RGB, output_dir, path_multibanda)

    # Passo 3: Segmentar
    aplicar_segmentacao_multibanda(
        image_path=path_multibanda,
        output_dir=output_dir,
        compactness=5,
        min_area=8,
        step=15,
        output_filename='segments_slic_compac05_area08_step15.tif'
    )

    return "✅ Segmentação finalizada com sucesso."
