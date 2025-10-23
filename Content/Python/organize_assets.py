from typing import List, Tuple

import unreal

from unreal_file_utils import _list_assets, _pkg_join, _ensure_dir, _static_mesh_materials, _collect_textures, \
    _move_asset
from utils import _log, _warn, _err


def run(source_root: str,
        per_mesh_subfolder: bool = True) -> int:
    if not source_root.startswith("/Game"):
        _err("source_root must start with /Game")
        return 0

    ads = _list_assets(source_root)
    if not ads:
        _warn(f"No StaticMesh under {source_root}")
        return 0

    dest_root = source_root
    _log(f"=== Organize StaticMeshes: {len(ads)} found ===")
    static_mesh_move_plan: List[Tuple[str, str]] = []
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
            dst_textures = _pkg_join(root, "Textures")
        else:
            dst_meshes = _pkg_join(dest_root, "Meshes")
            dst_mats = _pkg_join(dest_root, "Materials")
            dst_textures = _pkg_join(dest_root, "Textures")

        for p in (dst_meshes, dst_mats, dst_textures):
            _ensure_dir(p)

        # StaticMesh
        static_mesh_move_plan.append((sm.get_path_name(), dst_meshes))

        # Materials & Textures
        for mi in _static_mesh_materials(sm):
            materials_move_plan.append((mi.get_path_name(), dst_mats))
            for tex in _collect_textures(mi):
                textures_move_plan.append((tex.get_path_name(), dst_textures))

    moved = 0
    for src, dst in textures_move_plan:
        if _move_asset(src, dst):
            moved += 1

    for src, dst in materials_move_plan:
        if _move_asset(src, dst):
            moved += 1

    for src, dst in static_mesh_move_plan:
        if _move_asset(src, dst):
            moved += 1

    _log(f"=== Done === moved={moved}, destination={dest_root}")
    return moved
