from optparse import OptionParser
import os
import server

_conn = None

def get_connection():
    return server.Server()

def main():
    usage = "usage: %prog file_path"
    parser = OptionParser(usage)
    (options, args) = parser.parse_args()
    if len(args) != 1:
        parser.error("Incorrect number of arguments!")
    else:
        file_path = args[0]
        if file_path[0] == '.' or '/' != file_path[0]:
            now_path = os.getcwd()
            abs_path = now_path + '/' + file_path
        elif file_path[0] == '/':
            abs_path = args[0]

    _conn = get_connection()
    _conn.store(abs_path)
    print abs_path

if __name__ == '__main__':
    main()
