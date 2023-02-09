import os
import json
import trimesh
import dataclasses
from trimesh.visual import texture, TextureVisuals
import numpy as np
from PIL import Image, ImageDraw, ImageFont

@dataclasses.dataclass
class AnnotationFaces:
    vertices: list
    normals: list
    faces: list

@dataclasses.dataclass
class TextureAtlas:
    image: Image
    textures: list

@dataclasses.dataclass
class TextureInfo:
    global_id: str
    text: str
    topx: int
    topy: int
    width: int
    height: int

def create_annotation_texture_atlas(
    annotations: list,
    texture_atlas_size_pixel: int,
    font: ImageFont) -> TextureAtlas:
    """
    annotation配列をもとにテクスチャアトラス情報を生成
    """
    img = Image.new(
        "RGB", 
        (texture_atlas_size_pixel, texture_atlas_size_pixel),
        (255, 255, 255))

    all_textures = []
    ix = 0
    iy = 0
    maxHeight = 0
    draw = ImageDraw.Draw(img)
    # 注記テキストを1枚のテクスチャアトラス画像の中に詰め込む。
    # ※引数で指定されたサイズの画像の左上から単純に画像を敷き詰めて行っているだけの雑な実装です。
    # ちゃんとした実相を参考にしたい人は「TextureAtlas 長方形詰込み」などで検索して調べてみてください。
    for annotation in annotations:
        gid = annotation["GlobalId"]
        text = annotation["_text"]
        (w, h) = get_text_dimensions(text, font)
        if h > maxHeight:
            maxHeight = h
        if (ix + w > texture_atlas_size_pixel):
            ix = 0
            iy += maxHeight
            maxHeight = 0 
        tx = ix
        ty = iy
        ix += w
        t = TextureInfo(global_id=gid, text=text, topx = tx, topy = ty, width=w, height=h)
        all_textures.append(t)
        draw_text(draw, text, font, tx, ty)
    return TextureAtlas(
        image = img, 
        textures = all_textures)

def create_trimesh_texture_visuals(texture_atlas: TextureAtlas) -> TextureVisuals:
    """
    TextureAtlasからtrimeshのテクスチャ情報を生成
    """
    uvs = []
    for tx in texture_atlas.textures:
        texture_atlas_w = texture_atlas.image.width
        texture_atlas_h = texture_atlas.image.height
        topy = texture_atlas_h - tx.topy
        topx = tx.topx
        w = tx.width
        h = tx.height
        bottomy = topy - h
        rightx = topx + w
        img = texture_atlas.image
        uv_left = topx / texture_atlas_w
        uv_right = rightx / texture_atlas_w
        uv_bottom = bottomy / texture_atlas_h
        uv_top = topy / texture_atlas_h
        uvs.append([uv_left, uv_bottom])
        uvs.append([uv_right, uv_bottom])
        uvs.append([uv_right, uv_top])
        uvs.append([uv_left, uv_top])
    material = texture.SimpleMaterial(image=img)
    return TextureVisuals(uv=uvs, material=material)

def draw_text(draw, text: str, font, x: int, y: int):
    draw.text((x, y), text, fill=(0, 0, 0), font=font)

def get_text_dimensions(text_string, font):
    # https://stackoverflow.com/a/46220683/9263761
    ascent, descent = font.getmetrics()
    text_width = font.getmask(text_string).getbbox()[2]
    text_height = font.getmask(text_string).getbbox()[3] + descent
    return (text_width, text_height)

