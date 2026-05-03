"""
Note（票据）—— Zcash 中隐私交易的核心单元。

一个 Note 包含：
- value:   金额（整数）
- owner:   拥有者的公钥哈希（谁可以花这笔钱）
- rho:     唯一随机数，防止 Note 重复
- r:       另一个随机数，用于承诺的盲化

Note 本身永远不会公开上链。链上只存它的承诺（commitment）。
"""
from dataclasses import dataclass
from typing import Optional
from utils import random_bytes, int_to_bytes, sha256, bytes_to_hex


@dataclass
class Note:
    """隐私票据"""
    value: int
    owner: bytes       # 拥有者公钥哈希（20 字节，类似比特币的地址哈希）
    rho: bytes         # 唯一标识随机数
    r: bytes           # 盲化因子

    @staticmethod
    def create(value: int, owner_pkh: bytes) -> 'Note':
        """创建一个新 Note"""
        return Note(
            value=value,
            owner=owner_pkh,
            rho=random_bytes(32),
            r=random_bytes(32),
        )

    def commitment(self) -> bytes:
        """计算 Note 的承诺（链上可见）

        commitment = SHA256(value || owner || rho || r)
        
        注意：真正的 Zcash 使用 Pedersen 承诺 + 同态加密，
        这里用哈希做简化演示。
        """
        data = (
            int_to_bytes(self.value) +
            self.owner +
            self.rho +
            self.r
        )
        return sha256(data)

    def nullifier(self) -> Optional[bytes]:
        """生成无效器（花费 Note 时使用）

        nullifier = SHA256(owner || rho)
        
        只有拥有者（知道 owner 私钥的人）才能计算 nullifier。
        这样全网可用 nullifier 检测双花，但无法追溯到具体 Note。
        """
        return sha256(self.owner + self.rho)

    def __repr__(self) -> str:
        return (
            f"Note(value={self.value}, "
            f"owner={bytes_to_hex(self.owner)}, "
            f"cm={bytes_to_hex(self.commitment())})"
        )
