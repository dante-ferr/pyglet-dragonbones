from PIL import Image
import json
import pyglet
from typing import TypedDict


class Subtexture(TypedDict):
    name: str
    frameX: int
    frameY: int
    frameWidth: int
    frameHeight: int
    image: (
        pyglet.image.AbstractImage
    )  # Replace with the correct pyglet image type if necessary


def get_subtextures(texture_path, image_path):
    with open(texture_path, "r") as file:
        texture_data = json.load(file)

    subtextures = {}
    atlas_image = Image.open(image_path)

    for subtexture in texture_data["SubTexture"]:
        name = subtexture["name"]
        x = subtexture["x"]
        y = subtexture["y"]
        width = subtexture["width"]
        height = subtexture["height"]
        frameX = subtexture["frameX"]
        frameY = subtexture["frameY"]
        frameWidth = subtexture["frameWidth"]
        frameHeight = subtexture["frameHeight"]

        cropped_image = atlas_image.crop((x, y, x + width, y + height))

        image = pyglet.image.ImageData(width, height, "RGBA", cropped_image.tobytes())
        image.anchor_x = width // 2
        image.anchor_y = height // 2

        subtextures[name] = Subtexture(
            # 'x': x,
            # 'y': y,
            # 'width': width,
            # 'height': height,
            name=name,
            frameX=frameX,
            frameY=frameY,
            frameWidth=frameWidth,
            frameHeight=frameHeight,
            image=image,
        )

    return subtextures
