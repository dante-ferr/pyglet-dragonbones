from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .skeleton import Skeleton
    from .bone import Bone
    from .slot import Slot


class SkeletonStructureManager:
    def __init__(self, skeleton: "Skeleton"):
        self.skeleton = skeleton
        self.bones = self._load_bones()
        self.slots = None

        if self.skeleton.render:
            from .subtexture_manager import SubtextureManager

            self.subtexture_manager = SubtextureManager(self.skeleton)

            slot_skin = self.skeleton.armature_data["skin"][0]["slot"]
            self.slots = self._load_slots(
                (self.skeleton.armature_data["slot"], slot_skin)
            )

    def _load_bones(self) -> dict[str, "Bone"]:
        from .bone import Bone

        data = self.skeleton.armature_data["bone"]
        bones: dict[str, "Bone"] = {}

        bone_parent_names: dict[str, str] = {}
        for b in data:
            bone_name = b["name"]
            bone_group = (
                self.skeleton.groups.get(bone_name) if self.skeleton.groups else None
            )

            bone = Bone(b, self.skeleton, bone_group)
            bones[bone_name] = bone

            if "parent" in b:
                bone_parent_names[bone_name] = b["parent"]

        for bone_name, parent_name in bone_parent_names.items():
            bones[bone_name].parent = bones[parent_name]

        return bones

    def _load_slots(self, data) -> dict[str, "Slot"]:
        from .slot import Slot

        slots: dict[str, "Slot"] = {}
        slot_data, skin_data = data

        for slot_info in slot_data:
            slot_displays = next(
                (s.get("display") for s in skin_data if s["name"] == slot_info["name"]),
                None,
            )

            if not slot_displays:
                continue

            subtextures = [
                self.subtexture_manager.subtextures[display["name"]]
                for display in slot_displays
            ]
            bone = self.bones[slot_info["parent"]]
            slots[slot_info["name"]] = Slot(
                slot_info, bone=bone, subtextures=subtextures, batch=self.skeleton.batch
            )

        return slots
