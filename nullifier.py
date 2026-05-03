"""
无效器（Nullifier）—— 防止双花攻击。

关键设计：
- 每个 Note 有唯一的 nullifier（由 owner + rho 计算得出）
- 花费时，将 nullifier 发布到链上
- 全网维护一个"已用 nullifier"集合
- 如果某个 nullifier 已存在，交易被拒绝（双花检测）

关键属性：
- 只要不知道 owner 的私钥，就无法计算 nullifier
- 即使知道承诺，也无法反推 nullifier（单向函数）
- 承诺和 nullifier 之间不可关联（linkability）

简化演示：nullifier = SHA256(owner_pkh || rho)
"""
from typing import Set
from note import Note
from utils import bytes_to_hex


class NullifierSet:
    """已使用 Nullifier 集合（全局状态）"""

    def __init__(self):
        self._nullifiers: Set[bytes] = set()

    def contains(self, nullifier: bytes) -> bool:
        """检查 nullifier 是否已被使用"""
        return nullifier in self._nullifiers

    def add(self, nullifier: bytes) -> bool:
        """添加 nullifier。返回 False 表示已存在（双花！）"""
        if nullifier in self._nullifiers:
            return False
        self._nullifiers.add(nullifier)
        return True

    def __len__(self) -> int:
        return len(self._nullifiers)

    def __repr__(self) -> str:
        return f"NullifierSet(size={len(self)})"
