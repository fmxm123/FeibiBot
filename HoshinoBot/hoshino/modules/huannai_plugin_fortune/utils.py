from PIL import Image, ImageDraw, ImageFont
import os
from typing import Optional, Tuple, Dict, List
from pathlib import Path
import random
try:
    import ujson as json
except ModuleNotFoundError:
    import json

from .config import fortune_config

def get_copywriting(charaid: str = None, theme:str = None) -> Tuple[str, str]:
    '''
        Read the copywriting.json, choice a luck with a random content
    '''
    _p: Path = fortune_config.fortune_path / "fortune" / "copywriting.json"
    _s: Path = fortune_config.fortune_path / "fortune" / "special_dec.json"
    
    if charaid:
        with open(_s, "r", encoding="utf-8") as f:
            content = json.load(f)
        for i in content[theme]:
            if charaid in i['charaid']:
                desc = random.choice(i['type'])
                for i in content["luck_type"]:
                    if i['good-luck'] == desc['good-luck']:
                        return i['name'], desc['content']
    
    with open(_p, "r", encoding="utf-8") as f:
        content = json.load(f).get("copywriting")
            
    luck = random.choice(content)
        
    title: str = luck.get("good-luck")
    text: str = random.choice(luck.get("content"))

    return title, text

def randomBasemap(theme: str, spec_path: Optional[str] = None) -> Path:
    if isinstance(spec_path, str):
        p: Path = fortune_config.fortune_path / "img" / spec_path
        return p

    if theme == "random":
        __p: Path = fortune_config.fortune_path / "img"
        
        # Each dir is a theme, remember add _flag after the names of themes
        themes: List[str] = [f.name for f in __p.iterdir() if f.is_dir() and themes_flag_check(f.name)]
        picked: str = random.choice(themes)

        _p: Path = __p / picked
        
        # Each file is a posix path of images directory
        images_dir: List[Path] = [i for i in _p.iterdir() if i.is_file()]
        p: Path = random.choice(images_dir)
    else:
        _p: Path = fortune_config.fortune_path / "img" / theme
        images_dir: List[Path] = [i for i in _p.iterdir() if i.is_file()]
        p: Path = random.choice(images_dir)
    
    return p

def drawing(gid: str, uid: str, theme: str, spec_path: Optional[str] = None) -> Path:
    # 1. Random choice a base image
    imgPath: Path = randomBasemap(theme, spec_path)
    img: Image.Image = Image.open(imgPath)
    draw = ImageDraw.Draw(img)
    
    if theme in ("pcr", "genshin", "touhou"):
        filename = os.path.basename(imgPath)
        charaid: str = filename.lstrip('frame_')[:-4]
    else:
        charaid = None
        
    # 2. Random choice a luck text with title
    title, text = get_copywriting(charaid, theme)

    # 3. Draw
    font_size = 45
    color = "#F5F5F5"
    image_font_center = [140, 99]
    fontPath = {
        "title": f"{fortune_config.fortune_path}/font/Mamelon.otf",
        "text": f"{fortune_config.fortune_path}/font/sakura.ttf",
    }
    ttfront = ImageFont.truetype(fontPath["title"], font_size)
    bbox_title = draw.textbbox((0, 0), title, font=ttfront)
    text_width_title = bbox_title[2] - bbox_title[0]
    text_height_title = bbox_title[3] - bbox_title[1]
    draw.text(
        (
            image_font_center[0] - text_width_title / 2,
            image_font_center[1] - text_height_title / 2,
        ),
        title,
        fill=color,
        font=ttfront,
    )
    
    # Text rendering
    font_size = 25
    color = "#323232"
    image_font_center = [140, 297]
    ttfront = ImageFont.truetype(fontPath["text"], font_size)
    slices, result = decrement(text)
    
    for i in range(slices):
        font_height: int = len(result[i]) * (font_size + 4)
        textVertical: str = "\n".join(result[i])
        x: int = int(
            image_font_center[0]
            + (slices - 2) * font_size / 2
            + (slices - 1) * 4
            - i * (font_size + 4)
        )
        y: int = int(image_font_center[1] - font_height / 2)
        draw.text((x, y), textVertical, fill=color, font=ttfront)
    
    # Save
    outPath: Path = exportFilePath(imgPath, gid, uid)
    img.save(outPath)
    return outPath

def exportFilePath(originalFilePath: Path, gid: str, uid: str) -> Path:
    dirPath: Path = fortune_config.fortune_path / "out"
    if not dirPath.exists():
        dirPath.mkdir(exist_ok=True, parents=True)

    outPath: Path = originalFilePath.parent.parent.parent / "out" / f"{gid}_{uid}.png" 
    return outPath

def decrement(text: str) -> Tuple[int, List[str]]:
    '''
        Split the text, return the number of columns and text list
        TODO: Now, it ONLY fit with 2 columns of text
    '''
    length: int = len(text)
    result: List[str] = []
    cardinality = 9
    if length > 4 * cardinality:
        raise Exception
    
    col_num: int = 1
    while length > cardinality:
        col_num += 1
        length -= cardinality
    
    # Optimize for two columns
    space = " "
    length = len(text) # Value of length is changed!
    
    if col_num == 2:
        if length % 2 == 0:
            # even
            fillIn = space * int(9 - length / 2)
            return col_num, [text[: int(length / 2)] + fillIn, fillIn + text[int(length / 2) :]]
        else:
            # odd number
            fillIn = space * int(9 - (length + 1) / 2)
            return col_num, [text[: int((length + 1) / 2)] + fillIn, fillIn + space + text[int((length + 1) / 2) :]]
    
    for i in range(col_num):
        if i == col_num - 1 or col_num == 1:
            result.append(text[i * cardinality :])
        else:
            result.append(text[i * cardinality : (i + 1) * cardinality])
            
    return col_num, result

def themes_flag_check(theme: str) -> bool:
    '''
        Read the config json, return the status of a theme
    '''
    flags_config_path: Path = fortune_config.fortune_path / "fortune_config.json"
    
    with flags_config_path.open("r", encoding="utf-8") as f:
        data: Dict[str, bool] = json.load(f)
    
        return data.get((theme + "_flag"), False)