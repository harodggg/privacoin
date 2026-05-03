"""
承诺（Commitment）与打开（Open）。

在隐私币中：
1. 创建 Note → 计算 commitment → 发布到链上
2. 花费 Note → 提供 nullifier + 打开承诺的数据 + 证明
3. 验证者检查：承诺是否在树上 + nullifier 是否未用过

这里用一个简单的哈希承诺做演示。
"""
from note import Note
from utils import bytes_to_hex


def open_note(note: Note) -> dict:
    """"打开"一个 Note，暴露其内部数据用于验证"""
    return {
        "value": note.value,
        "owner": bytes_to_hex(note.owner),
        "rho": bytes_to_hex(note.rho),
        "r": bytes_to_hex(note.r),
    }


def verify_commitment(note: Note, claimed_cm: bytes) -> bool:
    """验证：给定 Note 的全部字段，计算承诺是否匹配"""
    computed = note.commitment()
    return computed == claimed_cm
