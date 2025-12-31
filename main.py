from m3u8_dl.argparsing import parse_args
from m3u8_dl.download import download

if __name__ == "__main__":
    args = parse_args()
    download(args)