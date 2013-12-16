

def count_balance_rate(record):
    avg_cnt = float(float(sum(record)) / float(len(record)))
    max_cnt = float(max(record))
    min_cnt = float(min(record))

    over = 100.0 * (max_cnt - avg_cnt) / avg_cnt
    under = 100.0 * (avg_cnt - min_cnt) / avg_cnt

    print 'max = %s, min = %s, avg = %.02f%%' % (max_cnt, min_cnt, avg_cnt)
    print 'over = +%.02f%%, under = -%0.02f%%' % (over, under)
    return over, under

def main():
    server_cnt = data = [136, 123, 139, 122, 125]
    over, under = count_balance_rate(server_cnt)

if __name__ == '__main__':
    main()

