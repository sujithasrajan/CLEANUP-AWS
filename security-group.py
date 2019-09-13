
#-----------------------
#Lists the unused SG_id
#-----------------------

import os
import boto3
import csv
import os
from datetime import datetime
import tempfile
import logging
import configargparse


def lambda_handler(event, context):
    p = configargparse.getArgumentParser()
    p.add_argument('--region', '-r', default="us-east-1", help="AWS region containing snapshots", nargs="+",env_var="REGION")
    args = p.parse_args()
    for region in args.region:

        ec2 = boto3.resource('ec2',region_name = region)
        security_group = ec2.SecurityGroup('id')
        s3 = boto3.client('s3')

        sg_id = []
        sgs = ec2.security_groups.all()
        for sg in sgs:
            sg_id.append(sg.group_id)

        instances = ec2.instances.all()

        ec2_sg_id = []

        for instance in instances:
            for sg in instance.security_groups:
                ec2_sg_id.append(sg['GroupId'])

        unused_sg_id = list(set(sg_id) - set(ec2_sg_id))
    
        # Upload the file
    
        sg_file = open("/tmp/sg-file","w+")
        with sg_file as fh:
            for sg in unused_sg_id:
                fh.write(sg)
                fh.write("\n")
    
    
        with open("/tmp/sg-file", "rb") as f:
            s3.upload_fileobj(f, "cleanup-s3", "sg-file+ str(datetime.now().strftime('%Y_%m_%d_%H_%M_%S')) + region)")
    
    return
