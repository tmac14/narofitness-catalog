"""Ordia core — manifest loader, path enforcement, and CLI."""



from ordia.config import OrdiaConfig, load_ordia_config, validate_ordia_manifest



try:

    from importlib.metadata import PackageNotFoundError, version



    try:

        __version__ = version("ordia-core")

    except PackageNotFoundError:

        __version__ = "0.8.0"

except ImportError:  # pragma: no cover

    __version__ = "0.8.0"



__all__ = [

    "OrdiaConfig",

    "load_ordia_config",

    "validate_ordia_manifest",

    "__version__",

]

