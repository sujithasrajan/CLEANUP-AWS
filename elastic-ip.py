import boto3
import sys
import configargparse
from datetime import datetime
import sys
import os
import time

def lambda_handler(event,context):
    p = configargparse.getArgumentParser()
    p.add_argument('--region', '-r', default="us-east-1", help="AWS region containing snapshots", nargs="+",env_var="REGION")
    p.add_argument('--delete','-del',help="To delete the resources found",action='store_true',default=False,env_var="DELETE")
    args = p.parse_args()

    for region in args.region:
        s3_client = boto3.client('s3')
        s3 = boto3.resource('s3')
        client = boto3.client('ec2', region_name=region)
        response = client.describe_addresses()
        eips = []
        for address in response['Addresses']:
            if 'NetworkInterfaceId' not in address:
                eips.append(address['PublicIp'])

        eip_file = open("/tmp/eip_file","w+")
        with eip_file as fh:
            for eip in eips:
                fh.write("Public Ip: ")
                fh.write(eip)
                fh.write("\n")

        with open("/tmp/eip_file", "rb") as f:
                s3_client.upload_fileobj(f, "cleanup-s3", "eip_file")

        for ip in eips:
            if args.delete:
                try:
                    ec2.release_address(PublicIp=ip)
                except ClientError as e:
                    continue
    return
