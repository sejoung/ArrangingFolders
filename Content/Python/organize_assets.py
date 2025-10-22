from typing import Set, List, Tuple, Optional

import unreal


# ─────────────────────────────────────────────────────────
# 내부 유틸
def _log(s: str): unreal.log(s)


def _warn(s: str): unreal.log_warning(s)


def _err(s: str): unreal.log_error(s)


def _pkg_join(*parts: str) -> str:
    p = "/".join(x.strip("/") for x in parts if x)
    return p if p.startswith("/") else "/" + p


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


def _move_asset(obj_path: str, dst_pkg_path: str) -> Optional[str]:
    ad = unreal.EditorAssetLibrary.find_asset_data(obj_path)
    if not ad:
        _warn(f"[Skip] Not found: {obj_path}")
        return None
    new_obj_path = _unique_move_path(dst_pkg_path, str(ad.asset_name))
    ad = unreal.EditorAssetLibrary.find_asset_data(obj_path)
    uobj = ad.get_asset()
    new_name = _unique_name_in(dst_pkg_path, str(ad.asset_name))

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


# 텍스처 수집 (머티리얼/MI 모두 지원)
_TextureExpr = (
    unreal.MaterialExpressionTextureSample,
    unreal.MaterialExpressionTextureSampleParameter,
    unreal.MaterialExpressionTextureSampleParameter2D,
    unreal.MaterialExpressionTextureSampleParameterCube,
    unreal.MaterialExpressionTextureSampleParameterSubUV,
    unreal.MaterialExpressionTextureObject,
    unreal.MaterialExpressionTextureObjectParameter
)


def collect_textures(mi_or_mat: unreal.MaterialInterface) -> Set[unreal.Texture]:
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
                out |= collect_textures(parent)
        except Exception:
            pass
    return out


def staticmesh_materials(sm: unreal.StaticMesh) -> List[unreal.MaterialInterface]:
    out: List[unreal.MaterialInterface] = []
    try:
        for smat in sm.get_editor_property("static_materials"):
            if smat.material_interface:
                out.append(smat.material_interface)
    except Exception:
        pass
    return out


# ─────────────────────────────────────────────────────────
# 공개 API
def run(source_root: str,
        dest_root: str,
        per_mesh_subfolder: bool = True) -> int:
    """
    source_root: '/Game/...'
    dest_root  : '/Game/...'
    per_mesh_subfolder: True면 DEST/<SM_Name>/Meshes|Materials|Textures 로 정리
    Return: 이동(또는 계획)된 항목 수(대략치)
    """
    if not source_root.startswith("/Game"):
        _err("source_root must start with /Game")
        return 0
    if not dest_root.startswith("/Game"):
        _err("dest_root must start with /Game")
        return 0

    ads = _list_assets(source_root)
    if not ads:
        _warn(f"No StaticMesh under {source_root}")
        return 0

    _log(f"=== Organize StaticMeshes: {len(ads)} found ===")
    staticmesh_move_plan: List[Tuple[str, str]] = []
    materials_move_plan: List[Tuple[str, str]] = []
    textures_move_plan: List[Tuple[str, str]] = []

    # 계획 생성
    for ad in ads:
        sm = ad.get_asset()
        if not isinstance(sm, unreal.StaticMesh):
            continue

        sm_name = str(ad.asset_name)
        if per_mesh_subfolder:
            root = _pkg_join(dest_root, sm_name)
            dst_meshes = _pkg_join(root, "Meshes")
            dst_mats = _pkg_join(root, "Materials")
            dst_texs = _pkg_join(root, "Textures")
        else:
            dst_meshes = _pkg_join(dest_root, "Meshes")
            dst_mats = _pkg_join(dest_root, "Materials")
            dst_texs = _pkg_join(dest_root, "Textures")

        for p in (dst_meshes, dst_mats, dst_texs):
            _ensure_dir(p)

        # StaticMesh
        staticmesh_move_plan.append((sm.get_path_name(), dst_meshes))

        # Materials & Textures
        for mi in staticmesh_materials(sm):
            materials_move_plan.append((mi.get_path_name(), dst_mats))
            for tex in collect_textures(mi):
                _log(f"textures {tex.get_path_name()}")
                textures_move_plan.append((tex.get_path_name(), dst_texs))

    # 실제 이동
    moved = 0
    for src, dst in textures_move_plan:
        if _move_asset(src, dst):
            moved += 1

    for src, dst in materials_move_plan:
        if _move_asset(src, dst):
            moved += 1

    for src, dst in staticmesh_move_plan:
        if _move_asset(src, dst):
            moved += 1

    _log(f"=== Done === moved={moved}, destination={dest_root}")
    return moved
