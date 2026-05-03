"""
简易账本 —— 维护全局状态。

真实场景中这就是"区块链"：
- Merkle 树（存储所有 Note 承诺）
- Nullifier 集合（存储所有已花费的 Note 的 nullifier）
- 未花费 Note 的记录（方便演示查找余额）

注意：真正的全节点不会存储未花费 Note 的内容
（因为隐私性！），只有 Note 的拥有者才知道自己的 Note。
"""
from typing import List, Optional, Dict
from note import Note
from merkle import MerkleTree
from nullifier import NullifierSet
from transaction import (
    ShieldedTransaction, verify_transaction,
    ShieldedOutput, ShieldedSpend,
)
from utils import bytes_to_hex


class Ledger:
    """隐私账本"""

    def __init__(self):
        self.tree = MerkleTree()
        self.nullifiers = NullifierSet()
        # 以下仅用于演示：记录未花费 Note 及其位置
        # 真实隐私币中，这是不存在的！
        self._unspent_notes: Dict[bytes, Note] = {}
        self._note_positions: Dict[bytes, int] = {}

    def mint(self, note: Note) -> int:
        """
        铸币：创建新的 Note（类似挖矿产出或接收转账）。
        返回 Note 在树中的位置。
        """
        cm = note.commitment()
        leaf_idx = self.tree.add_leaf(cm)
        self._unspent_notes[cm] = note
        self._note_positions[cm] = leaf_idx
        return leaf_idx

    def spend(self, note: Note) -> bool:
        """
        花费一个 Note。
        实际调用 verify_transaction + 更新状态的简化接口。
        """
        cm = note.commitment()
        if cm not in self._unspent_notes:
            return False

        leaf_idx = self._note_positions[cm]
        nf = note.nullifier()

        # 添加到 nullifier 集合
        if not self.nullifiers.add(nf):
            return False

        # 从未花费集合中移除
        del self._unspent_notes[cm]
        return True

    def balance(self, owner_pkh: bytes) -> int:
        """查询某个拥有者的余额（仅用于演示！）"""
        total = 0
        for cm, note in self._unspent_notes.items():
            if note.owner == owner_pkh:
                total += note.value
        return total

    def __repr__(self) -> str:
        return (
            f"Ledger(tree={self.tree}, "
            f"nullifiers={self.nullifiers}, "
            f"unspent={len(self._unspent_notes)})"
        )
