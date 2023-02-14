
Takes all tables in `in/tables/` and renames specified columns in specified tables. Result is moved to `out/tables/` All
other tables that are not specified or columns that are not specified are moved unchanged.

Files present in folder `in/files` are moved unchanged.

Manifest files are respected and transferred / modified as well.


## Configuration

### Sample configuration

```json
{
  "definition": {
    "component": "kds-team.processor-rename-headers"
  },
  "parameters": {
    "test.csv": {
      "column_mapping": {
        "Column_1": "New_name_col_1"
      }
    }
  }
}
```

List table names in parameters and list columns to rename, all others are kept

```
"test.csv": {
          "column_mapping": {
            "Column_1": "New_name_col_1"
          }
```

**NOTE**: Simple `*` wildcard is supported at the end of table name, e.g.:

```
"te*": {
          "column_mapping": {
            "Column_1": "New_name_col_1"
          }
```

The above will rename columns in table `test.csv`.
