# Install

To install the necessary requirements for this Python script, make sure you have Python installed on your system. You can download it from the [official Python website](https://www.python.org/downloads/). This script uses built-in libraries, so no additional packages are required.

# Usage

Run the script from the command line by navigating to the directory where the script is located and executing the following command:

```sh
python zipfiles.py -src SOURCE_FOLDER -dist DESTINATION_FOLDER [-max MAX_SIZE_MB]
```

Replace `SOURCE_FOLDER` with the path to the directory containing files you want to zip, `DESTINATION_FOLDER` with the path where you want the zip files to be saved, and optionally replace `MAX_SIZE_MB` with the maximum size in megabytes for each created zip file.

For example:

```sh
python zipfiles.py -src /path/to/source -dist /path/to/destination -max 50
```

Note that if `--max` is not specified, the default value of 20 MB will be used as the max size for each zip file.

# Examples

Below are examples of how to use the script with different parameters:

- Compress all files in `/mydocuments/project` into zip files of 20 MB each and save them in `/archives`:

    ```sh
    python zipfiles.py --source /mydocuments/project --destination /archives
    ```

- Compress files in `/photos` into zip files of 100 MB each and save them in `/backups/photos_backup`:

    ```sh
    python zipfiles.py --source /photos --destination /backups/photos_backup --max 100
    ```