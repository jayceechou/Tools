## Introduction

A tool to analyze ping output:  
1. ping pakcets:
    a. how many transmitted
    b. how many received
    c. how many lost
    d. % packet loss
2. round-trip time:
    a. min
    b. avg
    c. max
    d. stddev
3. percentiles:
    default: 25th, 50th, 75th
4. Count # of packets for consecutive packet timeouts    

## Instruction

1. Install requirement

```console
% pip3 install -r requirements.txt
```


2. Run As:

```console
% python3 ping_statistics.py

1. Enter a 'ping' filename: test01.txt

73 packets transmitted, 33 packets received, 40 packets lost, 121.21% packet loss
round-trip min/avg/max/stddev = 68.441 / 245.693 / 1490.029 / 337.364 ms
percentile 25th/50th/75th = 80.824 / 104.853 / 167.365 ms

2. Enter a number to indicate max consecutive packet timeouts ('0' to quit): 2
seq 12548 to 12551 -     2 packets lost
seq 12554 to 12562 -     7 packets lost
seq 12565 to 12596 -    30 packets lost
```