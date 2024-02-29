'''
Features:
1. Run As: $ ping_statistics.py filename1,filename2
    1) Takes one or more filenames as default requirement.
    2) Filenames are seperated by ','

2. Pakcets Count & RTT
    1) # of packets transmitted 
    2) # of packets received
    3) # of packets lost
    4) % of packets loss
    5) min RTT
    6) avg RTT
    7) max RTT
    8) stddev RTT
    9) The above is the default output which would be send to STDOUT.

3. Percentile Calculation (-p)
    1) Calculated percentile per requested values from STDIN.
    2) e.g. With '-p 10,20,30', it'd generate 10th, 20th, 30th percentiles. 
    3) Constraints: Input one or more integers between 0-100 that seperate the numbers by ','

4. Timeout Consecutively (-t)
    1) List lost-packet counts per requested consecutive-timeout period.
    2) e.g. With '-t 5', it'd display the total lost-packet counts which is larger than 0 per 5 seconds (per 5 sequences).
    3) Input only one integer between 1 and the max packets of the input file.

5. Counts of Lost-Packets during a Time-Period (-c)
    1) Input one or more integer values that seperate the numbers by ','
    2) The minimum value for the duration of time should be at least 1.
    3) The maximum value for the duration of time would be the max packets of the input file.
    4) e.g. With '-c 10,20', it'd list the total counts of each time period.

6. Convert one or more input file to a CSV and a Graph
    1) Default CSV filename: rtt.csv
    2) Default Graph file: rtt.html
    3) With '-g [name]' option, the default CSV and Graph would be replaced by [name].csv and [name].html.

7. Output the result to a CSV file
    1) "Counts of Lost-Packets during a Time-Period", it would only show:
        a. The number of incidents that happened 
        b. The max number for the lost packets
    2) Default output filename: output.csv
    3) With '-o [filename]' option, the default output will be replaced by filename.

Notice:
1. Exclude the timed-out packets that occur before the 1st successful ping packet. 
    (As in test02.txt, ignore timeouts before line 7.)
2. Exclude the timed-out packets that occur after the last successful ping packet. 
    (As in test02.txt, ignore timeouts before line 46.)
'''
import re
import numpy
import argparse
import statistics
import pandas as pd
import plotly.offline as pyo
import plotly.graph_objects as go


def go_parser():
    parser = argparse.ArgumentParser(description = 'Ping Statistics')
    parser.add_argument('filenames',
                        help = 'Input the name of the file(s) that contain(s) the ping output, separated by \',\' if more than one file.')
    parser.add_argument('-t', '--timeout', action = 'store', dest = 'timeout',
                        help = 'Input a single integer between 1 and the maximum number of packets in the input file for the maximum consecutive timeout.')    
    parser.add_argument('-p', '--percentiles', action = 'store', dest = 'percentiles',
                        help = 'Input value(s) (0-100), sepearted by \',\' if there is more than one value.')
    parser.add_argument('-c', '--count', action = 'store', dest = 'count',
                        help = 'Input number(s) for the duration of time period, sepearted by \',\' if more than one number')
    parser.add_argument('-g', '--graph', action = 'store', dest = 'graph',
                        help = 'Input a name for the csv and the graph files (default is \'rtt\' for rtt.csv and rtt.html')        
    parser.add_argument('-o', '--output', action = 'store', dest = 'output',
                        help = 'Input the output filename (default is output.csv)')

    args = parser.parse_args()
    return args    

'''
Read in ping output from a file.
'''
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


'''
Write the result to a file in CSV format. (-o)
'''
def output_to_file(lines:str, filename: str) -> bool:   
    try:
        with open(filename, 'w') as f:
            f.write(lines)
    except FileNotFoundError as e:
        print(e)
    return True 


'''
Covert the ping output of all input files to a CSV file. (-g)
'''
def convert_to_CSV(rtt: dict, filename: str) -> str:
    if not rtt:
        print('Invalid Round-Trip Time for CSV file!')
        exit()

    lines = 'File,Packet,RTT(ms)\n'
    for file, values in rtt.items():
        for i in range(0, len(values)):
            lines += '{},{},{}\n'.format(file,i + 1, values[i])
    try:
        with open(filename + '.csv', 'w') as f:
            f.write(lines)
    except FileNotFoundError as e:
        print(e)
    return lines 


