import random
from typing import Dict, List

CINEMATIC_VERSION = "v2-cinematic"  # Updated version name

def get_cinematic_preset(preset_name: str = "default") -> Dict:
    """Returns a dictionary of cinematic presets for different effects."""
    presets = {
        "default": {
            "zoom": {"factor": 1.04, "duration": 2.5, "ease": "inout"},
            "color": {"contrast": 1.08, "saturation": 1.06, "brightness": 0.01, "warmth": 0.02},
            "text": {"fade_duration": 0.5, "border_width": 2, "border_opacity": 0.5}
        },
        "dramatic": {
            "zoom": {"factor": 1.08, "duration": 3.0, "ease": "in"},
            "color": {"contrast": 1.15, "saturation": 1.1, "brightness": -0.02, "warmth": 0.03},
            "text": {"fade_duration": 0.8, "border_width": 3, "border_opacity": 0.6}
        },
        "subtle": {
            "zoom": {"factor": 1.02, "duration": 2.0, "ease": "out"},
            "color": {"contrast": 1.04, "saturation": 1.03, "brightness": 0.02, "warmth": 0.01},
            "text": {"fade_duration": 0.3, "border_width": 1, "border_opacity": 0.4}
        }
    }
    return presets.get(preset_name, presets["default"])

def create_zoom_effect(duration: float, preset: Dict = None) -> str:
    """Creates a zoom effect filter string."""
    if preset is None:
        preset = get_cinematic_preset()
    
    zoom = preset.get("zoom", {})
    factor = zoom.get("factor", 1.04)
    zoom_duration = zoom.get("duration", 2.5)
    
    return f"zoompan=z='min(zoom+0.0005,{factor})':d={zoom_duration*25}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"

def create_color_grade(preset: Dict = None) -> str:
    """Creates color grading filter string."""
    if preset is None:
        preset = get_cinematic_preset()
    
    color = preset.get("color", {})
    return (
        f"eq=contrast={color.get('contrast', 1.08)}:"
        f"saturation={color.get('saturation', 1.06)}:"
        f"brightness={color.get('brightness', 0.01)},"
        f"colorbalance=rs={color.get('warmth', 0.02)}:gs=0.01"
    )

def create_text_overlay(
    text: str, 
    start_time: float, 
    end_time: float, 
    font_path: str,
    preset: Dict = None
) -> str:
    """Creates a text overlay with fade in/out effects."""
    if preset is None:
        preset = get_cinematic_preset()
    
    text_style = preset.get("text", {})
    fade_duration = text_style.get("fade_duration", 0.5)
    border_width = text_style.get("border_width", 2)
    border_opacity = text_style.get("border_opacity", 0.5)
    
    safe_text = text.replace("'", "'\\\\\\''").replace(":", "\\:")
    
    return (
        f"drawtext=fontfile='{font_path}':text='{safe_text}':"
        f"x=(w-text_w)/2:y=(h-text_h)/2:"
        f"fontsize=60:fontcolor=white:"
        f"borderw={border_width}:bordercolor=black@{border_opacity}:"
        f"alpha='if(lt(t,{start_time}+{fade_duration}),(t-{start_time})/{fade_duration},"
        f"if(gt(t,{end_time}-{fade_duration}),1-(t-({end_time}-{fade_duration}))/{fade_duration},1))'"
    )

def create_audio_filters(duration: float) -> List[str]:
    """Creates audio filters for fade in/out."""
    return [
        "afade=t=in:st=0:d=0.5",
        f"afade=t=out:st={max(0, duration-0.5)}:d=0.5"
    ]

def create_cinematic_filters(
    image_count: int,
    duration_per_image: float = 3.0,
    preset: str = "default"
) -> Dict:
    """Creates all necessary filters for a cinematic effect."""
    preset_config = get_cinematic_preset(preset)
    filters = []
    
    filters.append("scale=1920:1080:force_original_aspect_ratio=decrease")
    filters.append("pad=1920:1080:(ow-iw)/2:(oh-ih)/2")
    filters.append(create_zoom_effect(duration_per_image, preset_config))
    filters.append(create_color_grade(preset_config))
    filters.append("fps=30")
    
    return {
        "video_filters": filters,
        "audio_filters": create_audio_filters(image_count * duration_per_image),
        "preset": preset_config
    }
