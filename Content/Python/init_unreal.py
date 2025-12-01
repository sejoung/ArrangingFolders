import unreal

from am_menu import register_menus


def _startup():
    try:
        register_menus()
        unreal.log("[OrganizeAssetsPy] Menus registered")
    except Exception as e:
        unreal.log_error(f"[OrganizeAssetsPy] Menu registration failed: {e}")


_startup()
