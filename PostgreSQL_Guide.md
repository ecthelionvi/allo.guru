# Guide to Installing and Using PostgreSQL

## Install PostgreSQL
- Update your system and install PostgreSQL:
  ```bash
  sudo yum update -y
  sudo yum install [postgresql-version]
  ```
  Replace `[postgresql-version]` with the specific version you want to install, e.g., `postgresql15.aarch64`.

## Connect to PostgreSQL
- Connect to a PostgreSQL database:
  ```bash
  psql -h [your-database-host] -p [port] -U [username] -d [database-name]
  ```
  Replace `[your-database-host]`, `[port]`, `[username]`, and `[database-name]` with your specific connection details.

## Common PostgreSQL Operations
### Add a Database
- To create a new database:
  ```sql
  CREATE DATABASE [database-name];
  ```

### Drop a Table
- To delete a table:
  ```sql
  DROP TABLE [table-name];
  ```

### View All Elements in a Table
- To view all rows in a table:
  ```sql
  SELECT * FROM [table-name];
  ```
  Replace `[database-name]`, `[table-name]` with the names of your database and table.
