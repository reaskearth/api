
import sys
import pytest
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

class TestTools:

    @pytest.mark.parametrize("product", ['Metryc', 'DeepCyc'])
    @pytest.mark.parametrize("halo", [0, 1, 2])
    @pytest.mark.parametrize("regrid_resolution", [1, 3, 5])
    def test_get_tcwind_csv(self, halo, regrid_resolution):
        pass
