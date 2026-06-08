#!/usr/bin/env bash

SQL_DIR="/home/jonas/Studium/Master/Thesis/join-order-benchmark/some_queries"
OUT_FILE="$1"
DB_FILE="/home/jonas/Studium/Master/Thesis/join-order-benchmark/benchmark.duckdb"
DUCKDB="/home/jonas/Studium/Master/Thesis/duckdb/build/release/duckdb"

if [[ -z "$OUT_FILE" ]]; then
    echo "Usage: $0 <output_file>"
    exit 1
fi

> "$OUT_FILE"

for query in "$SQL_DIR"/*.sql; do
  query_name=$(basename "$query" .sql)
  for threshold in {2..13}; do
    for repetition in {1..5}; do
      # execute query with threshold for repetition times and save results to output file
      echo "sql_file=$query_name threshold=$threshold repetition=$repetition"
      out_path="/home/jonas/Studium/Master/Thesis/join-order-benchmark/profiling/$query_name-$threshold-$repetition.json"
      "$DUCKDB" "$DB_FILE" -cmd '.mode trash' -cmd "SET approximate_join_order_threshold=$threshold;" -cmd 'pragma enable_profiling;' -cmd "set enable_profiling='json'" -cmd "set profiling_mode='detailed'" -cmd "set profiling_output='$out_path'" -f "$query" 2>&1
      time=$(sed -n 's/.*\"optimizer_join_order\": \([^,]*\),/\1/gp' "$out_path")
      printf '%s,%s,%s,%s\n' \
        "$query_name" \
        "$threshold" \
        "$repetition" \
        "$time" >> "$OUT_FILE"
      rm "$out_path"
    done
  done
done