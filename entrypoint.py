#!/usr/local/bin/python3.6
""" Simple lambda to lookup the default VPC and signal back to CloudFormation """
# Portions of this code copyright Amazon
# https://amzn.to/2FWF9bE
# Copyright 2016 Amazon Web Services, Inc. or its affiliates. All Rights Reserved.
# This file is licensed to you under the AWS Customer Agreement (the "License").
# You may not use this file except in compliance with the License.
# A copy of the License is located at http://aws.amazon.com/agreement/ .
#
# This file is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS
# OF ANY KIND, express or implied.
# See the License for the specific language governing permissions and limitations
# under the License.


import pprint
import logging
import json

import boto3
import requests

# import cfnresponse
# from botocore.vendored import re

def get_default_vpc(region):
    """Looks up the default VPC and returns it or ''"""
    ec2client = boto3.client('ec2', region_name=region)
    print_print = pprint.PrettyPrinter(indent=4)
    response = ec2client.describe_vpcs(Filters=[{'Name': 'isDefault', 'Values': ['true']}])

    logging.debug("Received response from AWS, VPC list is")
    logging.debug(print_print.pformat(response["Vpcs"]))

    vpcs = response["Vpcs"]
    vpc_id = ""

    # we want one and only one VPC in the list.  It's the default and that should
    # mean only one.  The other possible value would be 0 if the default VPC was deleted.
    if len(vpcs) != 1:
        logging.critical("Error, No VPC Found")

    else:
        logging.info("response has %d elements ", len(vpcs))
        vpc_id = vpcs[0]["VpcId"]
        logging.info("Found Default VPC Id %s", vpc_id)

    return vpc_id


def send(event, context, response_status, response_data, physical_resource_id=None, no_echo=False):
    """Send CF Response"""
    response_url = event['ResponseURL']
    logging.warning("context")
    print_print = pprint.PrettyPrinter(indent=4)
    logging.warning(print_print.pformat(context))

    logging.debug("Response URL is :%s", response_url)

    response_body = {}
    response_body['Status'] = response_status
    response_body['Reason'] = 'See the details in CloudWatch Log Stream: ' + context.log_stream_name
    response_body['PhysicalResourceId'] = physical_resource_id or context.log_stream_name
    response_body['StackId'] = event['StackId']
    response_body['RequestId'] = event['RequestId']
    response_body['LogicalResourceId'] = event['LogicalResourceId']
    response_body['NoEcho'] = no_echo
    response_body['Data'] = response_data

    json_response_body = json.dumps(response_body)

    logging.warning("Response body:\n%s", json_response_body)

    headers = {
        'content-type': '',
        'content-length': str(len(json_response_body))
    }

    try:
        response = requests.put(response_url,
                                data=json_response_body,
                                headers=headers)
        logging.info("Status code: %s", response.reason)
    except Exception as exception:
        logging.critical("send(..) failed executing requests.put(..): %s", str(exception))


def entrypoint(event, context):
    """Handle lambda invocation"""
    success = "SUCCESS"
    failed = "FAILED"
    # Alternate way to get region if the event doesn't have it.
    # my_session = boto3.session.Session()
    # region = my_session.region_name
    region = event["ResourceProperties"]["region"]
    logging.warning("Using Region %s", region)
    default_vpc_id = get_default_vpc(region)

    response_data = {}
    if default_vpc_id == "":
        send(event, context, failed, response_data)
    else:
        response_data['DefaultVpcId'] = default_vpc_id
        send(event, context, success, response_data)
