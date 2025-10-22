# Scripts/OrganizeAssetsPy/menu.py
import unreal

DEFAULT_DEST_ROOT = "/Game/Organized"  # 목적지 기본값
DEFAULT_PER_MESH = False  # 메시별 하위 폴더 생성 여부


def _get_selected_content_path() -> str:
    return "/Game/test"


def _run(dry_run: bool):
    src = _get_selected_content_path()
    dst = src
    unreal.log(f"[OrganizeAssetsPy] src={src}  dst={dst}  dry={dry_run}  per_mesh={DEFAULT_PER_MESH}")

    import organize_assets
    count = organize_assets.run(
        source_root=src,
        dest_root=dst,
        dry_run=dry_run,
        per_mesh_subfolder=DEFAULT_PER_MESH
    )
    unreal.EditorDialog.show_message(
        title="Organize (Done)",
        message=f"Moved items: {count}\nSource: {src}\nDest: {dst}",
        message_type=unreal.AppMsgType.OK
    )


def _run_dry(_ctx=None):
    _run(dry_run=True)


def _run_real(_ctx=None):
    _run(dry_run=False)


def register_menus():
    menus = unreal.ToolMenus.get()

    # 2) Content Browser 폴더 우클릭 메뉴
    cb_menu = menus.extend_menu("ContentBrowser.FolderContextMenu")
    section_name = "ArrangingFolder"
    cb_menu.add_section(section_name, "Organize Assets (Python)")

    e3 = unreal.ToolMenuEntry(
        name="ArrangingFolder.CB.Run",
        type=unreal.MultiBlockType.MENU_ENTRY
    )
    e3.set_label("Arranging Folder")
    e3.set_string_command(
        type=unreal.ToolMenuStringCommandType.PYTHON,
        custom_type="",
        string="import menu as M; M._run_real()"
    )
    cb_menu.add_menu_entry(section_name, e3)

    menus.refresh_all_widgets()
