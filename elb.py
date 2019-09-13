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
        client = boto3.client('elb', region_name=region)
        response = client.describe_load_balancers()
        elbs=[]
        for ELB in response['LoadBalancerDescriptions']:
            if len(ELB['Instances']) == 0:
                elbs.append(ELB['LoadBalancerName'])


        elb_file = open("/tmp/elb_file","w+")
        with elb_file as fh:
            for elb in elbs:
                fh.write("elb name: ")
                fh.write(elb)
                fh.write("\n")
        with open("/tmp/elb_file", "rb") as f:
                s3_client.upload_fileobj(f, "cleanup-s3", "elb_file")

        for id in elbs:
            if args.delete:
                client.delete_load_balancer(LoadBalancerName=id)

    return
