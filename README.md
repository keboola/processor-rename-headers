# Header deduplication processor

Takes all tables in `out/tables/` and deduplicates any duplicated columns by adding an index. All other tables 
that do not contain duplicated headers are moved to out unmodified.


**Table of contents:**  
  
[TOC]

## Functional notes

Any table with header containing duplicate columns has its column names deduplicated by appending index:

`A, B, B, C, D` => `A, B, B_1, C, D`

- works with sliced tables
- works with normal tables
- does not ignore manifest file
- if order of duplicated columns changes in the source, the values may be swapped 


## Configuration

### Index separator

Optional parameter `index_separator`.

It is possible to define custom index separator. This is useful when deduplication would lead to already existing column name. 
By default, `_` separator is used. 

e.g.
`A, B, B, B_1, C` => would with the default separator lead to `A, B, B_1, B_1, C`

Fix this by specifying custom separator `__`:

`A, B, B, B_1, C` => would with the default separator lead to `A, B, B__1, B_1, C`


**NOTE**: Only Storage column supported characters may be used, otherwise the import to storage fails. 

### Sample configuration

```json
{
    "definition": {
        "component": "kds-team.processor-deduplicate-headers"
    },
    "parameters": {
    	    "index_separator": "_"
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
git clone https://bitbucket.org:kds_consulting_team/kds-team.processor-deduplicate-headers.git my-new-component
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