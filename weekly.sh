#!/bin/bash
# =============================================================================
# weekly.sh – CSCI 3060U Phase 6: Weekly Banking System Script
# Group 21: Bushrat Zahan, Menhdi Patel, Sevara Omonova, Nabiha Shah
#
# Runs daily.sh seven times, simulating seven days of Banking System operation.
# The Current Bank Accounts File and Master Bank Accounts File from each day
# are automatically fed as inputs to the next day, chaining all seven days.
#
# USAGE (run from repo root):
#   ./weekly.sh [initial_current] [initial_master] [output_root] [inputs_root]
#
#   initial_current – Starting Current Bank Accounts File
#                     Default: frontend/current_accounts.txt
#   initial_master  – Starting Master Bank Accounts File
#                     Default: backend/old_master.txt
#   output_root     – Root output directory; day1/..day7/ created inside
#                     Default: outputs/week
#   inputs_root     – Root input directory containing day1/..day7/ sub-dirs
#                     Default: inputs
#
# EXPECTED INPUT LAYOUT:
#   inputs/
#     day1/  session1.txt  session2.txt  session3.txt
#     day2/  ...
#     day7/  ...
#
# OUTPUT LAYOUT:
#   outputs/week/
#     day1/  session1.atf  session2.atf  session3.atf
#            merged.atf    new_master.baf  new_current.baf
#     day2/  ...
#     day7/  ...
# =============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DAILY_SCRIPT="$SCRIPT_DIR/daily.sh"

# Defaults (all relative to repo root)
INITIAL_CURRENT="${1:-frontend/current_accounts.txt}"
INITIAL_MASTER="${2:-backend/old_master.txt}"
OUTPUT_ROOT="${3:-outputs/week}"
INPUTS_ROOT="${4:-inputs}"

# --------------------------------------------------------------------------
# Pre-flight checks
# --------------------------------------------------------------------------
if [ ! -f "$DAILY_SCRIPT" ]; then
    echo "ERROR: daily.sh not found at: $DAILY_SCRIPT"
    exit 1
fi
if [ ! -f "$INITIAL_CURRENT" ]; then
    echo "ERROR: Initial current accounts file not found: $INITIAL_CURRENT"
    exit 1
fi
if [ ! -f "$INITIAL_MASTER" ]; then
    echo "ERROR: Initial master accounts file not found: $INITIAL_MASTER"
    exit 1
fi

chmod +x "$DAILY_SCRIPT"
mkdir -p "$OUTPUT_ROOT"

# --------------------------------------------------------------------------
# Run seven daily cycles
# --------------------------------------------------------------------------
CURRENT_ACCOUNTS="$INITIAL_CURRENT"
MASTER_ACCOUNTS="$INITIAL_MASTER"

for DAY in $(seq 1 7); do
    echo ""
    echo "############################################################"
    echo "# DAY $DAY OF 7"
    echo "#   Current accounts : $CURRENT_ACCOUNTS"
    echo "#   Master accounts  : $MASTER_ACCOUNTS"
    echo "#   Session inputs   : $INPUTS_ROOT/day${DAY}/"
    echo "#   Outputs          : $OUTPUT_ROOT/day${DAY}/"
    echo "############################################################"

    DAY_OUTPUT="$OUTPUT_ROOT/day${DAY}"
    DAY_INPUT="$INPUTS_ROOT/day${DAY}"

    "$DAILY_SCRIPT" "$CURRENT_ACCOUNTS" "$MASTER_ACCOUNTS" \
                    "$DAY_OUTPUT" "$DAY_INPUT"

    if [ "$?" -ne 0 ]; then
        echo "ERROR: daily.sh failed on Day $DAY. Aborting."
        exit 1
    fi

    # Verify outputs exist before chaining
    NEW_CURRENT="$DAY_OUTPUT/new_current.baf"
    NEW_MASTER="$DAY_OUTPUT/new_master.baf"

    if [ ! -f "$NEW_CURRENT" ] || [ ! -f "$NEW_MASTER" ]; then
        echo "ERROR: Expected output files missing after Day $DAY. Aborting."
        exit 1
    fi

    # Chain: next day uses this day's outputs as its inputs
    CURRENT_ACCOUNTS="$NEW_CURRENT"
    MASTER_ACCOUNTS="$NEW_MASTER"
done

# --------------------------------------------------------------------------
# Final summary
# --------------------------------------------------------------------------
echo ""
echo "############################################################"
echo "# WEEKLY RUN COMPLETE — 7 days simulated"
echo "############################################################"
echo "Final Current Bank Accounts : $OUTPUT_ROOT/day7/new_current.baf"
echo "Final Master Bank Accounts  : $OUTPUT_ROOT/day7/new_master.baf"
echo ""
echo "Per-day outputs:"
for DAY in $(seq 1 7); do
    echo "  Day $DAY : $OUTPUT_ROOT/day${DAY}/"
done
