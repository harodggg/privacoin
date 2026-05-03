"""
Merkle 树 —— 存储 Note 承诺的全局树。

Zcash 使用 Merkle 树来：
1. 累积所有 Note 承诺（链上公共状态）
2. 让花费者能证明"我的 Note 确实存在"而不暴露树中的位置
3. 支持注资（树不断增长）

这个实现演示了：
- Merkle 树的构建
- Merkle 路径（Merkle Proof）的生成
- 利用路径验证承诺的存在
"""
from typing import List, Tuple
from utils import hash_pair, bytes_to_hex, EMPTY_HASH


class MerkleTree:
    """简易 Merkle 树（固定深度，用空哈希填充）"""

    DEPTH = 5  # 2^5 = 32 个叶子节点，演示够用

    def __init__(self):
        self.leaves: List[bytes] = [EMPTY_HASH] * self.num_leaves
        self._leaf_count = 0
        self._build_full_tree()

    @property
    def num_leaves(self) -> int:
        return 1 << self.DEPTH

    def _build_full_tree(self):
        """从叶子向上构建所有内部节点（全部用 EMPTY_HASH 填充）"""
        self.nodes: List[List[bytes]] = []
        self.nodes.append(list(self.leaves))
        for level in range(1, self.DEPTH + 1):
            prev = self.nodes[level - 1]
            current = []
            for i in range(0, len(prev), 2):
                current.append(hash_pair(prev[i], prev[i + 1]))
            self.nodes.append(current)

    def add_leaf(self, commitment: bytes) -> int:
        """添加一个承诺叶子，返回索引"""
        if self._leaf_count >= self.num_leaves:
            raise RuntimeError("Merkle 树已满")

        idx = self._leaf_count
        self.leaves[idx] = commitment
        self.nodes[0][idx] = commitment
        self._leaf_count += 1

        # 向上更新路径
        cur_idx = idx
        for level in range(1, self.DEPTH + 1):
            parent_idx = cur_idx // 2
            left = self.nodes[level - 1][parent_idx * 2]
            right = self.nodes[level - 1][parent_idx * 2 + 1]
            self.nodes[level][parent_idx] = hash_pair(left, right)
            cur_idx = parent_idx

        return self._leaf_count - 1

    def root(self) -> bytes:
        """获取当前树根（Merkle Root）"""
        return self.nodes[self.DEPTH][0]

    def proof(self, leaf_idx: int) -> List[Tuple[bytes, bool]]:
        """
        生成 Merkle 证明（认证路径）。
        返回 [(兄弟哈希, is_left), ...]
        is_left = True 表示兄弟节点在左边
        """
        path = []
        idx = leaf_idx
        for level in range(self.DEPTH):
            sibling_idx = idx ^ 1
            sibling = self.nodes[level][sibling_idx]
            path.append((sibling, sibling_idx % 2 == 0))
            idx //= 2
        return path

    @staticmethod
    def verify(root: bytes, leaf: bytes, proof: List[Tuple[bytes, bool]]) -> bool:
        """验证 Merkle 证明"""
        current = leaf
        for sibling, is_left in proof:
            if is_left:
                current = hash_pair(sibling, current)
            else:
                current = hash_pair(current, sibling)
        return current == root

    def __repr__(self) -> str:
        return (
            f"MerkleTree(leaves={self._leaf_count}/{self.num_leaves}, "
            f"root={bytes_to_hex(self.root())})"
        )
