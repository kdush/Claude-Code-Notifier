"""
Claude Code钩子集成模块
为PyPI用户提供完整的Claude Code集成功能
"""

from .installer import ClaudeHookInstaller
from .claude_hook import ClaudeHook

__all__ = ['ClaudeHookInstaller', 'ClaudeHook']