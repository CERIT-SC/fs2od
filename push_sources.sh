# sync source files to server
# call like ./push_sources.sh abc.node.eu
rsync -azv --exclude={'__pycache__','.git','.vscode'} $PWD/ $USER@$1:~/fs2od/devel/sources
