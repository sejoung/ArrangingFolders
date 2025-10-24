# Scripts/OrganizeAssetsPy/menu.py
import unreal

import organize_assets
from utils import _log

DEFAULT_PER_MESH = False  # 메시별 하위 폴더 생성 여부


def _get_selected_content_path() -> str:
    selected_path = unreal.EditorUtilityLibrary.get_current_content_browser_path()
    if selected_path:
        _log(f"selected content path: {selected_path}")
        return str(selected_path)
    else:
        raise Exception("NOT FOUND PATH")


def _run():
    src = _get_selected_content_path()
    unreal.log(f"[OrganizeAssetsPy] src={src}  per_mesh={DEFAULT_PER_MESH}")

    if not _confirm(src):
        unreal.log("사용자가 취소했습니다.")
    else:
        organize_assets.run(
            source_root=src,
            per_mesh_subfolder=DEFAULT_PER_MESH
        )


def _confirm(path: str) -> bool:
    message = f"{path} will be modified.\nThis action cannot be undone. Do you want to continue?"
    title_message = "Are you sure you want to proceed?"

    result = unreal.EditorDialog.show_message(
        title=title_message,
        message=message,
        message_type=unreal.AppMsgType.YES_NO,  # 버튼 구성
        default_value=unreal.AppReturnType.NO  # 기본 선택
    )
    return result == unreal.AppReturnType.YES


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
        string="import menu as M; M._run()"
    )
    cb_menu.add_menu_entry(section_name, e3)

    menus.refresh_all_widgets()
