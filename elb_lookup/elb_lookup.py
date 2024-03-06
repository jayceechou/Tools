from typing import List
import helper
import argparse
import subprocess
import json


def go_parser():
    parser = argparse.ArgumentParser(description = 'ELB to IP and DNS lookup')
    parser.add_argument('-l', '--list_dns', action = 'store_true',
                        help = 'List IP to omit.')
    parser.add_argument('-a', '--add_dns', action = 'store_true',
                        help = 'Add IP to omit list.')    
    parser.add_argument('-g', '--generate', action = 'store', dest = 'zone_id',
                        help = 'generate a URL list from elb_dns and route53_zone with IP addresseses and Zone names') 
    parser.add_argument('-o', '--output', action = 'store', dest = 'output_filename',
                    help = 'save to a file') 
    args = parser.parse_args()

    return args


def add_DNS(public_dns_obj:dict, text:str) -> dict:
    if not text:
        print("Error: Input is empty!")
        return False

    ip_address = helper.get_ipv4(text)
    if not public_dns_obj['public_DNS']:
        return ip_address
    
    for ip in ip_address:
        if ip not in public_dns_obj['public_DNS']:
            public_dns_obj['public_DNS'].append(ip)

    return public_dns_obj


def get_all_load_balancer_dns_urls(public_dns:dict, command:List) -> dict:
    """
    Gets all load balancer DNS URLs using `awscli`.
    
    Returns:
        A dictionary of all load balancer DNS URLs and each corespondding IP.
    """
    if not command:
        return {}
    
    cmd_obj = {}
    try:
        output = subprocess.check_output(command)
        cmd_obj = json.loads(output.decode())
    except Exception as e:
        print(e)

    # ELB URLs
    urls = []
    for i in range(len(cmd_obj)):
        if cmd_obj[i][1] not in urls:
            urls.append(cmd_obj[i][1])       
    

    ip_address = {}
    for url in urls:
        ipv4 = do_nslookup(public_dns['public_DNS'], url)
        ip_address[url] = ipv4

    return ip_address


def do_nslookup(public_dns:list, url:str) -> list:
    """
    Performs an `nslookup` against the given load balancer DNS URL.

    Args:
        url: The load balancer DNS URL to perform the `nslookup` against.
        public_dns: Output should remove public DNS name servers.

    Returns:
        The IP address of the load balancer without public DNS servers.
    """
    if not url:
        return []

    try:
        output = subprocess.check_output(["nslookup", url])
    except Exception as e:
        print(e)    
    
    ip_address = []
    ipv4 = helper.get_ipv4(output)
    if not ipv4:
        return []
    else:
        for ip in ipv4:
            if public_dns and ip not in public_dns:
                ip_address.append(ip)
        return ip_address
    

def get_all_route53_dns(command:List) -> dict:
    if not command:
        return False
    
    py_obj = {}
    try:
        output = subprocess.check_output(command)
        py_obj = json.loads(output.decode())
    except Exception as e:
        print(e)
    #helper.go_pprint(py_obj, 2)

    zones = {}
    if len(py_obj['ResourceRecordSets']) < 1:
        return {}
    else:
        for i in range(len(py_obj['ResourceRecordSets'])):
            if 'AliasTarget' in py_obj['ResourceRecordSets'][i].keys():
                DNSName = py_obj['ResourceRecordSets'][i]['AliasTarget']['DNSName'][:-1]
                Name = py_obj['ResourceRecordSets'][i]['Name']
                if DNSName not in zones.keys():
                    zones[DNSName] = [Name]
                else:
                    zones[DNSName].append(Name)
        # helper.go_pprint(zones, 2)
        return zones


def generate(dict1:dict, dict2:dict) -> dict:
    if not dict1 or not dict2:
        return {}
    
    dns_dict = {}
    for url, names in dict1.items():
        if url not in dns_dict.keys():
            dns_dict[url] = {}
            dns_dict[url]['Names'] = names
        if url in dict2.keys():
            dns_dict[url]['IPs'] = dict2[url]
        else:
            dns_dict[url]['IPs'] = []

    for url, ip_list in dict2.items():
        if url not in dns_dict.keys():
            dns_dict[url] = {}
        if url not in dict1.keys():
            dns_dict[url]['IPs'] = ip_list
            dns_dict[url]['Names'] = []
    return dns_dict



if __name__ == "__main__":

    args = go_parser()
    settings_file = 'settings.txt'
    public_dns_obj = helper.load_json(settings_file)
    command = []
    route53_dns = {}
    load_balancer_dns_urls = {}

    if args.list_dns:
        print('Current stored public DNS servers: {}'.format(', '.join([s for s in public_dns_obj['public_DNS']])))

    if args.add_dns:
        public_dns_obj = add_DNS(public_dns_obj, input('Please enter DNS IP address: '))
        if helper.save_json(public_dns_obj, settings_file):
            print('Updated stored public DNS servers: {}'.format(', '.join([s for s in public_dns_obj['public_DNS']])))
        else:
            print('Error occurs at saving public DNS servers to file: {}'.format(settings_file))                
    
    if args.zone_id:
        command = ["aws", "elbv2", "describe-load-balancers", "--query", "LoadBalancers[*].[LoadBalancerName,DNSName]"]
        elb_ip_address = get_all_load_balancer_dns_urls(public_dns_obj, command)
        #helper.go_pprint(elb_ip_address, 2)
 
        command = ["aws", "route53", "list-resource-record-sets", "--hosted-zone-id", args.zone_id, "--no-cli-pager"]
        route53_dns = get_all_route53_dns(command)
        #helper.go_pprint(route53_dns, 2)

        result = generate(route53_dns, elb_ip_address)
        if result:
            helper.go_pprint(result, 4)

    if args.output_filename:
        if not result:
            print("Error: please use `-g` to generate result.")
        else:
            helper.save_json(result, args.output_filename)