"""All tunable numbers live here so you can change a rule without touching logic."""

# Labels (these exact strings are stored in MongoDB and returned by the API)
EMERGING = "emerging"
DECLINING = "declining"
ESTABLISHED = "established"   # the UI shows this as "Influential"
RECENT = "recent"
REGULAR = "regular"           # none of the above
ALL_LABELS = (EMERGING, DECLINING, ESTABLISHED, RECENT, REGULAR)

# Rolling windows, in years. The UI toggle (1 Year / 3 Years / 5 Years) picks one.
WINDOWS = (1, 3, 5)
DEFAULT_WINDOW = 3

# A case needs at least this many citations *per year of window* before a
# percentage change means anything (stops "1 -> 4 citations = +300%" noise).
MIN_VOLUME_PER_YEAR = 3

EMERGING_MIN_GROWTH = 1.0      # +100% or more
DECLINING_MAX_GROWTH = -0.5    # -50% or worse

# "Recent" = young case that is already being cited and not fading.
RECENT_MAX_AGE_YEARS = 3
RECENT_MIN_CITATIONS = 3

# "Established" = steady, high citation count in each of the last N years.
TRAILING_YEARS = 4
ESTABLISHED_MIN_MEAN = 8       # average citations per year
ESTABLISHED_MAX_CV = 0.5       # coefficient of variation (std / mean): low = steady
