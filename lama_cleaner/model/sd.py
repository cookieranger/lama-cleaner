import random

import PIL.Image
import cv2
import numpy as np
import torch
from loguru import logger

from lama_cleaner.helper import norm_img

from lama_cleaner.model.base import InpaintModel
from lama_cleaner.schema import Config


#
#
# def preprocess_image(image):
#     w, h = image.size
#     w, h = map(lambda x: x - x % 32, (w, h))  # resize to integer multiple of 32
#     image = image.resize((w, h), resample=PIL.Image.LANCZOS)
#     image = np.array(image).astype(np.float32) / 255.0
#     image = image[None].transpose(0, 3, 1, 2)
#     image = torch.from_numpy(image)
#     # [-1, 1]
#     return 2.0 * image - 1.0
#
#
# def preprocess_mask(mask):
#     mask = mask.convert("L")
#     w, h = mask.size
#     w, h = map(lambda x: x - x % 32, (w, h))  # resize to integer multiple of 32
#     mask = mask.resize((w // 8, h // 8), resample=PIL.Image.NEAREST)
#     mask = np.array(mask).astype(np.float32) / 255.0
#     mask = np.tile(mask, (4, 1, 1))
#     mask = mask[None].transpose(0, 1, 2, 3)  # what does this step do?
#     mask = 1 - mask  # repaint white, keep black
#     mask = torch.from_numpy(mask)
#     return mask


class SD(InpaintModel):
    pad_mod = 32
    min_size = 512

    def init_model(self, device: torch.device, **kwargs):
        # return
        from .sd_pipeline import StableDiffusionInpaintPipeline

        self.model = StableDiffusionInpaintPipeline.from_pretrained(
            self.model_id_or_path,
            revision="fp16",
            torch_dtype=torch.float16,
            use_auth_token=kwargs["hf_access_token"],
        )
        # https://huggingface.co/docs/diffusers/v0.3.0/en/api/pipelines/stable_diffusion#diffusers.StableDiffusionInpaintPipeline.enable_attention_slicing
        self.model.enable_attention_slicing()
        self.model = self.model.to(device)
        self.callbacks = kwargs.pop("callbacks", None)

    @torch.cuda.amp.autocast()
    def forward(self, image, mask, config: Config):
        # return image
        """Input image and output image have same size
        image: [H, W, C] RGB
        mask: [H, W, 1] 255 means area to repaint
        return: BGR IMAGE
        """

        # image = norm_img(image)  # [0, 1]
        # image = image * 2 - 1  # [0, 1] -> [-1, 1]

        # resize to latent feature map size
        # h, w = mask.shape[:2]
        # mask = cv2.resize(mask, (h // 8, w // 8), interpolation=cv2.INTER_AREA)
        # mask = norm_img(mask)
        #
        # image = torch.from_numpy(image).unsqueeze(0).to(self.device)
        # mask = torch.from_numpy(mask).unsqueeze(0).to(self.device)
        # import time
        # time.sleep(2)
        # return image
        seed = config.sd_seed
        random.seed(seed)
        np.random.seed(seed)
        torch.manual_seed(seed)
        torch.cuda.manual_seed_all(seed)

        output = self.model(
            prompt=config.prompt,
            init_image=PIL.Image.fromarray(image),
            mask_image=PIL.Image.fromarray(mask[:, :, -1], mode="L"),
            strength=config.sd_strength,
            num_inference_steps=config.sd_steps,
            guidance_scale=config.sd_guidance_scale,
            output_type="np.array",
            callbacks=self.callbacks,
        ).images[0]

        output = (output * 255).round().astype("uint8")
        output = cv2.cvtColor(output, cv2.COLOR_RGB2BGR)
        return output

    @torch.no_grad()
    def __call__(self, image, mask, config: Config):
        """
        images: [H, W, C] RGB, not normalized
        masks: [H, W]
        return: BGR IMAGE
        """
        img_h, img_w = image.shape[:2]

        # boxes = boxes_from_mask(mask)
        if config.use_croper:
            logger.info("use croper")
            l, t, w, h = (
                config.croper_x,
                config.croper_y,
                config.croper_width,
                config.croper_height,
            )
            r = l + w
            b = t + h

            l = max(l, 0)
            r = min(r, img_w)
            t = max(t, 0)
            b = min(b, img_h)

            crop_img = image[t:b, l:r, :]
            crop_mask = mask[t:b, l:r]

            crop_image = self._pad_forward(crop_img, crop_mask, config)

            inpaint_result = image[:, :, ::-1]
            inpaint_result[t:b, l:r, :] = crop_image
        else:
            inpaint_result = self._pad_forward(image, mask, config)

        return inpaint_result

    @staticmethod
    def is_downloaded() -> bool:
        # model will be downloaded when app start, and can't switch in frontend settings
        return True


class SD14(SD):
    model_id_or_path = "CompVis/stable-diffusion-v1-4"


class SD15(SD):
    model_id_or_path = "CompVis/stable-diffusion-v1-5"
