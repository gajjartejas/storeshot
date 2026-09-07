"""Integration tests running full pipeline on sample files."""

from pathlib import Path
from PIL import Image

from storeshot.config import StoreShotConfig
from storeshot.core import process_batch


def test_full_sample_pipeline_integration(tmp_path: Path):
    in_dir = Path("examples/input")
    out_dir = tmp_path / "integration_out"

    assert in_dir.is_dir()
    input_files = sorted(list(in_dir.glob("*.png")))
    assert len(input_files) >= 2

    cfg = StoreShotConfig(
        input_dir=in_dir,
        output_dir=out_dir,
        theme="antigravity",
        text="App Store Ready Screenshots\nGenerate pixel-perfect listings with StoreShot",
        text_position="bottom"
    )

    successful, failed = process_batch(cfg)

    assert len(failed) == 0
    assert len(successful) == len(input_files)

    for in_file in input_files:
        out_file = out_dir / in_file.name
        assert out_file.is_file()
        with Image.open(out_file) as im:
            assert im.size == (1080, 1920)
            assert im.format == "PNG"
