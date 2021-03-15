import xbmcaddon
import xbmcgui


def rank_url_by_resolutionn(data):
    # data is in the format of (name, url)
    if "1080p" in data[0]:
        return 1
    elif "720p" in data[0]:
        return 2
    elif "360p" in data[0]:
        return 3
    return 4


def get_version_string():
    return xbmcaddon.Addon().getSetting("auto_select_version_string").lower().strip()


def settings_is_set(setting):
    return (
        xbmcaddon.Addon().getSetting("auto_select_master_switch") == "true"
        and xbmcaddon.Addon().getSetting(setting) == "true"
    )

