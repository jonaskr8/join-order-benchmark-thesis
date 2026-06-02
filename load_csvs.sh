#!/usr/bin/env bash

CSV_DIR="/home/jonas/Studium/Master/Thesis/join-order-benchmark/imdb"
DB_FILE="/home/jonas/Studium/Master/Thesis/join-order-benchmark/benchmark.duckdb"
duckdb="/home/jonas/Studium/Master/Thesis/duckdb/build/release/duckdb"

for csv_file in "$CSV_DIR"/*.csv; do
  table_name=$(basename "$csv_file" .csv)
  echo "clearing table $table_name"
  $duckdb $DB_FILE -c "DELETE FROM $table_name;"

  echo "Loading $csv_file into table $table_name..."

  $duckdb $DB_FILE -c "COPY $table_name FROM '$csv_file' (ESCAPE '\')";
done

echo "done"