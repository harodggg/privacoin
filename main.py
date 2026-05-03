#!/usr/bin/env python3
"""
Privacoin — 隐私币端到端演示。

模拟 Zcash 风格的隐私交易流程：

1. Alice 收到一笔铸币（相当于挖矿产出）
2. Alice 向 Bob 发送一笔隐私交易
3. 验证交易：双花检测 + Merkle 证明 + 余额守恒
4. Bob 查询自己的余额
"""
from note import Note
from ledger import Ledger
from transaction import (
    ShieldedTransaction, ShieldedOutput,
    verify_transaction,
)
from utils import random_bytes, bytes_to_hex, format_amount


def print_sep(title: str):
    print()
    print("=" * 60)
    print(f"  {title}")
    print("=" * 60)


def main():
    print()
    print("  ╔══════════════════════════════════════╗")
    print("  ║      Privacoin · 隐私币演示          ║")
    print("  ╚══════════════════════════════════════╝")

    # 初始化全局账本
    ledger = Ledger()

    # =============================================
    # Step 1: 身份生成
    # =============================================
    print_sep("第 1 步：生成身份（地址）")

    # 简化：用随机哈希作为"公钥哈希"（类似比特币地址）
    alice_pkh = random_bytes(20)
    bob_pkh = random_bytes(20)

    print(f"  Alice 地址: {bytes_to_hex(alice_pkh)}")
    print(f"  Bob 地址:   {bytes_to_hex(bob_pkh)}")

    # =============================================
    # Step 2: 铸币 —— Alice 收到 100 枚币
    # =============================================
    print_sep("第 2 步：铸币 —— Alice 收到 100 枚币")

    alice_note = Note.create(value=100, owner_pkh=alice_pkh)
    leaf_idx = ledger.mint(alice_note)

    cm = alice_note.commitment()
    nf = alice_note.nullifier()

    print(f"  Note 承诺 (链上):  {bytes_to_hex(cm)}")
    print(f"  Note 无效器 (秘密): {bytes_to_hex(nf)}")
    print(f"  Note 在树中位置:   {leaf_idx}")
    print(f"  Alice 余额:        {format_amount(ledger.balance(alice_pkh))}")
    print(f"  链上 Note 总数:    {len(ledger._unspent_notes)}")

    print()
    print(f"  🔐 关键点：链上只存了承诺 {bytes_to_hex(cm)}")
    print(f"  🔐 没人知道这个承诺代表 100 枚币，也不知道属于 Alice")

    # =============================================
    # Step 3: Alice 向 Bob 发送 40 枚币
    # =============================================
    print_sep("第 3 步：Alice 向 Bob 发送 40 枚币（隐私交易）")

    # 3a. 零钱 Note（Alice 找零 60 枚）
    change_note = Note.create(value=60, owner_pkh=alice_pkh)

    # 3b. 给 Bob 的 Note（40 枚）
    bob_note = Note.create(value=40, owner_pkh=bob_pkh)

    # 3c. 构建屏蔽交易
    tx = ShieldedTransaction()

    # 花费 Alice 的原始 Note
    tx.add_spend(alice_note, ledger.tree, leaf_idx)

    # 输出两个新 Note
    output_change = tx.add_output(change_note)
    output_bob = tx.add_output(bob_note)

    print(f"  交易: {tx}")
    print(f"  输入: 1 个 Note (100 枚)")
    print(f"       {bytes_to_hex(tx.spends[0].nullifier)}")
    print(f"  输出: 2 个新 Note")
    print(f"       输出 0 (Alice找零): {bytes_to_hex(output_change.commitment)}")
    print(f"       输出 1 (给Bob):      {bytes_to_hex(output_bob.commitment)}")
    print()
    print(f"  🔐 观察者只能看到：")
    print(f"     - 有人花了一个 Note（nullifier）")
    print(f"     - 产生了 2 个新承诺")
    print(f"     - ❌ 不知道金额")
    print(f"     - ❌ 不知道发送方/接收方")

    # =============================================
    # Step 4: 验证交易
    # =============================================
    print_sep("第 4 步：全网验证交易")

    valid, msg = verify_transaction(tx, ledger.tree, ledger.nullifiers)
    print(f"  结果: {msg}")

    if not valid:
        print("  ❌ 交易不合法！")
        return

    # =============================================
    # Step 5: 更新链上状态
    # =============================================
    print_sep("第 5 步：更新链上状态")

    # 标记 nullifier 已使用（防双花）
    for spend in tx.spends:
        ledger.spend(spend.note)

    # 将新 Note 的承诺添加到 Merkle 树
    idx_change = ledger.mint(change_note)
    idx_bob = ledger.mint(bob_note)

    print(f"  Alice 找零 Note → 树位置 {idx_change}")
    print(f"  Bob 的 Note     → 树位置 {idx_bob}")

    # =============================================
    # Step 6: 查询余额
    # =============================================
    print_sep("第 6 步：查询余额")

    alice_balance = ledger.balance(alice_pkh)
    bob_balance = ledger.balance(bob_pkh)

    print(f"  Alice 余额: {format_amount(alice_balance)}")
    print(f"  Bob 余额:   {format_amount(bob_balance)}")

    # =============================================
    # Step 7: 双花攻击检测
    # =============================================
    print_sep("第 7 步：双花攻击检测")

    # 尝试再次使用同一个 Note（双花攻击）
    double_spend_tx = ShieldedTransaction()
    double_spend_tx.add_spend(alice_note, ledger.tree, leaf_idx)

    valid2, msg2 = verify_transaction(
        double_spend_tx, ledger.tree, ledger.nullifiers
    )
    print(f"  重放旧 Note: {msg2}")
    if not valid2:
        print("  ✅ 双花攻击被成功拦截！")

    # =============================================
    # Summary
    # =============================================
    print_sep("总结")
    print(f"  📦 链上 Note 承诺数: {ledger.tree._leaf_count}")
    print(f"  🚫 已用 Nullifier 数: {len(ledger.nullifiers)}")
    print(f"  💰 有效 Note (未花费): {len(ledger._unspent_notes)}")
    print(f"  🔐 隐私属性: ✓ 金额机密  ✓ 发送方/接收方匿名")
    print(f"                ✓ 双花防护  ✓ 交易不可追溯")
    print()

    print("  ⚠️  免责声明：这是教学演示，不是真 zk-SNARKs。")
    print("     真实 Zcash 使用更先进的零知识证明来保证隐私。")
    print()


if __name__ == "__main__":
    main()
