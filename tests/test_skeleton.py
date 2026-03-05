from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import sys
import types

import pytest


@pytest.fixture(scope="module")
def skeleton_module():
    """Load ``skeleton.py`` from local source without requiring package install."""
    src_pkg = Path(__file__).resolve().parents[1] / "src" / "xrd_learn"

    pkg = types.ModuleType("xrd_learn")
    pkg.__path__ = [str(src_pkg)]
    pkg.__version__ = "0.0.test"
    sys.modules["xrd_learn"] = pkg

    spec = spec_from_file_location("xrd_learn.skeleton", src_pkg / "skeleton.py")
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    sys.modules["xrd_learn.skeleton"] = module

    yield module

    for name in ["xrd_learn.skeleton", "xrd_learn"]:
        sys.modules.pop(name, None)


__author__ = "Yichen Guo"
__copyright__ = "Yichen Guo"
__license__ = "MIT"


def test_fib(skeleton_module):
    """API tests."""
    assert skeleton_module.fib(1) == 1
    assert skeleton_module.fib(2) == 1
    assert skeleton_module.fib(7) == 13
    with pytest.raises(AssertionError):
        skeleton_module.fib(-10)


def test_main(capsys, skeleton_module):
    """CLI tests."""
    skeleton_module.main(["7"])
    captured = capsys.readouterr()
    assert "The 7-th Fibonacci number is 13" in captured.out
