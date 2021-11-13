# sync source files to server
# call like ./push_sources.sh abc.node.eu
rsync -azv --exclude={'__pycache__','.git','.vscode'} ~/CryoEM/ $USER@$1:~/CryoEM/build
