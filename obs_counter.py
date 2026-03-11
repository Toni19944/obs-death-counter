"""
OBS Counter Script
==================
Adds a configurable counter to a Text (GDI+/FreeType) source.
Format: {prefix}{counter}

Hotkeys (assign in OBS Settings → Hotkeys after loading this script):
  • Counter: Increment  (+1)
  • Counter: Decrement  (-1)
  • Counter: Reset

Setup:
  1. Add a "Text (GDI+)" or "Text (FreeType 2)" source to your scene.
  2. Load this script in OBS → Tools → Scripts → "+" button.
  3. Set the "Text Source Name" to match your source name.
  4. Customize the prefix/format and starting value.
  5. Go to OBS Settings → Hotkeys and bind the three Counter actions.
"""

import obspython as obs

# ── State ──────────────────────────────────────────────────────────────────────
counter_value   = 0
source_name     = ""
counter_prefix  = "Score: "
counter_suffix  = ""
min_value       = -9999
max_value       = 9999
step_size       = 1

hotkey_add_id   = obs.OBS_INVALID_HOTKEY_ID
hotkey_sub_id   = obs.OBS_INVALID_HOTKEY_ID
hotkey_reset_id = obs.OBS_INVALID_HOTKEY_ID


# ── Helpers ────────────────────────────────────────────────────────────────────
def update_text():
    """Push the current counter string to the OBS text source."""
    source = obs.obs_get_source_by_name(source_name)
    if source is None:
        return
    text = f"{counter_prefix}{counter_value}{counter_suffix}"
    settings = obs.obs_data_create()
    obs.obs_data_set_string(settings, "text", text)
    obs.obs_source_update(source, settings)
    obs.obs_data_release(settings)
    obs.obs_source_release(source)


# ── Hotkey callbacks ───────────────────────────────────────────────────────────
def on_increment(pressed):
    if not pressed:
        return
    global counter_value
    counter_value = min(counter_value + step_size, max_value)
    update_text()


def on_decrement(pressed):
    if not pressed:
        return
    global counter_value
    counter_value = max(counter_value - step_size, min_value)
    update_text()


def on_reset(pressed):
    if not pressed:
        return
    global counter_value
    counter_value = 0
    update_text()


# ── OBS Script API ─────────────────────────────────────────────────────────────
def script_description():
    return (
        "<b>Hotkey Counter</b><br>"
        "Displays a live counter inside any Text source.<br>"
        "Configure below, then bind hotkeys in <i>Settings → Hotkeys</i>.<br><br>"
        "Format preview: <code>{prefix}{value}{suffix}</code>"
    )


def script_defaults(settings):
    obs.obs_data_set_default_string(settings, "source_name",    "Counter")
    obs.obs_data_set_default_string(settings, "counter_prefix", "Score: ")
    obs.obs_data_set_default_string(settings, "counter_suffix", "")
    obs.obs_data_set_default_int   (settings, "start_value",    0)
    obs.obs_data_set_default_int   (settings, "step_size",      1)
    obs.obs_data_set_default_int   (settings, "min_value",      -9999)
    obs.obs_data_set_default_int   (settings, "max_value",      9999)


def script_properties():
    props = obs.obs_properties_create()

    # Source picker — lists all text sources in the current scene collection
    sp = obs.obs_properties_add_list(
        props, "source_name", "Text Source Name",
        obs.OBS_COMBO_TYPE_EDITABLE, obs.OBS_COMBO_FORMAT_STRING
    )
    sources = obs.obs_enum_sources()
    if sources:
        for src in sources:
            sid = obs.obs_source_get_unversioned_id(src)
            if sid in ("text_gdiplus", "text_ft2_source"):
                obs.obs_property_list_add_string(
                    sp,
                    obs.obs_source_get_name(src),
                    obs.obs_source_get_name(src)
                )
        obs.source_list_release(sources)

    obs.obs_properties_add_text(props, "counter_prefix", "Prefix text",  obs.OBS_TEXT_DEFAULT)
    obs.obs_properties_add_text(props, "counter_suffix", "Suffix text",  obs.OBS_TEXT_DEFAULT)
    obs.obs_properties_add_int (props, "start_value",    "Start / Reset value", -9999, 9999, 1)
    obs.obs_properties_add_int (props, "step_size",      "Step size",           1,     999,  1)
    obs.obs_properties_add_int (props, "min_value",      "Minimum value",       -9999, 9999, 1)
    obs.obs_properties_add_int (props, "max_value",      "Maximum value",       -9999, 9999, 1)

    return props


def script_update(settings):
    global source_name, counter_prefix, counter_suffix
    global min_value, max_value, step_size, counter_value

    source_name    = obs.obs_data_get_string(settings, "source_name")
    counter_prefix = obs.obs_data_get_string(settings, "counter_prefix")
    counter_suffix = obs.obs_data_get_string(settings, "counter_suffix")
    step_size      = obs.obs_data_get_int   (settings, "step_size")
    min_value      = obs.obs_data_get_int   (settings, "min_value")
    max_value      = obs.obs_data_get_int   (settings, "max_value")

    # Apply start value only on first load / explicit change
    start = obs.obs_data_get_int(settings, "start_value")
    counter_value = max(min_value, min(start, max_value))

    update_text()


def script_load(settings):
    global hotkey_add_id, hotkey_sub_id, hotkey_reset_id

    hotkey_add_id = obs.obs_hotkey_register_frontend(
        "counter_increment", "Counter: Increment (+1)", on_increment
    )
    hotkey_sub_id = obs.obs_hotkey_register_frontend(
        "counter_decrement", "Counter: Decrement (-1)", on_decrement
    )
    hotkey_reset_id = obs.obs_hotkey_register_frontend(
        "counter_reset", "Counter: Reset", on_reset
    )

    # Restore saved hotkey bindings
    hotkey_save_array_add   = obs.obs_data_get_array(settings, "hotkey_add")
    hotkey_save_array_sub   = obs.obs_data_get_array(settings, "hotkey_sub")
    hotkey_save_array_reset = obs.obs_data_get_array(settings, "hotkey_reset")

    obs.obs_hotkey_load(hotkey_add_id,   hotkey_save_array_add)
    obs.obs_hotkey_load(hotkey_sub_id,   hotkey_save_array_sub)
    obs.obs_hotkey_load(hotkey_reset_id, hotkey_save_array_reset)

    obs.obs_data_array_release(hotkey_save_array_add)
    obs.obs_data_array_release(hotkey_save_array_sub)
    obs.obs_data_array_release(hotkey_save_array_reset)


def script_save(settings):
    hotkey_save_array_add   = obs.obs_hotkey_save(hotkey_add_id)
    hotkey_save_array_sub   = obs.obs_hotkey_save(hotkey_sub_id)
    hotkey_save_array_reset = obs.obs_hotkey_save(hotkey_reset_id)

    obs.obs_data_set_array(settings, "hotkey_add",   hotkey_save_array_add)
    obs.obs_data_set_array(settings, "hotkey_sub",   hotkey_save_array_sub)
    obs.obs_data_set_array(settings, "hotkey_reset", hotkey_save_array_reset)

    obs.obs_data_array_release(hotkey_save_array_add)
    obs.obs_data_array_release(hotkey_save_array_sub)
    obs.obs_data_array_release(hotkey_save_array_reset)


def script_unload():
    obs.obs_hotkey_unregister(on_increment)
    obs.obs_hotkey_unregister(on_decrement)
    obs.obs_hotkey_unregister(on_reset)
