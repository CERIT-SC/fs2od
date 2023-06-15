# Dataset
Basic dataset details:

| Attribute   | Value                |
| ---         | ---                  |
| Name        | **$dataset_name**    |
| Institution | **$institution_name** |

## Usage
You can browse through the content of the dataset in this web interface in the tab `Files`.


[//]: # (## Metadata file)

[//]: # (Here is the actual copy of metadata file:)

[//]: # (```yaml)

[//]: # (metadata: content)

[//]: # (```)

$metadata_section

## Download
You can run following command to download whole content of the dataset:
```sh
# get the download script
wget https://raw.githubusercontent.com/CERIT-SC/onedata-downloader/master/download.py

# download the dataset to the current folder
python3 download.py $share_file_id

# help can be obtain by
python3 download.py --help
```
or you can run the download script directly from the repository:
```sh
curl -s https://raw.githubusercontent.com/CERIT-SC/onedata-downloader/master/download.py | python3 - $share_file_id
```

Data life cycle of this dataset is managed by fs2od (https://fs2od.readthedocs.io).
