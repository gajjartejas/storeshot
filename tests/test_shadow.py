"""Unit tests for drop shadow generation."""

from storeshot.shadow import create_drop_shadow


def test_drop_shadow_generation():
    w, h = 200, 300
    color = (0, 0, 0, 128)
    shadow_img, rel_x, rel_y = create_drop_shadow(
        width=w,
        height=h,
        border_radius=20,
        shadow_blur=30,
        shadow_color=color,
        offset_x=10,
        offset_y=20
    )

    assert shadow_img is not None
    assert shadow_img.width > w
    assert shadow_img.height > h
    assert rel_x < 0
    assert rel_y < 0

    center_px = shadow_img.getpixel(
        (shadow_img.width // 2, shadow_img.height // 2)
    )
    assert center_px[3] > 100


def test_transparent_shadow():
    shadow_img, rel_x, rel_y = create_drop_shadow(
        width=200,
        height=300,
        border_radius=10,
        shadow_blur=20,
        shadow_color=(0, 0, 0, 0)
    )
    assert shadow_img is None
    assert rel_x == 0
    assert rel_y == 0