'''
Generate a graph from converted ping output from a CSV file. (-g)
'''
def getGraph(rtt: dict, filename: str) -> bool:
    if not rtt:
        print('Invalid Round-Trip Time for graph!')
        exit()

    #  In order to make sure x-axis has enough values, 
    # sorted files by packet numbers in descending order 
    files = {}
    for file, rtt_list in rtt.items():
        files[file] = len(rtt_list)
    files = [file for file, v in list(sorted(files.items(), key=lambda item: item[1], reverse=True))]

    try:
        df = pd.read_csv(filename + '.csv')
    except FileNotFoundError as e:
        print(e)
        return False  

    data = []
    for file in files:
        trace = go.Scatter(x=df[df['File']==file]['Packet'],
                           y=df[df['File']==file]['RTT(ms)'],
                           mode='lines+markers',
                           name=file)
        data.append(trace)
    layout = go.Layout(title = 'Ping Statistics')
    fig = go.Figure(data=data,layout=layout)
    pyo.plot(fig, filename=filename + '.html')
    return True


'''
Calculate percentage for loss packets
'''
def getPercentage(num1: int, num2: int) -> float:
    return (float(num1) / float(num2) * 100)


'''
Counts lost packets
'''
def countMissingPackets(seq_list: list) -> int:
    count = 0
    for i in range(min(seq_list), max(seq_list) + 1):
        if i not in seq_list:
            count += 1
    return count


'''
Retrieve the sequence number before and after the requested consecutive timeout period (-t)
'''
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


'''
Calculate Percentile(s) (-p)
'''
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


'''
Display the number of lost packets during the requested time period. (-c)
'''
def getPacketsPerTimePeriod(time_period: list, seq_list:list) -> dict:
    if not time_period or not seq_list:
        print('Invalid Time Period Value!')
        exit()
    periods = {}
    for time in time_period:
        if type(time) != int or int(time) < 1 or (time >= max(seq_list) - min(seq_list)):
            print('Invalid Integer Value!')
            return {}
            
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
    rtt_filename = 'rtt'
    rtt = {}
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
                + str(loss_packets) + ' packets,' + '{:.2f}%'.format(packet_loss_rate) + ','

        # RTT
        print('\n // Round-Trip Time //')
        print(' Round-trip min    = {:9.3f} ms'.format(min(icmp.values())))
        print(' Round-trip max    = {:9.3f} ms'.format(max(icmp.values())))
        print(' Round-trip avg    = {:9.3f} ms'.format(sum(icmp.values()) / received_packets))
        print(' Round-trip stddev = {:9.3f} ms'.format(statistics.stdev(icmp.values())))
        lines += '{:.3f} ms,'.format(min(icmp.values())) + '{:.3f} ms,'.format(max(icmp.values())) \
                + '{:.3f} ms,'.format(sum(icmp.values()) / received_packets) + '{:.3f} ms,'.format(statistics.stdev(icmp.values()))
               
        # Percentile Calculation (-p)
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

        # Timeout Consecutively (-t)
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

        # Counts of Lost-Packets during a Time-Period (-c)
        if args.count:
            print('\n // Lost-Packet Counts during a Time-Period //')
            try:
                time_period_values = list(map(int, re.split(r'\D+', args.count)))
                time_periods = getPacketsPerTimePeriod(time_period_values, sorted(icmp.keys()))
                if time_periods:
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

        # for RTT Graph
        rtt[filename] = list(icmp.values())

    # Output to a CSV file
    if args.output:
        output_filename = args.output
    output_to_file(title + '\n' + lines, output_filename)

    # Output RTT and its graph to a CSV and a HTML file
    if args.graph:
        rtt_filename = args.graph
    convert_to_CSV(rtt, rtt_filename)
    getGraph(rtt, rtt_filename)


if __name__ == '__main__':
    main()