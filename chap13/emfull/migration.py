from optparse import OptionParser
import os
import server

_conn = None

def get_connection(server_num=5):
    return server.Server(server_num)

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

    server_num = 5
    _conn = get_connection(server_num)
    _new_conn = get_connection(server_num + 1)
    with open(abs_path) as f:
        total_files = 0
        migrated_files = 0
        line = f.readline().strip()
        while line:
            if os.path.isfile(line):
                total_files = total_files + 1

                old_server_iter = _conn._get_server(line)
                new_server_iter = _new_conn._get_server(line)
                if old_server_iter != new_server_iter:
                    migrated_files = migrated_files + 1

            line = f.readline().strip()
        print 'Total files = %s, Migrated files = %s' % \
               (total_files, migrated_files)
        print 'Migrate Rate = %.02f%%' % \
               (100.0 * float(migrated_files)/float(total_files))

if __name__ == '__main__':
    main()
