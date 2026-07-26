#!/bin/bash
# Verification script for MemGuard standalone demo

echo "================================================"
echo "MemGuard Standalone Demo Verification"
echo "================================================"
echo ""

# Test 1: Check if demo files exist
echo "Test 1: Checking demo files..."
if [ -f "demo_simple.py" ] && [ -f "demo_with_dashboard.py" ]; then
    echo "✅ Demo files exist"
else
    echo "❌ Demo files missing"
    exit 1
fi

# Test 2: Check if SDK can be imported
echo ""
echo "Test 2: Testing SDK imports..."
python3 -c "
import sys
sys.path.insert(0, 'sdk')
try:
    from memguard import MemGuardInterceptor
    from memguard.transport.stdout import StdoutTransport
    from memguard.transport.http import HttpTransport
    print('✅ All SDK imports work')
except ImportError as e:
    print(f'❌ Import failed: {e}')
    sys.exit(1)
"

# Test 3: Check if required packages are available
echo ""
echo "Test 3: Checking required packages..."
python3 -c "
import sys
packages = []
try:
    import openai
    packages.append('openai')
except:
    pass
try:
    import rich
    packages.append('rich')
except:
    pass

if len(packages) == 2:
    print('✅ All required packages installed (openai, rich)')
elif len(packages) > 0:
    print(f'⚠️  Partial: {packages} installed')
    print('   Run: pip install openai rich')
else:
    print('⚠️  Missing packages')
    print('   Run: pip install openai rich')
"

# Test 4: Check if demo_simple.py has correct structure
echo ""
echo "Test 4: Validating demo_simple.py structure..."
if grep -q "MemGuardInterceptor" demo_simple.py && \
   grep -q "StdoutTransport" demo_simple.py && \
   grep -q "OPENAI_API_KEY" demo_simple.py; then
    echo "✅ demo_simple.py has correct structure"
else
    echo "❌ demo_simple.py structure incomplete"
fi

# Test 5: Check if demo_with_dashboard.py has correct structure
echo ""
echo "Test 5: Validating demo_with_dashboard.py structure..."
if grep -q "HttpTransport" demo_with_dashboard.py && \
   grep -q "trace_decision" demo_with_dashboard.py; then
    echo "✅ demo_with_dashboard.py has correct structure"
else
    echo "❌ demo_with_dashboard.py structure incomplete"
fi

# Test 6: Check README
echo ""
echo "Test 6: Checking README.md updates..."
if grep -q "5-minute demo (terminal only)" README.md && \
   grep -q "pip install -e sdk/" README.md; then
    echo "✅ README.md updated with quick start"
else
    echo "❌ README.md not updated"
fi

# Test 7: Check SDK packaging files
echo ""
echo "Test 7: Checking SDK packaging..."
if [ -f "sdk/pyproject.toml" ] && [ -f "sdk/setup.py" ] && [ -f "sdk/README.md" ]; then
    echo "✅ SDK packaging files present"
else
    echo "❌ SDK packaging incomplete"
fi

echo ""
echo "================================================"
echo "Verification Summary"
echo "================================================"
echo ""
echo "To run the demo:"
echo "  1. export OPENAI_API_KEY=sk-xxx"
echo "  2. python3 demo_simple.py"
echo ""
echo "If you see import errors, run:"
echo "  pip3 install openai rich"
echo ""
