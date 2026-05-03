"""工具函数"""
import hashlib
import os

def sha256(data: bytes) -> bytes:
    """SHA-256 哈希"""
    return hashlib.sha256(data).digest()

def random_bytes(n: int = 32) -> bytes:
    """生成安全的随机字节"""
    return os.urandom(n)

def hash_pair(a: bytes, b: bytes) -> bytes:
    """Merkle 树中哈希左右子节点"""
    return sha256(a + b)

def int_to_bytes(value: int, length: int = 8) -> bytes:
    """整数转定长字节"""
    return value.to_bytes(length, 'big')

def bytes_to_hex(data: bytes) -> str:
    """字节转十六进制字符串（缩短显示）"""
    return data.hex()[:16] + "..." if len(data) > 16 else data.hex()

def format_amount(amount: int) -> str:
    """格式化金额（最小单位）"""
    return f"{amount} 聪"


# Merkle 树空占位哈希
EMPTY_HASH = sha256(b"")
