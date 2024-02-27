
import sys
import io
import pytest
import tempfile
import pandas as pd
from pathlib import Path
import subprocess as sp

class TestTools:

    @pytest.mark.skipif(sys.platform == 'win32', reason='Temp file is not writable on Windows')
    @pytest.mark.skipif(sys.platform == 'darwin', reason='Temp file is not writable on Mac')
    @pytest.mark.parametrize("product", ['Metryc', 'DeepCyc'])
    @pytest.mark.parametrize("halo_size", [0, 1, 2])
    @pytest.mark.parametrize("regrid_resolution", [1, 3, 5])
    def test_get_tcwind_csv(self, product, halo_size, regrid_resolution):

        get_tcwind_csv = Path(__file__).resolve().parent.parent / 'tools' / 'get_tcwind_csv.py'
        assert get_tcwind_csv.exists()
        input_file = Path(__file__).resolve().parent / 'starbucks_us_locations.csv'
        assert input_file.exists()

        input_df = pd.read_csv(input_file).sample(10)

        tmp = tempfile.NamedTemporaryFile()
        input_df.to_csv(tmp, index=False)

        cmd = ['python3', str(get_tcwind_csv), '--product', product, '--location_csv', tmp.name]
        if product == 'DeepCyc':
            cmd.extend(['--return_period', str(100)])

            if halo_size == 0:
                cmd.extend(['--regrid_resolution', str(regrid_resolution)])
            else:
                cmd.extend(['--halo_size', str(halo_size)])

        ret = sp.run(cmd, capture_output=True)
        assert ret.returncode == 0

        ret_df = pd.read_csv(io.StringIO(ret.stdout.decode()), sep=',')

        set(input_df.location_id) == set(ret_df.location_id)

        if product == 'DeepCyc':
            if halo_size == 0:
                assert len(ret_df) == len(input_df)

                if regrid_resolution > 1:
                    assert ret_df.iloc[0].resolution_deg == regrid_resolution*(2**-7 + 2**-9)
            else:
                side_len = halo_size*2 + 1
                assert len(ret_df) == len(input_df)*side_len**2


