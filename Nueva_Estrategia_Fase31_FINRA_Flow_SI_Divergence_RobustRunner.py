import requests

_orig_response_json = requests.models.Response.json


def _patched_json(self, *args, **kwargs):
    obj = _orig_response_json(self, *args, **kwargs)
    # FINRA's endpoint has returned both object- and list-shaped JSON.
    # Normalize a top-level list to the shape expected by Phase 31 without
    # changing the underlying data or PIT logic.
    if isinstance(obj, list):
        return {'data': obj}
    return obj


requests.models.Response.json = _patched_json

import Nueva_Estrategia_Fase31_FINRA_Flow_SI_Divergence as phase31


if __name__ == '__main__':
    phase31.main()
