from typing import Set, List, Optional

import unreal

from utils import _warn


def _pkg_join(*parts: str) -> str:
    p = "/".join(x.strip("/") for x in parts if x)
    return p if p.startswith("/") else "/" + p


def is_engine(path: str) -> bool:
    unreal.log(f"is_engine {path}")
    if not path.startswith("/Engine"):
        return False
    return True


def _ensure_dir(path: str):
    if not unreal.EditorAssetLibrary.does_directory_exist(path):
        unreal.EditorAssetLibrary.make_directory(path)


def _list_assets(root: str) -> List[unreal.AssetData]:
    arm = unreal.AssetRegistryHelpers.get_asset_registry()
    flt = unreal.ARFilter(package_paths=[unreal.Name(root)], recursive_paths=True,
                          class_paths=[unreal.StaticMesh.static_class().get_class_path_name()]
                          )
    return arm.get_assets(flt)


def _unique_move_path(dst_pkg_path: str, desired_name: str) -> str:
    base = desired_name
    name = base
    i = 1
    while True:
        obj_path = f"{dst_pkg_path}/{name}"
        if not unreal.EditorAssetLibrary.does_asset_exist(obj_path):
            return obj_path
        i += 1
        name = f"{base}_{i:03d}"


def _unique_name_in(dst_pkg_path: str, desired_name: str) -> str:
    name = desired_name
    i = 1
    while True:
        if not unreal.EditorAssetLibrary.does_asset_exist(f"{dst_pkg_path}/{name}"):
            return name
        i += 1
        name = f"{desired_name}_{i:03d}"


def _get_asset_name(ad: unreal.AssetData) -> str:
    uobj = ad.get_asset()

    if isinstance(uobj, unreal.Material):
        kind = "M_"
    elif isinstance(uobj, unreal.MaterialInstanceConstant):
        kind = "MI_"
    elif isinstance(uobj, unreal.StaticMesh):
        kind = "SM_"
    elif isinstance(uobj, unreal.Texture):
        kind = "T_"
    else:
        kind = ""

    asset_name = str(ad.asset_name)
    index = asset_name.find(kind)

    if index != 0:
        return kind + asset_name
    else:
        return asset_name


def _move_asset(obj_path: str, dst_pkg_path: str) -> Optional[str]:
    ad = unreal.EditorAssetLibrary.find_asset_data(obj_path)
    if not ad or is_engine(obj_path):
        _warn(f"[Skip] Not found: {obj_path}")
        return None

    new_obj_path = _unique_move_path(dst_pkg_path, str(ad.asset_name))
    new_asset_name = _get_asset_name(ad)

    new_name = _unique_name_in(dst_pkg_path, new_asset_name)
    uobj = ad.get_asset()
    rename_data = unreal.AssetRenameData(uobj, dst_pkg_path, new_name)
    tools = unreal.AssetToolsHelpers.get_asset_tools()
    ok = tools.rename_assets([rename_data])

    # 변경분 저장(선택)
    try:
        unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
    except Exception:
        pass

    if not ok:
        _warn(f"[Move Failed] {obj_path} -> {new_obj_path}")
        return None
    return new_obj_path


def _collect_textures(mi_or_mat: unreal.MaterialInterface) -> Set[unreal.Texture]:
    """
    UMaterial / UMaterialInstance 모두 지원.
    에디터 전용 expressions에 의존하지 않고, 엔진 제공 API로 텍스처 집계.
    """
    out: Set[unreal.Texture] = set()
    try:
        # UE 5.x: MaterialEditingLibrary.get_used_textures 가 MI 포함 전체 텍스처를 반환
        # (파라미터 텍스처/TextureObject/샘플 등 모두 커버)
        tex_list = unreal.MaterialEditingLibrary.get_used_textures(mi_or_mat)
        for t in tex_list:
            if isinstance(t, unreal.Texture):
                out.add(t)
        return out
    except Exception:
        pass

    # 예비: MI의 파라미터에서만이라도 수집
    if isinstance(mi_or_mat, unreal.MaterialInstance):
        try:
            for tp in mi_or_mat.get_editor_property("texture_parameter_values"):
                if isinstance(tp.parameter_value, unreal.Texture):
                    out.add(tp.parameter_value)
        except Exception:
            pass
        # 부모 따라 올라가며 한번 더 시도
        try:
            parent = mi_or_mat.get_editor_property("parent")
            if parent:
                out |= _collect_textures(parent)
        except Exception:
            pass
    return out


def _static_mesh_materials(sm: unreal.StaticMesh) -> List[unreal.MaterialInterface]:
    out: List[unreal.MaterialInterface] = []
    try:
        for smat in sm.get_editor_property("static_materials"):
            if smat.material_interface:
                out.append(smat.material_interface)
    except Exception:
        pass
    return out
