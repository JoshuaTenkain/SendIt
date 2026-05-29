#!/bin/bash

# Send-it Test Runner Script
# Runs comprehensive test suite for Phases 1 & 2

set -e

echo "=========================================="
echo "Send-it Platform: Test Suite Runner"
echo "=========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counters
TESTS_PASSED=0
TESTS_FAILED=0

# Function to run a test suite
run_test_suite() {
    local test_file=$1
    local test_name=$2
    
    echo -e "${YELLOW}Running: $test_name${NC}"
    if pytest "tests/$test_file" -v --tb=short; then
        echo -e "${GREEN}✓ $test_name passed${NC}"
        ((TESTS_PASSED++))
    else
        echo -e "${RED}✗ $test_name failed${NC}"
        ((TESTS_FAILED++))
    fi
    echo ""
}

# Phase 1.1 - Courier Adapters
echo -e "${YELLOW}=== PHASE 1.1: Courier API Integrations ===${NC}"
run_test_suite "test_courier_adapters.py" "Courier Adapters"
run_test_suite "test_tcg_adapter.py" "TCG Adapter"

# Phase 1.2 - Email & SMS
echo -e "${YELLOW}=== PHASE 1.2: Email & SMS Notifications ===${NC}"
run_test_suite "test_email_service.py" "Email Service"

# Phase 1.3 - Cancellation
echo -e "${YELLOW}=== PHASE 1.3: Booking Cancellation ===${NC}"
run_test_suite "test_cancellation_service.py" "Cancellation Service"

# Phase 2.1 - Quote Caching
echo -e "${YELLOW}=== PHASE 2.1: Quote Caching ===${NC}"
run_test_suite "test_quote_cache.py" "Quote Cache Service"

# Phase 2.2 - Tracking
echo -e "${YELLOW}=== PHASE 2.2: Tracking & Issues ===${NC}"
run_test_suite "test_tracking_service.py" "Tracking Service"

# Existing tests
echo -e "${YELLOW}=== EXISTING TESTS ===${NC}"
run_test_suite "test_auth.py" "Authentication"
run_test_suite "test_bookings.py" "Bookings"
run_test_suite "test_quotes.py" "Quotes"
run_test_suite "test_addresses.py" "Addresses"

# Summary
echo ""
echo "=========================================="
echo "Test Summary"
echo "=========================================="
echo -e "${GREEN}Passed: $TESTS_PASSED${NC}"
echo -e "${RED}Failed: $TESTS_FAILED${NC}"
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}All tests passed!${NC}"
    exit 0
else
    echo -e "${RED}Some tests failed. Please review the output above.${NC}"
    exit 1
fi
