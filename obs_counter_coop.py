"""
OBS Co-op Counter Script
========================
Tracks individual counters for up to 4 players.
Each player has their own Text source and three hotkeys:
  • [Player Name]: Increment
  • [Player Name]: Decrement
  • [Player Name]: Reset

Setup:
  1. Create a Text (GDI+) source for each player in your scene.
  2. Load this script via OBS → Tools → Scripts → "+".
  3. Set player count, names, and source names below.
  4. Bind hotkeys in OBS Settings → Hotkeys.
"""

import obspython as obs

# ── Config defaults ────────────────────────────────────────────────────────────
MAX_PLAYERS = 4

DEFAULT_NAMES   = ["Player 1", "Player 2", "Player 3", "Player 4"]
DEFAULT_SOURCES = ["Counter P1", "Counter P2", "Counter P3", "Counter P4"]

# ── Runtime state ──────────────────────────────────────────────────────────────
player_count = 2
step_size    = 1
min_value    = -9999
max_value    = 9999
start_value  = 0

players = [
    {
        "name":    DEFAULT_NAMES[i],
        "source":  DEFAULT_SOURCES[i],
        "prefix":  "",
        "suffix":  "",
        "counter": 0,
        "hk_inc":  obs.OBS_INVALID_HOTKEY_ID,
        "hk_dec":  obs.OBS_INVALID_HOTKEY_ID,
        "hk_rst":  obs.OBS_INVALID_HOTKEY_ID,
    }
    for i in range(MAX_PLAYERS)
]


# ── Core helpers ───────────────────────────────────────────────────────────────
def update_text(idx):
    p = players[idx]
    source = obs.obs_get_source_by_name(p["source"])
    if source is None:
        return
    text = f"{p['prefix']}{p['counter']}{p['suffix']}"
    settings = obs.obs_data_create()
    obs.obs_data_set_string(settings, "text", text)
    obs.obs_source_update(source, settings)
    obs.obs_data_release(settings)
    obs.obs_source_release(source)


def make_increment_cb(idx):
    def cb(pressed):
        if not pressed:
            return
        players[idx]["counter"] = min(players[idx]["counter"] + step_size, max_value)
        update_text(idx)
    return cb


def make_decrement_cb(idx):
    def cb(pressed):
        if not pressed:
            return
        players[idx]["counter"] = max(players[idx]["counter"] - step_size, min_value)
        update_text(idx)
    return cb


def make_reset_cb(idx):
    def cb(pressed):
        if not pressed:
            return
        players[idx]["counter"] = max(min_value, min(start_value, max_value))
        update_text(idx)
    return cb


# Keep references so GC doesn't kill them
_callbacks = []


def register_hotkeys():
    """Register (or re-label) hotkeys for all players."""
    global _callbacks
    _callbacks = []

    for i in range(MAX_PLAYERS):
        p    = players[i]
        name = p["name"] or f"Player {i+1}"

        inc_cb = make_increment_cb(i)
        dec_cb = make_decrement_cb(i)
        rst_cb = make_reset_cb(i)
        _callbacks.extend([inc_cb, dec_cb, rst_cb])

        if p["hk_inc"] == obs.OBS_INVALID_HOTKEY_ID:
            p["hk_inc"] = obs.obs_hotkey_register_frontend(
                f"counter_p{i+1}_inc",
                f"{name}: Increment (+1)",
                inc_cb
            )
            p["hk_dec"] = obs.obs_hotkey_register_frontend(
                f"counter_p{i+1}_dec",
                f"{name}: Decrement (-1)",
                dec_cb
            )
            p["hk_rst"] = obs.obs_hotkey_register_frontend(
                f"counter_p{i+1}_rst",
                f"{name}: Reset",
                rst_cb
            )


# ── OBS Script API ─────────────────────────────────────────────────────────────
def script_description():
    return (
        "<b>Co-op Hotkey Counter</b><br>"
        "Individual counters for up to 4 players.<br>"
        "Each player needs their own Text (GDI+) source.<br><br>"
        "After configuring, bind hotkeys in <i>Settings → Hotkeys</i>."
    )


