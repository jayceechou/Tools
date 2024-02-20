'''
1. count ping pakcets:
    a. how many transmitted
    b. how many received
    c. how many lost
    d. % packet loss
2. round-trip:
    a. min
    b. avg
    c. max
    d. stddev
3. percentiles:
    default: 25th, 50th, 75th
4. Count # of packets for consecutive packet timeouts    
'''

import re
import numpy
import statistics

def read_ping_frm_file(filename):
    pattern = r'icmp_seq=([0-9]+).*time=([0-9]+\.[0-9]+)'
    icmp = {}
    
    with open(filename) as f:
        for line in f.readlines():
            match = re.search(pattern, line.rstrip())
            if match:
                seq, t = match.groups()
                icmp[int(seq)] = float(t)
    return icmp    


def getPercentage(num1, num2):
    return (float(num1) / float(num2) * 100)


def countMissingPackets(seq_list):
    count = 0
    for i in range(min(seq_list), max(seq_list) + 1):
        if i not in seq_list:
            count += 1
    return count


def missingPackets(seq_list):
    missingPackets = []
    for i in range(min(seq_list), max(seq_list) + 1):
        if i not in seq_list:    
            missingPackets.append(i)
    return missingPackets


def getTimeout(timeout_packets, seq_list):
    #print(seq_list)
    if not timeout_packets.isnumeric():
        print('Invalid Input!')
        exit()
    if int(timeout_packets) < 1:
        exit()
    timeout_list = []
    for i in range(len(sorted(seq_list))):
        if seq_list[i] == seq_list[-1]:
            break
        elif (seq_list[i + 1] - seq_list[i]) > int(timeout_packets):
            timeout_list.append((seq_list[i], seq_list[i + 1]))
    return timeout_list


def getPercentiles(seq_list, nums):
    if not seq_list or not nums or type(nums) != list:
        print('Invalid Percentile!')
        exit()
    values = {}
    for num in nums:
        values[num] = numpy.percentile(seq_list, num)
    return values
        

def main():
    filename = input('\n1. Enter a \'ping\' filename: ')
    icmp = read_ping_frm_file(filename)

    transmitted_packets = max(icmp.keys()) - min(icmp.keys()) + 1
    loss_packets = countMissingPackets(icmp.keys())
    received_packets = transmitted_packets - loss_packets
    print('\n{} packets transmitted, {} packets received, {} packets lost, {:.2f}% packet loss'.format(transmitted_packets, received_packets, loss_packets, getPercentage(loss_packets, received_packets)))
    print('round-trip min/avg/max/stddev = {:.3f} / {:.3f} / {:.3f} / {:.3f} ms'.format(min(icmp.values()), sum(icmp.values()) / received_packets, max(icmp.values()), statistics.stdev(icmp.values())))
    
    request_percentiles_values = [25, 50, 75]
    percentiles = getPercentiles(list(icmp.values()), request_percentiles_values)    
    print('percentile 25th/50th/75th = {:.3f} / {:.3f} / {:.3f} ms'.format(percentiles[25], percentiles[50], percentiles[75]))

    max_timeout_packets = input('\n2. Enter a number to indicate max consecutive packet timeouts (\'0\' to quit): ')
    timeout_list = getTimeout(max_timeout_packets, sorted(icmp.keys()))
    if not timeout_list:
        print('No match!')
    else:
        for item in timeout_list:
            p1, p2 = item
            print('seq {} to {} - {:5d} packets lost'.format(p1, p2, p2 - p1 - 1))
    print()


if __name__ == '__main__':
    main()