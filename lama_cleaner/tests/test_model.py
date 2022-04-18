import os
from pathlib import Path

import cv2
import numpy as np
import pytest

from lama_cleaner.model_manager import ModelManager
from lama_cleaner.schema import Config, HDStrategy

current_dir = Path(__file__).parent.absolute().resolve()


def get_data():
    img = cv2.imread(str(current_dir / 'image.png'))
    img = cv2.cvtColor(img, cv2.COLOR_BGRA2RGB)
    mask = cv2.imread(str(current_dir / 'mask.png'), cv2.IMREAD_GRAYSCALE)
    return img, mask


def get_config(strategy):
    return Config(
        ldm_steps=1,
        hd_strategy=strategy,
        hd_strategy_crop_margin=32,
        hd_strategy_crop_trigger_size=200,
        hd_strategy_resize_limit=200,
    )


def assert_equal(model, config, gt_name):
    img, mask = get_data()
    res = model(img, mask, config)
    # cv2.imwrite(gt_name, res,
    #             [int(cv2.IMWRITE_JPEG_QUALITY), 100, int(cv2.IMWRITE_PNG_COMPRESSION), 0])

    """
    Note that JPEG is lossy compression, so even if it is the highest quality 100, 
    when the saved image is reloaded, a difference occurs with the original pixel value. 
    If you want to save the original image as it is, save it as PNG or BMP.
    """
    gt = cv2.imread(str(current_dir / gt_name), cv2.IMREAD_UNCHANGED)
    assert np.array_equal(res, gt)


@pytest.mark.parametrize('strategy', [HDStrategy.ORIGINAL, HDStrategy.RESIZE, HDStrategy.CROP])
def test_lama(strategy):
    model = ModelManager(name='lama', device='cpu')
    assert_equal(model, get_config(strategy), f'lama_{strategy[0].upper() + strategy[1:]}_result.png')


@pytest.mark.parametrize('strategy', [HDStrategy.ORIGINAL, HDStrategy.RESIZE, HDStrategy.CROP])
def test_ldm(strategy):
    model = ModelManager(name='ldm', device='cpu')
    assert_equal(model, get_config(strategy), f'ldm_{strategy[0].upper() + strategy[1:]}_result.png')