def calc_face_vertices(
    annotation: dict):
    """
    板ポリゴンの座標を生成。
    テキストが回転してもテクスチャ画像を回転しなくても良いように頂点座標を調整。
    ただし現状は回転角度0, 90, 180, 270のみ対応。
    """
    p = annotation["json_geometry"]["coordinates"]
    px = p[0]
    py = p[1]
    pz = p[2]
    rot = annotation["_rotation_ccw_degree"]
    minx = annotation["_minx"]
    miny = annotation["_miny"]
    minz = annotation["_minz"]
    maxx = annotation["_maxx"]
    maxy = annotation["_maxy"]
    maxz = annotation["_maxz"]

    if rot == 0:
        """
               (max)
        3----2 
        |   /|
        |  / |
        | /  |
        |/   |
        P----1
        (min)   
        """
        return [
            [minx, miny, pz], [maxx, miny, pz], [maxx, maxy, pz], [minx, maxy, pz]
        ]
    elif rot == 90:
        """
               (max)
        2----1 
        |\   |
        | \  |
        |  \ |
        |   \|
        3----P
        (min)   
        """
        return [
            [maxx, miny, pz], [maxx, maxy, pz], [minx, maxy, pz], [minx, miny, pz]
        ]
    elif rot == 180:
        """
               (max)
        1----P
        |   /|
        |  / |
        | /  |
        |/   |
        2----3
        (min)   
        """
        return [
            [maxx, maxy, pz], [minx, maxy, pz], [minx, miny, pz], [maxx, miny, pz]
        ]
    elif rot == 270:
        """
               (max)
        P----3
        |\   |
        | \  |
        |  \ |
        |   \|
        1----2
        (min)   
        """
        return [
            [minx, maxy, pz], [minx, miny, pz], [maxx, miny, pz], [maxx, maxy, pz]
        ]
    else:
        print("TODO")
        # 以下のようにすればp, 1, 2, 3の座標を計算できるはず。
        # p ... (px, py, pz)
        # 1 ... (1,0,0)ベクトルとmin, maxのバウンディングボックスとの交点
        # 3 ... (0,1,0) ベクトルとmin, maxのバウンディングボックスとの交点
        # 2 ... P1とP3の合成ベクトル
        return None

def append_annotation_face(
    annotation: dict,
    vertices: list,
    normals: list,
    faces: list):
    vs = calc_face_vertices(annotation)
    """
    vs[3]     vs[2]
       +------+
       |    / |
       |   /  |
       |  /   |
       | /    |
       +------+
    vs[0]     vs[1]
    0-2-3, 0-1-2のfaceを追加
    """
    idx0 = len(vertices)
    vertices.append(vs[0])
    vertices.append(vs[1])
    vertices.append(vs[2])
    vertices.append(vs[3])
    faces.append([idx0, idx0 + 2, idx0 + 3])
    faces.append([idx0, idx0 + 1, idx0 + 2])
    normals.append([0,0,1])
    normals.append([0,0,1])

def create_annotation_faces(annotations: list) -> AnnotationFaces:
    """
    annotation要素をもとに板ポリゴンのvertices, normals, facesを生成
    """
    vertices = []
    normals = []
    faces = []
    uvs = []
    for annotation in annotations:
        append_annotation_face(annotation, vertices, normals, faces)
    return AnnotationFaces(vertices, normals, faces)

# 動作確認：
# あらかじめjson配下にFMEから出力したannotations.jsonを配置してください。
annotation_path = "./fme_workflow/json/annotations.json"

## ここは実在するフォントを選ぶ
font_path = 'C:/Windows/Fonts/meiryob.ttc'
font = ImageFont.truetype('C:/Windows/Fonts/meiryob.ttc', 32)
image_size = 512
output_path = "output/annotations.glb"
os.makedirs("output", exist_ok=True)

with open(annotation_path, mode="r", encoding="utf-8") as f:
    annotations = json.load(f)

# 板ポリゴン生成
faces = create_annotation_faces(annotations)

# テクスチャ生成
texture_atlas = create_annotation_texture_atlas(annotations, image_size, font)
tex_visual = create_trimesh_texture_visuals(texture_atlas)

# メッシュ生成
mesh = trimesh.Trimesh(
    vertices=faces.vertices,
    faces=faces.faces,
    face_normals=faces.normals,
    visual=tex_visual,
    validate=True,
    process=False
    )

# glb形式で保存
mesh.export(file_type="glb", file_obj=output_path)

# テクスチャ画像を確認したい場合はここをコメントアウト。
os.makedirs("texture")
texture_atlas_path = "texture/annotations.png"
texture_atlas.image.save(texture_atlas_path)

#meshを目視したい人はここをコメントアウト。
#mesh.show()
