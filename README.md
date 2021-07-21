# Rename headers processor

Takes all tables in `in/tables/` and renames specified columns in specified tables. Result is moved to `out/tables/` All other tables 
that are not specified or columns that are not specified are moved unchanged.

Manifest files are respected and transferred / modified as well.


**Table of contents:**  
  
[TOC]



## Configuration

list table names in parameters and list columns to rename, all others are kept

```
"test.csv": {
          "column_mapping": {
            "Column_1": "New_name_col_1"
          }
```

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
 
# Development
 
This example contains runnable container with simple unittest. For local testing it is useful to include `data` folder in the root
and use docker-compose commands to run the container or execute tests. 

If required, change local data folder (the `CUSTOM_FOLDER` placeholder) path to your custom path:
```yaml
    volumes:
      - ./:/code
      - ./CUSTOM_FOLDER:/data
```

Clone this repository, init the workspace and run the component with following command:

```
git clone https://bitbucket.org:kds_consulting_team/kds-team.processor-rename-headers.git my-new-component
cd my-new-component
docker-compose build
docker-compose run --rm dev
```

Run the test suite and lint check using this command:

```
docker-compose run --rm test
```

# Testing

The preset pipeline scripts contain sections allowing pushing testing image into the ECR repository and automatic 
testing in a dedicated project. These sections are by default commented out. 

# Integration

For information about deployment and integration with KBC, please refer to the [deployment section of developers documentation](https://developers.keboola.com/extend/component/deployment/) 