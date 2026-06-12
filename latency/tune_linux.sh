#!/bin/bash
set -e

# ---------------------------------------------------------------------------
# Low-latency network tuning for trading infrastructure
# Increases socket buffers, enables busy-poll, stops irqbalance
# ---------------------------------------------------------------------------

RMEM_MAX=134217728
WMEM_MAX=134217728
RMEM_DEFAULT=134217728
WMEM_DEFAULT=134217728
BUSY_POLL=50
BUSY_READ=50

get_value() {
    sysctl -n "$1" 2>/dev/null || echo "N/A"
}

apply_sysctl() {
    local key=$1
    local value=$2
    if sysctl -a 2>/dev/null | grep -q "^${key}"; then
        sysctl -w "${key}=${value}"
    else
        echo "Skipping ${key} (not available on this kernel)"
    fi
}

print_values() {
    echo "net.core.rmem_max        = $(get_value net.core.rmem_max)"
    echo "net.core.wmem_max        = $(get_value net.core.wmem_max)"
    echo "net.core.rmem_default    = $(get_value net.core.rmem_default)"
    echo "net.core.wmem_default    = $(get_value net.core.wmem_default)"
    echo "net.ipv4.tcp_low_latency = $(get_value net.ipv4.tcp_low_latency)"
    echo "net.core.busy_poll       = $(get_value net.core.busy_poll)"
    echo "net.core.busy_read       = $(get_value net.core.busy_read)"
    echo "irqbalance               = $(systemctl is-active irqbalance 2>/dev/null || echo inactive)"
}

echo "=========================================================="
echo "  LOW LATENCY NETWORK TUNING"
echo "=========================================================="

echo
echo "[BEFORE]"
print_values

OLD_RMEM_MAX=$(get_value net.core.rmem_max)
OLD_WMEM_MAX=$(get_value net.core.wmem_max)
OLD_BUSY_POLL=$(get_value net.core.busy_poll)
OLD_TCP_LOW=$(get_value net.ipv4.tcp_low_latency)
OLD_IRQ=$(systemctl is-active irqbalance 2>/dev/null || echo inactive)

echo
echo "[APPLYING TUNING]"
echo

apply_sysctl net.core.rmem_max        $RMEM_MAX
apply_sysctl net.core.wmem_max        $WMEM_MAX
apply_sysctl net.core.rmem_default    $RMEM_DEFAULT
apply_sysctl net.core.wmem_default    $WMEM_DEFAULT
apply_sysctl net.ipv4.tcp_low_latency 1
apply_sysctl net.core.busy_poll       $BUSY_POLL
apply_sysctl net.core.busy_read       $BUSY_READ

echo
echo "[STOPPING IRQBALANCE]"
if systemctl is-active --quiet irqbalance; then
    systemctl stop irqbalance
    systemctl disable irqbalance
    IRQ_ACTION="stopped and disabled"
else
    IRQ_ACTION="already inactive"
fi
echo "irqbalance: $IRQ_ACTION"

echo
echo "[AFTER]"
print_values

echo
echo "=========================================================="
echo "  SUMMARY"
echo "=========================================================="
printf "%-30s %s -> %s\n" "net.core.rmem_max"        "$OLD_RMEM_MAX"  "$(get_value net.core.rmem_max)"
printf "%-30s %s -> %s\n" "net.core.wmem_max"        "$OLD_WMEM_MAX"  "$(get_value net.core.wmem_max)"
printf "%-30s %s -> %s\n" "net.core.busy_poll"       "$OLD_BUSY_POLL" "$(get_value net.core.busy_poll)"
printf "%-30s %s -> %s\n" "net.ipv4.tcp_low_latency" "$OLD_TCP_LOW"   "$(get_value net.ipv4.tcp_low_latency)"
printf "%-30s %s -> %s\n" "irqbalance"               "$OLD_IRQ"       "$IRQ_ACTION"
echo
echo "Tuning complete. Run tuned_test.py to measure impact."