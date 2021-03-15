import xbmcaddon
import xbmcgui

SOURCE_PREFERENCE = None


def retrieve_rank_source_preference():
    """Retrieve source preference from settings."""
    global SOURCE_PREFERENCE
    if SOURCE_PREFERENCE is None:
        preference = xbmcaddon.Addon().getSetting("auto_select_source_preference").lower().strip()
        SOURCE_PREFERENCE =                     [pref for pref in map(lambda x: x.strip().lower(), preference.split(',')) if pref != '']


def rank_url_by_preference(data):
    global SOURCE_PREFERENCE
    if SOURCE_PREFERENCE is None:
        retrieve_rank_source_preference()
    # data is in the format of (name, url)
    no_pref = len(SOURCE_PREFERENCE) # max length of preference list
    for i, pref in enumerate(SOURCE_PREFERENCE):
        if pref in data[0].lower():
            return i
    return no_pref


def get_version_string():
    return xbmcaddon.Addon().getSetting("auto_select_version_string").lower().strip()


def settings_is_set(setting):
    return (
        xbmcaddon.Addon().getSetting("auto_select_master_switch") == "true"
        and xbmcaddon.Addon().getSetting(setting) == "true"
    )

