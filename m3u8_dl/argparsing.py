from argparse import ArgumentParser,Namespace
from m3u8_dl.constants import NB_PARTS, WAIT_SECONDS

def parse_args() -> Namespace:
    parser = ArgumentParser("m3u8dl")
    
    # output
    parser.add_argument("-o","--output",type=str)
    
    # wait time
    parser.add_argument("-w","--wait",type=int,help="the number of seconds to wait before trying a new download method",default=WAIT_SECONDS)
    
    # nb parts
    parser.add_argument("-n","--nb-parts",type=int,help="the number of parts to split the m3u8 in if the single download doesn't work",default=NB_PARTS)
    
    # ffmpeg path
    parser.add_argument("-f","--ffmpeg-path",type=str,help="the path to the ffmpeg executable to use",default="ffmpeg")
    
    ### nb results
    parser.add_argument("--nb-results",help="the number of results to display",default=5,type=int)
    
    # m3u8 url or filepath or query
    parser.add_argument("url_or_filepath_or_query",type=str)    
    
    return parser.parse_args()