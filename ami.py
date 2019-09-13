

Skip to content
Using Gmail with screen readers
sujitha@terpmail.umd.edu 

5 of 35
cleanup-terraform-lambda

Sujitha Rajan <sujithasrajan.sr26@gmail.com>
Attachments
12 Aug 2019, 14:39
to sujitha

PFA
15 Attachments

import boto3
import sys
import argparse
from datetime import datetime
import sys
import os
import time
import configargparse


def lambda_handler(event,context):
    list_of_ami = []
    list_of_amiID = []
    list_delete_snapshot = []
    list_instance_amiID = []
    list_delete_ami = []

    p = configargparse.getArgumentParser()
    p.add_argument('--pattern', '-p', help="Regular expression pattern used to filter AMI names", type=str,
                        nargs="+",env_var="PATTERN")
    p.add_argument('--region', '-r', default="us-east-1", help="AWS region containing snapshots", nargs="+",env_var="REGION")
    p.add_argument('--latest_count', '-lc',help="The total no. of the most recent AMI you want to keep",type=int,env_var="LATEST_COUNT")
    p.add_argument('--delete','-del',help="To delete the resources found",action='store_true',default=False,env_var="DELETE")
    args = p.parse_args()

    for region in args.region:
        my_session = boto3.session.Session(region_name=region)
        ec2 = my_session.client('ec2')
        ami_response = ec2.describe_images(Filters=[{'Name': 'tag:Name', 'Values': args.pattern}],Owners=['self'])
        s3 = boto3.resource('s3')
        s3_client = boto3.client('s3')


#AMI-ID Associated with instances in the LIST: list_instance_amiID without duplication
        client = boto3.client('ec2',region_name=region)
        response = client.describe_instances()
        for reservation in response["Reservations"]:
            for instance in reservation["Instances"]:
                instance_amiID = instance['ImageId']
                if not instance_amiID in list_instance_amiID:
                    list_instance_amiID.append(instance_amiID)



    #AMI-ID of all the AMI with its name and creation date sorted from the most latest to the least latest
        for ami in ami_response['Images']:
            for tag in ami['Tags']:
                if tag['Key'] == 'Name':
                    name = tag['Value']
                    list_of_ami.append({'date': ami['CreationDate'], 'ami_id': ami['ImageId'], 'Name': tag['Value']})
                    list_of_ami.sort(key=lambda x: x['date'],reverse=True)
        for ami_id in list_of_ami:
            list_of_amiID.append(ami_id['ami_id'])
    #List of total ID's of the AMI available for the name search checked if it has less number of AMI's than we want to store
        if len(list_of_amiID) > args.latest_count:
            list_of_amiID = list_of_amiID[args.latest_count:]

            #Checks if there is any instances associated to the AMI
            list_delete_ami = [x for x in list_of_amiID if x not in list_instance_amiID]

            #*SNAPSHOTS* associated with AMI that are to be deleted
            for ami_id in list_delete_ami:
                response_snapshot = client.describe_images(ImageIds=[ami_id])
                for images in response_snapshot['Images']:
                    for device in images['BlockDeviceMappings']:
                        try:
                            snapshotID = device['Ebs']['SnapshotId']
                        except KeyError:
                            continue
                        else:
                            list_delete_snapshot.append(snapshotID)
            for ami_id in list_delete_ami:
                if args.delete:
                    client.deregister_image(ImageId=ami_id)

            for id in list_delete_snapshot:
                if args.delete:
                    client.delete_snapshot(SnapshotId=id)

        #Writes the deleted AMI details to the File ami-delete
            ami_deleted = open("/tmp/ami-delete", "w+")
            with ami_deleted as fh:
                fh.write("The number of AMI's cleaned: {}".format(len(list_delete_ami)))
                fh.write("\n")
                fh.write("The number of AMI's cleaned: {}".format(len(list_delete_ami)))
                fh.write("\n")
                for id in list_delete_ami:
                    fh.write("\n")
                    fh.write(region)
                    fh.write("\n")
                    fh.write("ami-id:      ")
                    fh.write(id)
                    fh.write("\n")
                for id in list_delete_snapshot:
                    fh.write("\n")
                    fh.write("snapshot-id: ")
                    fh.write(id)
                    fh.write("\n")
            with open("/tmp/ami-delete", "rb") as f:
                s3_client.upload_fileobj(f, "cleanup-s3", "ami-delete")

            return 
        else:
            return("There are less than {} AMI for your name query".format(args.latest_count))


