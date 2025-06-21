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
from skimage.segmentation import slic, mark_boundaries
from skimage.util import img_as_float

# === CONFIGURAÇÕES GERAIS ===
BANDAS_TODAS = ['B01', 'B02', 'B03', 'B04', 'B05', 'B06',
                'B07', 'B08', 'B8A', 'B09', 'B11', 'B12']
BANDAS_RGB = ['B04', 'B03', 'B02']  # Ordem correta para RGB Sentinel-2
OUTPUT_DIR = './SENTINEL2_BANDAS'


# === BAIXAR BANDAS ===
def baixar_bandas_sentinel(output_dir=OUTPUT_DIR, dias=60, resolucao=30):
    config = SHConfig()
    config.sh_client_id = 'b38dba7b-11a9-43b1-8e86-688ba3ac619a'
    config.sh_client_secret = 'Z0h1jEGidbmLvvDbrLu1HctBmDKrNa8o'

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


# === CRIAR MULTIBANDA ===
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


# === CRIAR COMPOSIÇÃO RGB 8 BITS PARA VISUALIZAÇÃO ===
def criar_rgb_8bit(bandas_rgb, output_dir, output_path):
    arrays = []
    for banda in bandas_rgb:
        path = os.path.join(output_dir, f'{banda}.tif')
        with rasterio.open(path) as src:
            data = src.read(1).astype(np.float32)
            # Normaliza entre 0-1 para 8bit
            data_norm = (data - data.min()) / (data.max() - data.min())
            arrays.append(data_norm)
            if 'profile' not in locals():
                profile = src.profile
                profile.update({
                    'count': len(bandas_rgb),
                    'dtype': 'uint8',
                    'compress': 'lzw'
                })

    stack = np.stack(arrays)
    stack_8bit = (stack * 255).astype(np.uint8)

    with rasterio.open(output_path, 'w', **profile) as dst:
        dst.write(stack_8bit)

    print(f"📸 RGB 8 bits salvo em: {output_path}")


# === SEGMENTAÇÃO COM SLIC (skimage) ===
def aplicar_segmentacao_multibanda(image_path, output_dir, compactness=5, step=200, output_filename='segments_slic.tif'):
    output_path = os.path.join(output_dir, output_filename)

    with rasterio.open(image_path) as src:
        img = src.read().astype(np.float32)
        profile = src.profile

    # Transpor para (altura, largura, canais)
    img = np.moveaxis(img, 0, -1)
    img = img_as_float(img)

    # Define número de segmentos como área / step (step aqui é uma área média aproximada)
    n_segments = max(100, int(img.shape[0] * img.shape[1] / step))

    segments = slic(
        img,
        n_segments=n_segments,
        compactness=compactness,
        start_label=1
    )

    # Atualiza perfil para salvar segmento (1 banda, uint16)
    profile.update(
        dtype=rasterio.uint16,
        count=1,
        compress='lzw'
    )

    with rasterio.open(output_path, 'w', **profile) as dst:
        dst.write(segments.astype(rasterio.uint16), 1)

    print(f"✅ Segmentação salva em: {output_path}")

    # Visualização
    rgb_path = os.path.join(output_dir, 'RGB_composicao_8bit.tif')
    if os.path.exists(rgb_path):
        with rasterio.open(rgb_path) as rgb:
            rgb_data = rgb.read().astype(np.uint8)
            rgb_vis = np.moveaxis(rgb_data, 0, -1) / 255.0

        plt.figure(figsize=(10, 10))
        plt.imshow(mark_boundaries(rgb_vis, segments))
        plt.title(f"SLIC (compactness={compactness}, step={step})")
        plt.axis('off')
        plt.show()


# === EXECUÇÃO COMPLETA ===
def processar_segmentacao_completa(output_dir=OUTPUT_DIR):
    print(baixar_bandas_sentinel(output_dir))
    path_multibanda = os.path.join(output_dir, 'sentinel_multibanda.tif')
    criar_multibanda(BANDAS_RGB, output_dir, path_multibanda)

    path_rgb_8bit = os.path.join(output_dir, 'RGB_composicao_8bit.tif')
    criar_rgb_8bit(BANDAS_RGB, output_dir, path_rgb_8bit)

    aplicar_segmentacao_multibanda(
        image_path=path_multibanda,
        output_dir=output_dir,
        compactness=5,
        step=200,
        output_filename='segments_slic_compactness05_step200.tif'
    )

    return "✅ Segmentação finalizada com sucesso."


# Para rodar tudo:
if __name__ == '__main__':
    print(processar_segmentacao_completa())
