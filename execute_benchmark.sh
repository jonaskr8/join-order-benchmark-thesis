#!/usr/bin/env bash

SQL_DIR="/home/jonas/Studium/Master/Thesis/join-order-benchmark/some_queries"
OUT_FILE="$1"
DB_FILE="/home/jonas/Studium/Master/Thesis/join-order-benchmark/benchmark.duckdb"
DUCKDB="/home/jonas/Studium/Master/Thesis/duckdb/build/release/duckdb"
if [[ -z "$OUT_FILE" ]]; then
    echo "Usage: $0 <output_file>"
    exit 1
fi

echo '' > "$OUT_FILE"
echo '' > "${OUT_FILE%.csv}_processed.csv"

escape_csv() {
  printf '%s' "$1" | sed 's/"/""/g'
}

for query in "$SQL_DIR"/*.sql; do
  query_name=$(basename "$query" .sql)
  for threshold in {2..13}; do
    for repetition in {1..30}; do
      # execute query with threshold for repetition times and save results to output file
      echo "sql_file=$query_name threshold=$threshold repetition=$repetition"
      output=$("$DUCKDB" "$DB_FILE" -cmd '.mode trash' -cmd "SET approximate_join_order_threshold=$threshold;" -cmd '.timer on' -c ".read $query" 2>&1) # oder -f $query
      output=${output//$'\n'/ }
      printf '%s,%s,%s,%s\n' \
        "$(escape_csv "$query_name")" \
        "$threshold" \
        "$repetition" \
        "$(escape_csv "$output")" >> "$OUT_FILE"
    done
  done
done

sed -n 's/\(.*\)Run.*real \([0-9]*\.[0-9]*\).*/\1\2/gp' "$OUT_FILE" > "${OUT_FILE%.csv}_processed.csv"