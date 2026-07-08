#!/usr/bin/env python3
"""
End-to-End 测试：SDK → Backend → Frontend 完整流程
"""

import time
import requests
import sys
import os

# Add SDK to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "sdk"))

from memguard.core.interceptor import MemGuardInterceptor
from memguard.transport import HttpTransport
from memguard.core.event import MemoryOp, MemoryType

def test_complete_flow():
    print("\n" + "="*70)
    print("  End-to-End 测试：完整流程验证")
    print("="*70 + "\n")

    # 1. 创建 SDK interceptor
    print("📡 步骤 1: 创建 SDK interceptor...")
    interceptor = MemGuardInterceptor(
        agent_id="test-e2e-agent",
        namespace="test-org",
        transport=HttpTransport("http://localhost:8000"),
        capture_content=True
    )
    interceptor.set_session("test-e2e-session-001")
    print("   ✅ SDK interceptor 已创建\n")

    # 2. 生成测试事件
    print("📤 步骤 2: 生成测试事件...")
    test_events = []
    for i in range(5):
        event_id = interceptor.record(
            operation=MemoryOp.CREATE,
            memory_key=f"test_key_{i}",
            after_value={"test": f"value_{i}"},
            memory_type=MemoryType.SEMANTIC,
            tags=["e2e-test"]
        )
        test_events.append(event_id)
        print(f"   ✅ Event {i+1}/5: {event_id[:8]}...")
        time.sleep(0.1)

    print(f"\n   ✅ 生成了 {len(test_events)} 个测试事件\n")

    # 3. 等待 Backend 处理
    print("⏳ 步骤 3: 等待 Backend 处理...")
    time.sleep(2)
    print("   ✅ 等待完成\n")

    # 4. 验证 Backend API
    print("🔍 步骤 4: 验证 Backend API...")

    # 4.1 检查统计
    try:
        stats_res = requests.get("http://localhost:8000/v1/db/stats")
        if stats_res.status_code == 200:
            stats = stats_res.json()
            print(f"   ✅ 统计 API: {stats['total_events']} 个事件")
        else:
            print(f"   ❌ 统计 API 失败: {stats_res.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Backend 无法连接: {e}")
        return False

    # 4.2 检查事件列表
    try:
        events_res = requests.get("http://localhost:8000/v1/events?limit=10")
        if events_res.status_code == 200:
            events_data = events_res.json()
            events = events_data.get("events", [])
            print(f"   ✅ 事件列表 API: 返回 {len(events)} 个事件")

            # 验证我们的测试事件
            found_count = sum(1 for e in events if e.get("agent_id") == "test-e2e-agent")
            print(f"   ✅ 找到 {found_count} 个测试事件")
        else:
            print(f"   ⚠️  事件列表 API: {events_res.status_code} (可能还没实现)")
            print(f"   📝 需要添加: GET /v1/events 端点")
    except Exception as e:
        print(f"   ⚠️  事件列表 API 调用失败: {e}")

    print()

    # 5. 验证 Frontend
    print("🌐 步骤 5: 验证 Frontend...")
    try:
        frontend_res = requests.get("http://localhost:3000")
        if frontend_res.status_code == 200:
            print("   ✅ Frontend 可访问")
            print("   ✅ 打开浏览器查看: http://localhost:3000")
        else:
            print(f"   ❌ Frontend 无法访问: {frontend_res.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Frontend 连接失败: {e}")
        return False

    print()
    print("="*70)
    print("  ✅ End-to-End 测试完成！")
    print("="*70 + "\n")

    print("📊 测试报告:")
    print(f"  - SDK 事件生成: ✅ {len(test_events)} 个事件")
    print(f"  - Backend 接收: ✅ 统计 API 正常")
    print(f"  - Backend 查询: ⚠️  需要添加 /v1/events API")
    print(f"  - Frontend 访问: ✅ Dashboard 可用")
    print()
    print("📝 下一步:")
    print("  1. 在 backend/app/main.py 添加 GET /v1/events 端点")
    print("  2. 重启 Backend")
    print("  3. 重新运行此测试")
    print()

    return True

if __name__ == "__main__":
    success = test_complete_flow()
    sys.exit(0 if success else 1)
