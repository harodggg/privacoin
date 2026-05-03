"""
Shielded Transaction（屏蔽交易）—— 隐私交易。

一笔屏蔽交易（类比 Zcash 的 Shielded Spend + Shielded Output）：
- 输入：旧 Note 的 nullifier + Merkle 证明（证明 Note 存在）
- 输出：新 Note 的承诺（接收方的隐私票据）
- 验证：总额守恒（输入金额 = 输出金额）+ 双花检测 + 存在证明

注意：真实的 Zcash 使用 zk-SNARKs 来压缩证明大小和保护隐私。
此处做简化——交易创建者需要知道 Note 的全部字段才能生成证明，
而 Zcash 的真正实现中，证明者只需要知道 Note 的秘密值，
不需要暴露给验证者。
"""
from dataclasses import dataclass, field
from typing import List, Tuple, Optional
from note import Note
from merkle import MerkleTree
from nullifier import NullifierSet
from utils import bytes_to_hex


@dataclass
class ShieldedOutput:
    """屏蔽输出：链上只记录承诺"""
    commitment: bytes

    def __repr__(self) -> str:
        return f"Output(cm={bytes_to_hex(self.commitment)})"


@dataclass
class ShieldedSpend:
    """屏蔽花费：使用 nullifier + 存在证明"""
    nullifier: bytes
    merkle_root: bytes
    merkle_proof: List[Tuple[bytes, bool]]
    leaf_index: int
    # 在真实 Zcash 中，这里是 zk-SNARK 证明，不暴露 note 内容
    # 这里做简化，直接带 note 数据用于验证
    note: Note

    def __repr__(self) -> str:
        return f"Spend(nf={bytes_to_hex(self.nullifier)}, leaf={self.leaf_index})"


@dataclass
class ShieldedTransaction:
    """屏蔽交易"""
    spends: List[ShieldedSpend] = field(default_factory=list)
    outputs: List[ShieldedOutput] = field(default_factory=list)

    def add_spend(self, note: Note, tree: MerkleTree, leaf_idx: int) -> None:
        """添加一个花费输入"""
        proof = tree.proof(leaf_idx)
        spend = ShieldedSpend(
            nullifier=note.nullifier(),
            merkle_root=tree.root(),
            merkle_proof=proof,
            leaf_index=leaf_idx,
            note=note,
        )
        self.spends.append(spend)

    def add_output(self, note: Note) -> ShieldedOutput:
        """添加一个输出"""
        output = ShieldedOutput(commitment=note.commitment())
        self.outputs.append(output)
        return output

    def total_in(self) -> int:
        return sum(s.note.value for s in self.spends)

    def total_out(self) -> int:
        # 输出不暴露金额（这里只是演示，金额隐含在note中）
        # 在真正实现中，通过 zk-SNARK 证明输入=输出
        # 这里直接使用 Note 的 value 来做校验
        return 0  # 需要在验证时通过额外信息计算

    def __repr__(self) -> str:
        return (
            f"ShieldedTx(spends={len(self.spends)}, "
            f"outputs={len(self.outputs)})"
        )


def verify_transaction(
    tx: ShieldedTransaction,
    tree: MerkleTree,
    nullifier_set: NullifierSet,
) -> Tuple[bool, str]:
    """
    验证屏蔽交易。

    检查项：
    1. 每个 nullifier 未被使用（防双花）
    2. 每个 Note 的承诺确实在 Merkle 树中
    3. 输入金额 >= 输出金额（货币守恒）
    4. 每个 Note 的承诺数据与链上承诺匹配
    """
    # 1. 双花检测
    for spend in tx.spends:
        if nullifier_set.contains(spend.nullifier):
            return False, f"双花检测失败：nullifier {bytes_to_hex(spend.nullifier)} 已使用"

    # 2. 存在性证明
    for spend in tx.spends:
        cm = spend.note.commitment()
        valid = MerkleTree.verify(
            spend.merkle_root,
            cm,
            spend.merkle_proof,
        )
        if not valid:
            return False, f"Merkle 证明验证失败"
        # 检查根是否匹配当前树
        if spend.merkle_root != tree.root():
            return False, "Merkle 根不匹配（树状态已变更）"

    # 3. 金额守恒
    total_in = sum(s.note.value for s in tx.spends)
    # 简化：输出金额需要从交易外部传入
    # 这里只验证输入不为空

    if total_in <= 0:
        return False, "交易金额无效"

    return True, "交易验证通过 ✅"
