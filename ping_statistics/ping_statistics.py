'''
1. Pakcets Count & RTT:
    a. # of packets transmitted 
    b. # of packets received
    c. # of packets lost
    d. % of packets loss
    e. min RTT
    f. avg RTT
    g. max RTT
    h. stddev RTT
2. Percentile Calculation
    a. Constraints: 
        Input one or more integer between 0-100
3. Consecutive Timeouts
    a. Notice:
        a1. Exclude the timed-out packets that occur before the 1st successful ping packet. 
            (As in test02.txt, ignore timeouts before line 7.)
        a2. Exclude the timed-out packets that occur after the last successful ping packet. 
            (As in test02.txt, ignore timeouts before line 46.)
    b. Constraints: 
        Input one integer
4. Lost-Packets during a Time-Period (How many packets were lost during the requested time period?)
    a. Constraints: 
        a1. Input one or more integer values
        a2. The minimum value for the duration of time should be at least 1.
        a3. The maximum value for the duration of time would be the max packets of the input file.
5. Output to output.csv file by default
    a. For Lost-Packet during a Time-Period section, it would only include:
        a1. The number of incidents that happened 
        a2. The max number for the lost packets
'''
import re
import numpy
import argparse
import textwrap
import statistics


def go_parser():
    parser = argparse.ArgumentParser(description = 'Ping Statistics')
    parser.add_argument('filenames',
                        help = 'List the files that contain(s) ping outputs, sepearted by \',\'')
    parser.add_argument('-p', '--percentiles', action = 'store', dest = 'percentiles',
                        help = 'List percentile value(s) (0-100), sepearted by \',\'')
    parser.add_argument('-t', '--timeout', action = 'store', dest = 'timeout',
                        help = 'Enter an Integer for the MAX Consecutive Timeout Packet(s)/Second(s)')
    parser.add_argument('-c', '--count', action = 'store', dest = 'count',
                        help = 'Enter a list of number(s) for the duration of time period, sepearted by \',\'')
    parser.add_argument('-o', '--output', action = 'store', dest = 'output',
                        help = 'Enter the output filename (default is output.csv)')
    args = parser.parse_args()
    return args    


def read_ping_frm_file(filename: str) -> dict:
    pattern = r'icmp_seq=([0-9]+).*time=([0-9]+\.[0-9]+)'
    icmp = {}
    
    try:
        with open(filename) as f:
            for line in f.readlines():
                match = re.search(pattern, line.rstrip())
                if match:
                    seq, t = match.groups()
                    icmp[int(seq)] = float(t)
    except FileNotFoundError as e:
        print(e)
    return icmp    


def write_to_file(lines:str, filename: str):   
    try:
        with open(filename, 'w') as f:
            f.write(lines)
    except FileNotFoundError as e:
        print(e)
    return True   


def getPercentage(num1: int, num2: int) -> float:
    return (float(num1) / float(num2) * 100)


def countMissingPackets(seq_list: list) -> int:
    count = 0
    for i in range(min(seq_list), max(seq_list) + 1):
        if i not in seq_list:
            count += 1
    return count


def getTimeout(timeout_packets:int, seq_list: list) -> list:
    if int(timeout_packets) < 1:
        exit()
    timeout_list = []
    for i in range(len(sorted(seq_list))):
        if seq_list[i] == seq_list[-1]:
            break
        elif (seq_list[i + 1] - seq_list[i]) > int(timeout_packets):
            timeout_list.append((seq_list[i], seq_list[i + 1]))
    return timeout_list


def getPercentiles(seq_list: list, nums: list) -> dict:
    if not seq_list or not nums:
        print('Invalid Percentile!')
        exit()
    values = {}
    for num in nums:
        try:
            values[num] = numpy.percentile(seq_list, num)
        except ValueError as e:
            print(e)
    return values


def getPacketsPerTimePeriod(time_period: list, seq_list:list) -> dict:
    if not time_period or not seq_list:
        print('Invalid Time Period Value!')
    periods = {}
    for time in time_period:
        if type(time) != int or int(time) < 1 or (time >= max(seq_list) - min(seq_list)):
            print('Invalid Integer Value!')
            exit()
            
        for i in range(0, max(seq_list) - min(seq_list) + 1, time):
            # time period should not be over the last icmp_seq #
            if min(seq_list) + i + time - 1 > max(seq_list):
                last_seq = max(seq_list)
            else:
                last_seq = min(seq_list) + i + time - 1
            
            # packet count
            packet_count = 0
            for j in range(time):
                if min(seq_list) + i + j > max(seq_list):
                    break
                if min(seq_list) + i + j not in seq_list:
                    packet_count += 1

            if time not in periods:
                periods[time] = [[min(seq_list) + i, last_seq, packet_count]]
            else:
                periods[time].append([min(seq_list) + i, last_seq, packet_count])
    return periods



