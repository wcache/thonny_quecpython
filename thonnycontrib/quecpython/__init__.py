from thonny import get_workbench
from thonny.languages import tr
from thonny.plugins.micropython.mp_front import (
    add_micropython_backend,
    GenericBareMetalMicroPythonConfigPage,
    GenericBareMetalMicroPythonProxy,
)
from .view import QuecView, open_quecview


def load_plugin():
    add_micropython_backend(
        "GenericQuecPython",
        GenericBareMetalMicroPythonProxy,
        tr("QuecPython (generic)"),
        GenericBareMetalMicroPythonConfigPage,
        sort_key="51",
    )

    get_workbench().add_view(QuecView, tr("QuecPython Kits"), "s")
    get_workbench().add_command(
        'quecpython_kits',
        'tools',
        tr('QuecPython Kits'),
        open_quecview
    )
