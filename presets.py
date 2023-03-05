PROMPT = {
    "none": "",
    "anime": "anime, illustration, cartoon",
    "midjourney": "epic realistic, faded, neutral colors, ((((hdr)))), ((((muted colors)))), intricate scene, "
                  "artstation, hyper detailed, cinematic shot, warm lights, dramatic light, intricate details, "
                  "vignette, complex background"
}

NEGATIVE_PROMPT = {
    "none": "",
    "standard": "deformed, bad anatomy, disfigured, poorly drawn face, watermark, watermarked, mutation"
}

RESOLUTIONS = {

    "1:1": {"height": 512, "width": 512},
    "2:1": {"height": 1024, "width": 512},
    "1:2": {"height": 512, "width": 1024},
    "3:2": {"height": 768, "width": 512},
    "2:3": {"height": 512, "width": 768},

    "low 1:1": {"height": 256, "width": 256},
    "low 2:1": {"height": 512, "width": 256},
    "low 1:2": {"height": 256, "width": 512},
    "low 3:2": {"height": 384, "width": 256},
    "low 2:3": {"height": 256, "width": 384},
}