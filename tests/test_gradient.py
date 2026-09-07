"""Unit tests for gradient generation."""

from storeshot.gradient import create_gradient_image


def test_vertical_gradient_stops():
    c1 = (15, 23, 36, 255)
    c2 = (11, 18, 32, 255)
    img = create_gradient_image(100, 200, c1, c2, orientation="vertical")
    assert img.size == (100, 200)

    # Check top pixel stop
    top_px = img.getpixel((50, 0))
    for i in range(4):
        assert abs(top_px[i] - c1[i]) <= 1

    # Check bottom pixel stop
    bot_px = img.getpixel((50, 199))
    for i in range(4):
        assert abs(bot_px[i] - c2[i]) <= 1

    # Check midpoint interpolation
    mid_px = img.getpixel((50, 100))
    for i in range(4):
        expected = int(round((c1[i] + c2[i]) / 2.0))
        assert abs(mid_px[i] - expected) <= 2


def test_horizontal_gradient_stops():
    c1 = (255, 0, 0, 255)
    c2 = (0, 0, 255, 255)
    img = create_gradient_image(200, 100, c1, c2, orientation="horizontal")
    assert img.size == (200, 100)

    # Check leftmost pixel stop
    left_px = img.getpixel((0, 50))
    for i in range(4):
        assert abs(left_px[i] - c1[i]) <= 1

    # Check rightmost pixel stop
    right_px = img.getpixel((199, 50))
    for i in range(4):
        assert abs(right_px[i] - c2[i]) <= 1