def script_defaults(settings):
    obs.obs_data_set_default_int   (settings, "player_count",    2)
    obs.obs_data_set_default_int   (settings, "start_value",     0)
    obs.obs_data_set_default_int   (settings, "step_size",       1)
    obs.obs_data_set_default_int   (settings, "min_value",       -9999)
    obs.obs_data_set_default_int   (settings, "max_value",       9999)
    for i in range(MAX_PLAYERS):
        obs.obs_data_set_default_string(settings, f"p{i+1}_name",   DEFAULT_NAMES[i])
        obs.obs_data_set_default_string(settings, f"p{i+1}_source", DEFAULT_SOURCES[i])
        obs.obs_data_set_default_string(settings, f"p{i+1}_prefix", "")
        obs.obs_data_set_default_string(settings, f"p{i+1}_suffix", "")


def script_properties():
    props = obs.obs_properties_create()

    obs.obs_properties_add_int(props, "player_count", "Number of players", 1, MAX_PLAYERS, 1)
    obs.obs_properties_add_int (props, "start_value",  "Start / Reset value", -9999, 9999, 1)
    obs.obs_properties_add_int (props, "step_size",    "Step size",           1,     999,  1)
    obs.obs_properties_add_int (props, "min_value",    "Minimum value",       -9999, 9999, 1)
    obs.obs_properties_add_int (props, "max_value",    "Maximum value",       -9999, 9999, 1)

    obs.obs_properties_add_text(props, "_sep", "──── Per-player settings ────", obs.OBS_TEXT_INFO)

    # Collect existing text source names for the dropdowns
    text_source_names = []
    sources = obs.obs_enum_sources()
    if sources:
        for src in sources:
            sid = obs.obs_source_get_unversioned_id(src)
            if sid in ("text_gdiplus", "text_ft2_source"):
                text_source_names.append(obs.obs_source_get_name(src))
        obs.source_list_release(sources)

    for i in range(MAX_PLAYERS):
        n = i + 1
        obs.obs_properties_add_text(props, f"p{n}_name",   f"P{n} display name", obs.OBS_TEXT_DEFAULT)
        obs.obs_properties_add_text(props, f"p{n}_prefix", f"P{n} prefix",        obs.OBS_TEXT_DEFAULT)
        obs.obs_properties_add_text(props, f"p{n}_suffix", f"P{n} suffix",        obs.OBS_TEXT_DEFAULT)

        sp = obs.obs_properties_add_list(
            props, f"p{n}_source", f"P{n} text source",
            obs.OBS_COMBO_TYPE_EDITABLE, obs.OBS_COMBO_FORMAT_STRING
        )
        for sname in text_source_names:
            obs.obs_property_list_add_string(sp, sname, sname)

    return props


def script_update(settings):
    global player_count, step_size, min_value, max_value, start_value

    player_count = obs.obs_data_get_int(settings, "player_count")
    step_size    = obs.obs_data_get_int(settings, "step_size")
    min_value    = obs.obs_data_get_int(settings, "min_value")
    max_value    = obs.obs_data_get_int(settings, "max_value")
    start_value  = obs.obs_data_get_int(settings, "start_value")

    for i in range(MAX_PLAYERS):
        n = i + 1
        players[i]["name"]    = obs.obs_data_get_string(settings, f"p{n}_name")   or f"Player {n}"
        players[i]["source"]  = obs.obs_data_get_string(settings, f"p{n}_source")
        players[i]["prefix"]  = obs.obs_data_get_string(settings, f"p{n}_prefix")
        players[i]["suffix"]  = obs.obs_data_get_string(settings, f"p{n}_suffix")
        players[i]["counter"] = max(min_value, min(start_value, max_value))
        if i < player_count:
            update_text(i)


def script_load(settings):
    register_hotkeys()

    # Restore saved bindings
    for i in range(MAX_PLAYERS):
        p = players[i]
        for hk_key, hk_id in [("hk_inc", p["hk_inc"]),
                               ("hk_dec", p["hk_dec"]),
                               ("hk_rst", p["hk_rst"])]:
            save_key  = f"p{i+1}_{hk_key}"
            arr = obs.obs_data_get_array(settings, save_key)
            obs.obs_hotkey_load(hk_id, arr)
            obs.obs_data_array_release(arr)


def script_save(settings):
    for i in range(MAX_PLAYERS):
        p = players[i]
        for hk_key, hk_id in [("hk_inc", p["hk_inc"]),
                               ("hk_dec", p["hk_dec"]),
                               ("hk_rst", p["hk_rst"])]:
            save_key = f"p{i+1}_{hk_key}"
            arr = obs.obs_hotkey_save(hk_id)
            obs.obs_data_set_array(settings, save_key, arr)
            obs.obs_data_array_release(arr)


def script_unload():
    for cb in _callbacks:
        obs.obs_hotkey_unregister(cb)
