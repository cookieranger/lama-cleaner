import abc

import cv2
import torch
from loguru import logger

from lama_cleaner.helper import boxes_from_mask, resize_max_size, pad_img_to_modulo
from lama_cleaner.schema import Config, HDStrategy


class InpaintModel:
    pad_mod = 8

    def __init__(self, device):
        """

        Args:
            device:
        """
        self.device = device
        self.init_model(device)

    @abc.abstractmethod
    def init_model(self, device):
        ...

    @staticmethod
    @abc.abstractmethod
    def is_downloaded() -> bool:
        ...

    @abc.abstractmethod
    def forward(self, image, mask, config: Config):
        """Input image and output image have same size
        image: [H, W, C] RGB
        mask: [H, W]
        return: BGR IMAGE
        """
        ...

    def _pad_forward(self, image, mask, config: Config):
        origin_height, origin_width = image.shape[:2]
        padd_image = pad_img_to_modulo(image, mod=self.pad_mod)
        padd_mask = pad_img_to_modulo(mask, mod=self.pad_mod)
        result = self.forward(padd_image, padd_mask, config)
        result = result[0:origin_height, 0:origin_width, :]

        original_pixel_indices = mask != 255
        result[original_pixel_indices] = image[:, :, ::-1][original_pixel_indices]
        return result

    @torch.no_grad()
    def __call__(self, image, mask, config: Config):
        """
        image: [H, W, C] RGB, not normalized
        mask: [H, W]
        return: BGR IMAGE
        """
        inpaint_result = None
        logger.info(f"hd_strategy: {config.hd_strategy}")
        if config.hd_strategy == HDStrategy.CROP:
            if max(image.shape) > config.hd_strategy_crop_trigger_size:
                logger.info(f"Run crop strategy")
                boxes = boxes_from_mask(mask)
                crop_result = []
                for box in boxes:
                    crop_image, crop_box = self._run_box(image, mask, box, config)
                    crop_result.append((crop_image, crop_box))

                inpaint_result = image[:, :, ::-1]
                for crop_image, crop_box in crop_result:
                    x1, y1, x2, y2 = crop_box
                    inpaint_result[y1:y2, x1:x2, :] = crop_image

        elif config.hd_strategy == HDStrategy.RESIZE:
            if max(image.shape) > config.hd_strategy_resize_limit:
                origin_size = image.shape[:2]
                downsize_image = resize_max_size(image, size_limit=config.hd_strategy_resize_limit)
                downsize_mask = resize_max_size(mask, size_limit=config.hd_strategy_resize_limit)

                logger.info(f"Run resize strategy, origin size: {image.shape} forward size: {downsize_image.shape}")
                inpaint_result = self._pad_forward(downsize_image, downsize_mask, config)

                # only paste masked area result
                inpaint_result = cv2.resize(inpaint_result,
                                            (origin_size[1], origin_size[0]),
                                            interpolation=cv2.INTER_CUBIC)

                original_pixel_indices = mask != 255
                inpaint_result[original_pixel_indices] = image[:, :, ::-1][original_pixel_indices]

        if inpaint_result is None:
            inpaint_result = self._pad_forward(image, mask, config)

        return inpaint_result

    def _run_box(self, image, mask, box, config: Config):
        """

        Args:
            image: [H, W, C] RGB
            mask: [H, W, 1]
            box: [left,top,right,bottom]

        Returns:
            BGR IMAGE
        """
        box_h = box[3] - box[1]
        box_w = box[2] - box[0]
        cx = (box[0] + box[2]) // 2
        cy = (box[1] + box[3]) // 2
        img_h, img_w = image.shape[:2]

        w = box_w + config.hd_strategy_crop_margin * 2
        h = box_h + config.hd_strategy_crop_margin * 2

        l = max(cx - w // 2, 0)
        t = max(cy - h // 2, 0)
        r = min(cx + w // 2, img_w)
        b = min(cy + h // 2, img_h)

        crop_img = image[t:b, l:r, :]
        crop_mask = mask[t:b, l:r]

        logger.info(f"box size: ({box_h},{box_w}) crop size: {crop_img.shape}")

        return self._pad_forward(crop_img, crop_mask, config), [l, t, r, b]
