# Dataset
Basic dataset details:

| Attribute   | Value                |
| ---         | ---                  |
| Name        | **$dataset_name**    |
| Institution | **$institution_name** |

## Usage
You can browse through the content of the dataset in this web interface in the tab `Files`.

## Download
 You can run following command to download whole content of the dataset:
```
# get the download script
wget https://raw.githubusercontent.com/CERIT-SC/onedata-downloader/master/download.py

# download the dataset
./download.py $share_file_id
```
or you can run the download script directly from the repository:
```
curl -s https://raw.githubusercontent.com/CERIT-SC/onedata-downloader/master/download.py | python3 - $share_file_id
```

Data life cycle of this dataset is managed by fs2od (https://fs2od.readthedocs.io).
