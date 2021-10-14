# sync source files to server
rsync -azv --exclude={'__pycache__','.git','.vscode'} ~/CryoEM/ $USER@storage-ceitec1-fe1.ceitec.muni.cz:~/CryoEM/build