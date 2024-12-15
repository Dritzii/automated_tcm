from io import BytesIO
from zipfile import ZipFile

myzip = ZipFile("/mnt/49bb6cd3-a5bf-468d-b67a-f4dd29190808/test.zip")
unzip = myzip.open(myzip.namelist()[0])
print(unzip)