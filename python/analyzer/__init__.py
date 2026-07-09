"""PolyAnalyzer analyzer package."""

from .base import (
    # Constants
    APP_VERSION,
    DEFAULT_BAR_COLOR,
    DEFAULT_MW_COLOR,
    DEFAULT_SETTING_NAME,
    DEFAULT_DSC_SETTING_NAME,
    DEFAULT_TRANSPARENT_BACK,
    FIGURE_DPI,
    FIGURE_SIZE_WITH_TABLE,
    FIGURE_SIZE_WITHOUT_TABLE,
    GPC_FIGURE_SIZE,
    GRIDSPEC_ROWS,
    GRIDSPEC_COLS,
    MW_DATA_OFFSET,
    NORM_COLUMN_INDEX,
    MW_COLUMN_INDEX,
    GPC_X_COLUMN_INDEX,
    GPC_Y_COLUMN_INDEX,
    MIN_PEAK_COLUMNS,
    MIN_GPC_PEAK_COLUMNS,
    MIN_MW_DATA_COLUMNS,
    NORM_SCALE_FACTOR,
    PERCENTAGE_FACTOR,
    BAR_POSITION_WEIGHT_LEFT,
    BAR_POSITION_WEIGHT_RIGHT,
    # Functions
    get_install_dir,
    # Classes
    Logger,
    DataValidator,
    SettingsManager,
    BaseAnalyzer,
    logger,
)


def __getattr__(name: str):
    """Lazily import analyzer classes so lightweight commands stay fast."""
    if name == "GPCAnalyzer":
        from .gpc import GPCAnalyzer
        return GPCAnalyzer
    if name == "DSCAnalyzer":
        from .dsc import DSCAnalyzer
        return DSCAnalyzer
    if name == "MolecularWeightAnalyzer":
        from .mw import MolecularWeightAnalyzer
        return MolecularWeightAnalyzer
    if name == "IRAnalyzer":
        from .ir import IRAnalyzer
        return IRAnalyzer
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

__all__ = [
    "APP_VERSION",
    "DEFAULT_BAR_COLOR",
    "DEFAULT_MW_COLOR",
    "DEFAULT_SETTING_NAME",
    "DEFAULT_DSC_SETTING_NAME",
    "DEFAULT_TRANSPARENT_BACK",
    "FIGURE_DPI",
    "FIGURE_SIZE_WITH_TABLE",
    "FIGURE_SIZE_WITHOUT_TABLE",
    "GPC_FIGURE_SIZE",
    "GRIDSPEC_ROWS",
    "GRIDSPEC_COLS",
    "MW_DATA_OFFSET",
    "NORM_COLUMN_INDEX",
    "MW_COLUMN_INDEX",
    "GPC_X_COLUMN_INDEX",
    "GPC_Y_COLUMN_INDEX",
    "MIN_PEAK_COLUMNS",
    "MIN_GPC_PEAK_COLUMNS",
    "MIN_MW_DATA_COLUMNS",
    "NORM_SCALE_FACTOR",
    "PERCENTAGE_FACTOR",
    "BAR_POSITION_WEIGHT_LEFT",
    "BAR_POSITION_WEIGHT_RIGHT",
    "get_install_dir",
    "Logger",
    "DataValidator",
    "SettingsManager",
    "BaseAnalyzer",
    "DSCAnalyzer",
    "MolecularWeightAnalyzer",
    "IRAnalyzer",
    "logger",
    "GPCAnalyzer",
]
