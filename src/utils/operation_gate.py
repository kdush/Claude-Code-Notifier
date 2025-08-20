#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
操作阻止机制 - Operation Gate
真正的智能限流执行层，防止超限操作
"""

import time
import logging
import threading
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple, Callable
from enum import Enum
from dataclasses import dataclass

from .time_utils import RateLimitTracker


class OperationResult(Enum):
    """操作结果枚举"""
    ALLOWED = "allowed"
    BLOCKED = "blocked"
    DEFERRED = "deferred"
    QUEUED = "queued"


class BlockingStrategy(Enum):
    """阻止策略枚举"""
    HARD_BLOCK = "hard_block"      # 直接阻止
    SOFT_BLOCK = "soft_block"      # 延迟执行
    QUEUE = "queue"                # 排队等待
    THROTTLE = "throttle"          # 节流处理


@dataclass
class OperationRequest:
    """操作请求数据结构"""
    operation_id: str
    operation_type: str
    priority: int = 1
    context: Dict[str, Any] = None
    callback: Optional[Callable] = None
    created_at: float = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = time.time()
        if self.context is None:
            self.context = {}


class OperationGate:
    """操作门控制器 - 智能限流执行核心"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.rate_tracker = RateLimitTracker()
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # 阻止策略配置
        self.blocking_strategies = self._load_blocking_strategies()
        
        # 操作队列和延迟执行
        self.operation_queue: List[OperationRequest] = []
        self.delayed_operations: List[Tuple[float, OperationRequest]] = []
        self.queue_lock = threading.RLock()
        
        # 执行统计
        self.blocked_count = 0
        self.deferred_count = 0
        self.queued_count = 0
        
        # 启动后台处理器
        self._start_background_processor()
        
    def _load_blocking_strategies(self) -> Dict[str, Dict[str, Any]]:
        """加载阻止策略配置"""
        default_strategies = {
            'critical_operations': {
                'strategy': BlockingStrategy.HARD_BLOCK,
                'patterns': ['sudo rm -rf', 'DROP TABLE', 'rm -rf /'],
                'message': '检测到极危险操作，已阻止执行'
            },
            'sensitive_operations': {
                'strategy': BlockingStrategy.SOFT_BLOCK,
                'patterns': ['git push --force', 'npm publish', 'docker rm'],
                'delay_seconds': 5,
                'message': '敏感操作将延迟执行，允许取消'
            },
            'high_frequency': {
                'strategy': BlockingStrategy.QUEUE,
                'max_per_minute': 20,
                'queue_size': 50,
                'message': '操作频率过高，已加入队列'
            },
            'resource_intensive': {
                'strategy': BlockingStrategy.THROTTLE,
                'max_concurrent': 3,
                'throttle_delay': 2,
                'message': '资源密集型操作被节流处理'
            }
        }
        
        # 从配置中加载自定义策略
        custom_strategies = self.config.get('operation_gate', {}).get('strategies', {})
        default_strategies.update(custom_strategies)
        
        return default_strategies
        
    def should_allow_operation(self, request: OperationRequest) -> Tuple[OperationResult, str]:
        """检查是否允许执行操作"""
        
        # 1. 检查是否为关键危险操作
        if self._is_critical_operation(request):
            self.blocked_count += 1
            strategy = self.blocking_strategies['critical_operations']
            return OperationResult.BLOCKED, strategy['message']
            
        # 2. 检查限流状态
        rate_status = self.rate_tracker.check_rate_limit('minute')
        if rate_status['is_limited']:
            return self._handle_rate_limited_operation(request)
            
        # 3. 检查是否为敏感操作
        if self._is_sensitive_operation(request):
            return self._handle_sensitive_operation(request)
            
        # 4. 检查资源使用情况
        if self._is_resource_intensive(request):
            return self._handle_resource_intensive_operation(request)
            
        # 5. 默认允许
        self.rate_tracker.record_usage(request.operation_type)
        return OperationResult.ALLOWED, "操作已允许执行"
        
    def _is_critical_operation(self, request: OperationRequest) -> bool:
        """检查是否为关键危险操作"""
        operation_text = str(request.context.get('command', '')).lower()
        patterns = self.blocking_strategies['critical_operations']['patterns']
        
        return any(pattern in operation_text for pattern in patterns)
        
    def _is_sensitive_operation(self, request: OperationRequest) -> bool:
        """检查是否为敏感操作"""
        operation_text = str(request.context.get('command', '')).lower()
        patterns = self.blocking_strategies['sensitive_operations']['patterns']
        
        return any(pattern in operation_text for pattern in patterns)
        
    def _is_resource_intensive(self, request: OperationRequest) -> bool:
        """检查是否为资源密集型操作"""
        # 简化版本：基于操作类型判断
        intensive_types = ['file_operation', 'network_request', 'compute_heavy']
        return request.operation_type in intensive_types
        
    def _handle_rate_limited_operation(self, request: OperationRequest) -> Tuple[OperationResult, str]:
        """处理限流状态下的操作"""
        strategy_config = self.blocking_strategies.get('high_frequency', {})
        strategy = strategy_config.get('strategy', BlockingStrategy.QUEUE)
        
        if strategy == BlockingStrategy.QUEUE:
            return self._queue_operation(request)
        elif strategy == BlockingStrategy.THROTTLE:
            return self._throttle_operation(request)
        else:
            self.blocked_count += 1
            return OperationResult.BLOCKED, "当前限流中，操作被阻止"
            
    def _handle_sensitive_operation(self, request: OperationRequest) -> Tuple[OperationResult, str]:
        """处理敏感操作"""
        strategy_config = self.blocking_strategies['sensitive_operations']
        delay_seconds = strategy_config.get('delay_seconds', 5)
        
        # 延迟执行
        execute_at = time.time() + delay_seconds
        
        with self.queue_lock:
            self.delayed_operations.append((execute_at, request))
            self.deferred_count += 1
            
        message = f"{strategy_config['message']}，将在{delay_seconds}秒后执行"
        return OperationResult.DEFERRED, message
        
    def _handle_resource_intensive_operation(self, request: OperationRequest) -> Tuple[OperationResult, str]:
        """处理资源密集型操作"""
        strategy_config = self.blocking_strategies['resource_intensive']
        max_concurrent = strategy_config.get('max_concurrent', 3)
        
        # 检查当前并发数（简化版本）
        current_concurrent = len([op for op in self.operation_queue 
                                if op.operation_type == request.operation_type])
                                
        if current_concurrent >= max_concurrent:
            throttle_delay = strategy_config.get('throttle_delay', 2)
            execute_at = time.time() + throttle_delay
            
            with self.queue_lock:
                self.delayed_operations.append((execute_at, request))
                
            message = f"资源使用已达上限，操作将延迟{throttle_delay}秒执行"
            return OperationResult.DEFERRED, message
            
        return OperationResult.ALLOWED, "资源密集型操作已允许"
        
    def _queue_operation(self, request: OperationRequest) -> Tuple[OperationResult, str]:
        """将操作加入队列"""
        strategy_config = self.blocking_strategies['high_frequency']
        max_queue_size = strategy_config.get('queue_size', 50)
        
        with self.queue_lock:
            if len(self.operation_queue) >= max_queue_size:
                self.blocked_count += 1
                return OperationResult.BLOCKED, "队列已满，操作被阻止"
                
            self.operation_queue.append(request)
            self.queued_count += 1
            
        position = len(self.operation_queue)
        message = f"操作已加入队列，当前位置: {position}"
        return OperationResult.QUEUED, message
        
    def _throttle_operation(self, request: OperationRequest) -> Tuple[OperationResult, str]:
        """节流处理操作"""
        strategy_config = self.blocking_strategies.get('high_frequency', {})
        throttle_delay = strategy_config.get('throttle_delay', 1)
        
        execute_at = time.time() + throttle_delay
        
        with self.queue_lock:
            self.delayed_operations.append((execute_at, request))
            
        message = f"操作被节流，将在{throttle_delay}秒后执行"
        return OperationResult.DEFERRED, message
        
    def _start_background_processor(self):
        """启动后台处理器"""
        import threading
        
        def process_delayed_operations():
            while True:
                try:
                    current_time = time.time()
                    ready_operations = []
                    
                    with self.queue_lock:
                        # 找到准备执行的延迟操作
                        self.delayed_operations = [
                            (exec_time, op) for exec_time, op in self.delayed_operations
                            if exec_time > current_time or ready_operations.append(op)
                        ]
                        
                    # 执行准备好的操作
                    for operation in ready_operations:
                        self._execute_delayed_operation(operation)
                        
                    # 处理队列中的操作
                    self._process_queue()
                    
                    time.sleep(0.5)  # 500ms检查间隔
                    
                except Exception as e:
                    self.logger.error(f"后台处理器异常: {e}")
                    time.sleep(1)
                    
        processor_thread = threading.Thread(target=process_delayed_operations, daemon=True)
        processor_thread.start()
        
    def _execute_delayed_operation(self, operation: OperationRequest):
        """执行延迟的操作"""
        try:
            if operation.callback:
                operation.callback(operation)
            else:
                self.logger.info(f"执行延迟操作: {operation.operation_id}")
                # 记录使用
                self.rate_tracker.record_usage(operation.operation_type)
                
        except Exception as e:
            self.logger.error(f"执行延迟操作失败 {operation.operation_id}: {e}")
            
    def _process_queue(self):
        """处理队列中的操作"""
        if not self.operation_queue:
            return
            
        # 检查是否可以处理队列中的操作
        rate_status = self.rate_tracker.check_rate_limit('minute')
        if rate_status['remaining'] <= 0:
            return
            
        with self.queue_lock:
            if self.operation_queue:
                # 取出队列中的第一个操作
                operation = self.operation_queue.pop(0)
                self._execute_delayed_operation(operation)
                
    def get_gate_status(self) -> Dict[str, Any]:
        """获取门控状态"""
        return {
            'rate_limits': self.rate_tracker.get_all_limits_status(),
            'queue_length': len(self.operation_queue),
            'delayed_operations': len(self.delayed_operations),
            'statistics': {
                'blocked_count': self.blocked_count,
                'deferred_count': self.deferred_count,
                'queued_count': self.queued_count
            },
            'strategies': {name: {
                'strategy': str(config['strategy'].value) if isinstance(config.get('strategy'), BlockingStrategy) else config.get('strategy'),
                'description': config.get('message', '')
            } for name, config in self.blocking_strategies.items()}
        }
        
    def cancel_operation(self, operation_id: str) -> bool:
        """取消操作"""
        with self.queue_lock:
            # 从队列中移除
            self.operation_queue = [op for op in self.operation_queue 
                                  if op.operation_id != operation_id]
                                  
            # 从延迟操作中移除
            original_count = len(self.delayed_operations)
            self.delayed_operations = [(exec_time, op) for exec_time, op in self.delayed_operations
                                     if op.operation_id != operation_id]
                                     
            removed = original_count != len(self.delayed_operations)
            
        if removed:
            self.logger.info(f"操作已取消: {operation_id}")
            
        return removed
        
    def emergency_stop(self):
        """紧急停止所有操作"""
        with self.queue_lock:
            blocked_ops = len(self.operation_queue) + len(self.delayed_operations)
            self.operation_queue.clear()
            self.delayed_operations.clear()
            
        self.logger.warning(f"紧急停止: 已清空{blocked_ops}个待执行操作")
        return blocked_ops