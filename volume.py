import boto3
import os
from datetime import datetime
import sys
import configargparse


def lambda_handler(event, context):
    p = configargparse.getArgumentParser()
    p.add_argument('--region', '-r', default="us-east-1", help="AWS region containing snapshots", nargs="+",env_var="REGION")
    p.add_argument('--delete','-del',help="To delete the resources found",action='store_true',default=False,env_var="DELETE")
    args = p.parse_args()

    for region in args.region:
        ec2 = boto3.resource('ec2', region_name=region)
        volume = ec2.Volume('id')
        s3 = boto3.resource('s3')
        s3_client = boto3.client('s3')
        volumes_available = ec2.volumes.filter(Filters=[{'Name': 'status', 'Values': ['available']}])
        volume_id = []
        for volume in volumes_available:
            volume_id.append(volume.id)

        volume_file = open("/tmp/volume-file", "w+")
        with volume_file as fh:
            for vol in volume_id:
                fh.write(vol)
                fh.write("\n")

        with open("/tmp/volume-file", "rb") as f:
            s3_client.upload_fileobj(f, "cleanup-s3", "volume-file")

        if args.delete:
            for volume in volumes_available:
                volume.delete()
                return
        else:
            return("No actions was taken on the available volumes")

    