def main():
    args = go_parser()
    output_filename = 'output.csv'
    lines = ''
    title = ''

    for filename in args.filenames.split(','):
        print('------------------\n {} \n------------------'.format(filename))        
        icmp = read_ping_frm_file(filename)
        title = 'File Name,Transmitted,Received,Packet Loss, Loss Rate,RTT Min,RTT Max,RTT Avg,RTT STDDEV,'
        lines += filename + ','

        # Packet Count
        transmitted_packets = max(icmp.keys()) - min(icmp.keys()) + 1
        loss_packets = countMissingPackets(icmp.keys())
        received_packets = transmitted_packets - loss_packets
        packet_loss_rate = getPercentage(loss_packets, transmitted_packets)
        print('\n // Packet Counts //')
        print(' Transmitted   {:6d} packets'.format(transmitted_packets))
        print(' Received      {:6d} packets'.format(received_packets))
        print(' Lost          {:6d} packets'.format(loss_packets))
        print(' Packet Loss Rate is {:5.2f}%'.format(packet_loss_rate))
        lines += str(transmitted_packets) + ' packets,' + str(received_packets) + ' packets,' \
                + str(loss_packets) + ' packets,' + '{:.2f}%'.format(packet_loss_rate) + '%,'

        # RTT
        print('\n // Round-Trip Time //')
        print(' Round-trip min    = {:9.3f} ms'.format(min(icmp.values())))
        print(' Round-trip max    = {:9.3f} ms'.format(max(icmp.values())))
        print(' Round-trip avg    = {:9.3f} ms'.format(sum(icmp.values()) / received_packets))
        print(' Round-trip stddev = {:9.3f} ms'.format(statistics.stdev(icmp.values())))
        lines += '{:.3f} ms,'.format(min(icmp.values())) + '{:.3f} ms,'.format(max(icmp.values())) \
                + '{:.3f} ms,'.format(sum(icmp.values()) / received_packets) + '{:.3f} ms,'.format(statistics.stdev(icmp.values()))
               
        # Percentile Calculation
        if args.percentiles:
            print('\n // Percentiles //')
            try:
                percentiles_values = list(map(int, re.split(r'\D+', args.percentiles)))
                percentiles = getPercentiles(list(icmp.values()), percentiles_values)
                if not percentiles:
                    print('[ Error occured on calculating percentile! ]')
                else:
                    print(''.join(['{:3d}th Percentile is {:9.3f} ms\n'.format(percentile, value) for percentile, value in percentiles.items()]))
                    title += ''.join(['{:3d}th Percentile,'.format(p) for p in percentiles.keys()])
                    lines +=  ''.join(['{:.3f} ms,'.format(percentiles[p]) for p in percentiles.keys()])                    
            except ValueError as e:
                print('[ Error on Percentiles: {} ]'.format(e))

        # Consecutive Timeouts
        if args.timeout:
            print('\n // Consecutive Timeouts //')
            if not args.timeout.isnumeric() or int(args.timeout) < 0 or int(args.timeout) >= max(icmp.keys()) -  min(icmp.keys()):
                print('[ Error on Timeout Value: \'{}\' ]'.format(args.timeout))
            else:
                timeout_list = getTimeout(args.timeout, sorted(icmp.keys()))
                title += 'Consecutive Timeout ' + str(args.timeout) + ' packets,'
                if not timeout_list:
                    print('[ No Match on Timeout Value: \'{}\' ]'.format(args.timeout))
                    lines += 'No Match!,'
                else:
                    print(''.join([' Seq {} to {} : {:5d} packets lost\n'.format(p1, p2, p2 - p1 - 1) for p1, p2 in timeout_list]))
                    lines += '"'
                    lines += ''.join(['Seq {} to {} : {:d} packets lost\n'.format(p1, p2, p2 - p1 - 1) for p1, p2 in timeout_list])
                    lines += '",'

        # Lost-Packet Count during a Time-Period
        if args.count:
            print('\n // Lost-Packet Counts during a Time-Period //')
            try:
                time_period_values = list(map(int, re.split(r'\D+', args.count)))
                time_periods = getPacketsPerTimePeriod(time_period_values, sorted(icmp.keys()))
                for time_period, v in time_periods.items():
                    print('Per {} packets/seconds -- '.format(time_period))
                    print(''.join([' Seq {} to {} lost {} packets\n'.format(p1, p2, count) for p1, p2, count in v if count > 0]))
                    title += '# of Incidents Per '+ str(time_period) + ' Packets,'
                    sum_incident = max_packet_lost = 0
                    for *p,count in v:
                        if count > 0:
                            sum_incident += 1
                        if count > max_packet_lost:
                            max_packet_lost = count
                    lines += '{} Incidents (Max {} packets lost),'.format(sum_incident, max_packet_lost)
            except ValueError as e:
                print('[ Error on Lost-Packet Count: {} ]'.format(e))        
        lines += '\n'

    # Output to a CSV file
    if args.output:
        output_filename = args.output            
    #print(title + '\n' + lines)      
    write_to_file(title + '\n' + lines, output_filename)

if __name__ == '__main__':
    main()