#!/usr/bin/env bash

## This script measures the overall execution time for all queries for different thresholds.
## The results are saved in a csv file with the following format: query_name,threshold,optimizer_join_order_time,actual_join_times.

SQL_DIR="/home/jonas/Studium/Master/Thesis/join-order-benchmark/some_queries"
OUT_FILE="$1"
DB_FILE="/home/jonas/Studium/Master/Thesis/join-order-benchmark/benchmark.duckdb"
DUCKDB="/home/jonas/Studium/Master/Thesis/duckdb/build/release/duckdb"

if [[ -z "$OUT_FILE" ]]; then
    echo "Usage: $0 <output_file>"
    exit 1
fi

> "$OUT_FILE"


for threshold in {14..1}; do
  for query in "$SQL_DIR"/*.sql; do
    query_name=$(basename "$query" .sql)
    # execute query with threshold for repetition times and save results to output file
    echo "sql_file=$query_name threshold=$threshold"
    out_path="/home/jonas/Studium/Master/Thesis/join-order-benchmark/profiling/$query_name-$threshold.json"
    "$DUCKDB" "$DB_FILE" -cmd '.mode trash' -cmd "SET approximate_join_order_threshold=$threshold;" -cmd 'pragma enable_profiling;' -cmd "set enable_profiling='json'" -cmd "set profiling_mode='detailed'" -cmd "set profiling_output='$out_path'" -f "$query" 2>&1
    # optimize_join_order_time=$(sed -n 's/.*\"optimizer_join_order\": \([^,]*\),/\1/gp' "$out_path")
    # actual_join_times=$(sed -n 's/.*\"actual_join_times\": \([^]]*\),/\1/gp' "$out_path")
    # printf '%s,%s,%s,[%s]\n' \
    #   "$query_name" \
    #   "$threshold" \
    #   "$optimize_join_order_time" \
    #   "$actual_join_times" >> "$OUT_FILE"
      # rm "$out_path"
  done
done