#!/bin/bash
# check-stale-memories.sh — CASS 置信度衰减检测
# 扫描 memory 文件，应用衰减公式，报告 stale 记忆

MEMORY_DIR="${1:-$HOME/.claude/projects/-Users-jerry-hu-AI/memory}"

if [ ! -d "$MEMORY_DIR" ]; then
  echo "Error: memory directory not found at $MEMORY_DIR"
  exit 1
fi

TODAY=$(date +%s)
TOTAL=0
STALE_COUNT=0
AGING_COUNT=0
HEALTHY_COUNT=0
STALE_LIST=""
AGING_LIST=""
HEALTHY_LIST=""
CANDIDATE_COUNT=0
ESTABLISHED_COUNT=0
PROVEN_COUNT=0
DEPRECATED_COUNT=0

for file in "$MEMORY_DIR"/*.md; do
  filename=$(basename "$file")
  [ "$filename" = "MEMORY.md" ] && continue

  in_frontmatter=false
  name=""
  confidence=""
  last_verified=""
  maturity=""

  feedback_count=""
  last_referenced=""

  while IFS= read -r line; do
    if [ "$line" = "---" ]; then
      if $in_frontmatter; then
        break
      else
        in_frontmatter=true
        continue
      fi
    fi
    if $in_frontmatter; then
      key=$(echo "$line" | cut -d: -f1 | tr -d ' ')
      val=$(echo "$line" | cut -d: -f2- | sed 's/^ *//')
      case "$key" in
        name) name="$val" ;;
        confidence) confidence="$val" ;;
        last_verified) last_verified="$val" ;;
        maturity) maturity="$val" ;;
        feedback_count) feedback_count="$val" ;;
        last_referenced) last_referenced="$val" ;;
      esac
    fi
  done < "$file"

  [ -z "$last_verified" ] && continue
  TOTAL=$((TOTAL + 1))

  verified_ts=$(date -j -f "%Y-%m-%d" "$last_verified" +%s 2>/dev/null)
  [ -z "$verified_ts" ] && continue
  age_days=$(( (TODAY - verified_ts) / 86400 ))

  conf="${confidence:-0.7}"
  decayed=$(echo "$conf * e(l(0.5) * $age_days / 90)" | bc -l 2>/dev/null)
  decayed=$(printf "%.2f" "$decayed" 2>/dev/null || echo "$conf")

  if [ "$age_days" -gt 90 ]; then
    STALE_COUNT=$((STALE_COUNT + 1))
    STALE_LIST="${STALE_LIST}\n  - ${filename} (${age_days}d, ${conf}->${decayed}, ${maturity:-?}, refs:${feedback_count:-0}, last_ref:${last_referenced:-never})"
  elif [ "$age_days" -gt 45 ]; then
    AGING_COUNT=$((AGING_COUNT + 1))
    AGING_LIST="${AGING_LIST}\n  - ${filename} (${age_days}d, ${conf}->${decayed}, ${maturity:-?}, refs:${feedback_count:-0}, last_ref:${last_referenced:-never})"
  else
    HEALTHY_COUNT=$((HEALTHY_COUNT + 1))
    HEALTHY_LIST="${HEALTHY_LIST}\n  - ${filename} (${age_days}d, ${conf}->${decayed}, ${maturity:-?}, refs:${feedback_count:-0}, last_ref:${last_referenced:-never})"
  fi

  # Track maturity counts
  case "${maturity:-?}" in
    candidate) CANDIDATE_COUNT=$((CANDIDATE_COUNT + 1)) ;;
    established) ESTABLISHED_COUNT=$((ESTABLISHED_COUNT + 1)) ;;
    proven) PROVEN_COUNT=$((PROVEN_COUNT + 1)) ;;
    deprecated) DEPRECATED_COUNT=$((DEPRECATED_COUNT + 1)) ;;
  esac
done

echo "Memory Health Check (${TOTAL} memories, decay: 0.5^(age/90))"
echo ""
if [ "$STALE_COUNT" -gt 0 ]; then
  echo "STALE (${STALE_COUNT}): confidence <50%, verify or archive"
  echo -e "$STALE_LIST"
  echo ""
fi
if [ "$AGING_COUNT" -gt 0 ]; then
  echo "AGING (${AGING_COUNT}): decaying, consider verifying"
  echo -e "$AGING_LIST"
  echo ""
fi
if [ "$STALE_COUNT" -eq 0 ] && [ "$AGING_COUNT" -eq 0 ]; then
  echo "ALL HEALTHY (${HEALTHY_COUNT}): within 45 days"
  echo -e "$HEALTHY_LIST"
else
  echo "HEALTHY (${HEALTHY_COUNT}): within 45 days"
  echo -e "$HEALTHY_LIST"
fi
echo ""
echo "Maturity: candidate=${CANDIDATE_COUNT} established=${ESTABLISHED_COUNT} proven=${PROVEN_COUNT} deprecated=${DEPRECATED_COUNT}"
