import os
import random
import sys
import argparse

import numpy as np
from PIL import Image
import torch

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from modules.AutoEncoders import VariationalAE
from modules.clip import Clip
from modules.sample import sampling

from modules.Utilities import upscale
from modules.UltimateSDUpscale import UltimateSDUpscale as USDU
from modules.AutoDetailer import ADetailer

from modules.FileManaging import ImageSaver, Loader
from modules.Model import LoRas
from modules.Utilities import Enhancer, Latent

def pipeline(prompt, w, h, hires_fix = False):
    ckpt = "./_internal/checkpoints/Meina V10 - baked VAE.safetensors"
    with torch.inference_mode():
        checkpointloadersimple = Loader.CheckpointLoaderSimple()
        checkpointloadersimple_241 = checkpointloadersimple.load_checkpoint(
            ckpt_name=ckpt
        )
        cliptextencode = Clip.CLIPTextEncode()
        emptylatentimage = Latent.EmptyLatentImage()
        ksampler_instance = sampling.KSampler2()
        vaedecode = VariationalAE.VAEDecode()
        saveimage = ImageSaver.SaveImage()
        latent_upscale = upscale.LatentUpscale()
    try:
        prompt = Enhancer.enhance_prompt(prompt)
    except:
        pass
    while prompt is None:
        pass
    with torch.inference_mode():
        try:
            loraloader = LoRas.LoraLoader()
            loraloader_274 = loraloader.load_lora(
                lora_name="add_detail.safetensors",
                strength_model=0.7,
                strength_clip=0.7,
                model=checkpointloadersimple_241[0],
                clip=checkpointloadersimple_241[1],
            )
            print("loading add_detail.safetensors")
        except:
            loraloader_274 = checkpointloadersimple_241
        clipsetlastlayer = Clip.CLIPSetLastLayer()
        clipsetlastlayer_257 = clipsetlastlayer.set_last_layer(
            stop_at_clip_layer=-2, clip=loraloader_274[1]
        )
        applystablefast_158 = loraloader_274
        cliptextencode_242 = cliptextencode.encode(
            text=prompt,
            clip=clipsetlastlayer_257[0],
        )
        cliptextencode_243 = cliptextencode.encode(
            text="(worst quality, low quality:1.4), (zombie, sketch, interlocked fingers, comic), (embedding:EasyNegative), (embedding:badhandv4), (embedding:lr), (embedding:ng_deepnegative_v1_75t)",
            clip=clipsetlastlayer_257[0],
        )
        emptylatentimage_244 = emptylatentimage.generate(
            width=w, height=h, batch_size=1
        )
        ksampler_239 = ksampler_instance.sample(
            seed=random.randint(1, 2**64),
            steps=40,
            cfg=7,
            sampler_name="dpm_adaptive",
            scheduler="karras",
            denoise=1,
            model=applystablefast_158[0],
            positive=cliptextencode_242[0],
            negative=cliptextencode_243[0],
            latent_image=emptylatentimage_244[0],
        )
        if hires_fix:
            latentupscale_254 = latent_upscale.upscale(
                upscale_method="bislerp",
                width=w * 2,
                height=h * 2,
                crop="disabled",
                samples=ksampler_239[0],
            )
            ksampler_253 = ksampler_instance.sample(
                seed=random.randint(1, 2**64),
                steps=10,
                cfg=8,
                sampler_name="euler_ancestral",
                scheduler="normal",
                denoise=0.45,
                model=applystablefast_158[0],
                positive=cliptextencode_242[0],
                negative=cliptextencode_243[0],
                latent_image=latentupscale_254[0],
            )
        else:
            ksampler_253 = ksampler_239
        vaedecode_240 = vaedecode.decode(
            samples=ksampler_253[0],
            vae=checkpointloadersimple_241[2],
        )
        saveimage.save_images(filename_prefix="LD", images=vaedecode_240[0])
        for image in vaedecode_240[0]:
            i = 255.0 * image.cpu().numpy()
            img = Image.fromarray(np.clip(i, 0, 255).astype(np.uint8))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the LightDiffusion pipeline.")
    parser.add_argument("prompt", type=str, help="The prompt for the pipeline.")
    parser.add_argument("width", type=int, help="The width of the generated image.")
    parser.add_argument("height", type=int, help="The height of the generated image.")
    parser.add_argument("--hires-fix", action="store_true", help="Enable high-resolution fix.")
    args = parser.parse_args()

    pipeline(args.prompt, args.width, args.height, args.hires_fix)