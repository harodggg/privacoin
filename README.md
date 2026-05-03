# Privacoin — 隐私币原型

> 一个教学性质、受 Zcash 启发的隐私保护加密货币原型。
> 用 Python 实现，演示了**零知识证明思想的简化版本**以及**链上隐私交易**的核心机制。

## 核心理念

Zcash 的隐私基于 **shielded transactions（屏蔽交易）** ——
交易金额和发送方/接收方地址对全网不可见，但通过密码学证明其合法性。

本项目实现了以下关键概念：

| 概念 | 说明 |
|---|---|
| **Note（票据）** | 拥有者、金额、随机数构成的隐私单元 |
| **Commitment（承诺）** | Note 的哈希值，发布到链上，不暴露 Note 内容 |
| **Nullifier（无效器）** | 花费 Note 时发布的唯一值，防止双花 |
| **Merkle Tree** | 存储所有承诺，用于验证 Note 是否存在于链上 |
| **Merkle Proof** | 证明某个承诺在树中而不暴露其位置 |
| **Shielded Transaction** | 输入 = 旧 Note 的 nullifier + proof；输出 = 新 Note 的 commitment |

## 快速开始

```bash
python3 main.py
```

## 架构

```
privacoin/
├── main.py          # 入口：演示完整交易流程
├── note.py          # Note（票据）结构
├── commitment.py    # 承诺与打开
├── nullifier.py     # 无效器生成
├── merkle.py        # Merkle 树与证明
├── transaction.py   # 交易构建与验证
├── ledger.py        # 简易账本
└── utils.py         # 杂项工具
```

## 隐私性说明

- ❌ **NOT production-ready** — 仅供学习
- ❌ 不是真正的 zk-SNARKs（故有限隐私保护）
- ✅ 清晰展示了 Zcash 的核心数据结构和交易流程

## 参考

- [Zcash Protocol Specification](https://zips.z.cash/protocol/protocol.pdf)
- ["Why Zcash is Different" by Zcash Foundation](https://z.cash/technology/)
