#!/usr/bin/env python
from html.entities import name2codepoint
from constructs import Construct
from cdktf import App, TerraformStack
from imports.aws import AwsProvider
from imports.aws.kms import KmsAlias, KmsKey
from imports.aws.vpc import Route, RouteTable,RouteTableAssociation, Vpc, Subnet, InternetGateway, NatGateway, SecurityGroup, SecurityGroupIngress, SecurityGroupEgress
from imports.aws.ec2 import Instance, Eip, EbsVolume, VolumeAttachment
from imports.aws.sns import SnsTopic, SnsTopicSubscription
from imports.aws.s3 import S3Bucket, S3BucketServerSideEncryptionConfiguration, S3BucketServerSideEncryptionConfigurationRule,S3BucketServerSideEncryptionConfigurationRuleApplyServerSideEncryptionByDefault
from imports.aws.elb import Alb, AlbTargetGroup, AlbTargetGroupHealthCheck, AlbTargetGroupAttachment, AlbListenerDefaultAction, AlbListener
from imports.aws.cloudwatch import CloudwatchMetricAlarm, CloudwatchLogMetricFilter,CloudwatchLogMetricFilterMetricTransformation
from imports.aws.rds import DbInstance, DbSubnetGroup, RdsClusterInstanceTimeouts
from imports.aws.secretsmanager import SecretsmanagerSecret



class MyStack(TerraformStack):
    def __init__(self, scope: Construct, ns: str):
        super().__init__(scope, ns)

        AwsProvider(self, "AWS", region="us-east-1")

        # secretstoreDB = SecretsmanagerSecret(self, "secretstoreDB",
        # name = "rdsdatabase",
        # )

# Vpc
        myvpc = Vpc(self, "myvpc",
        cidr_block = "10.0.0.0/16",
        tags={"Name": "vpc-dev"},
        )
        
# InternetGateway

        ig_dev = InternetGateway(self, "ig_dev",
        depends_on=[myvpc],
        vpc_id= myvpc.id,
        tags = {"Name": "ig-dev"},
        )

# Subnets

        public1 = Subnet(self, "public1",
        depends_on= [myvpc],
        vpc_id = myvpc.id,
        cidr_block= '10.0.1.0/24',
        availability_zone = "us-east-1a",
        map_public_ip_on_launch = True,
        tags={"Name": "public1"},
        )
        public2 = Subnet(self, "public2",
        vpc_id = myvpc.id,
        depends_on=[myvpc],
        cidr_block= '10.0.2.0/24',
        availability_zone = "us-east-1b",
        map_public_ip_on_launch = True,
        tags={"Name": "public2"},
        )      

        routetablepublic = RouteTable(self, "routetablepublic",
        vpc_id = myvpc.id,
        depends_on=[ig_dev],
        tags= {"Name":"PubRoute"},
        )

        Route(self, "publicroute",
        route_table_id= routetablepublic.id,
        destination_cidr_block = "0.0.0.0/0",
        gateway_id = ig_dev.id,
        )

        routetableassociation_a = RouteTableAssociation(self,"routetableassociation_a",
        subnet_id = public1.id,
        route_table_id = routetablepublic.id,
        )
        routetableassociation_b = RouteTableAssociation(self,"routetableassociation_b",
        subnet_id = public2.id,
        route_table_id = routetablepublic.id,
        )

        private1 = Subnet(self, "private1",
        vpc_id= myvpc.id,
        depends_on= [myvpc],
        availability_zone = "us-east-1a",
        cidr_block= '10.0.3.0/24',
        map_public_ip_on_launch = False,
        tags={"Name": "private1"},
        )
        private2 = Subnet(self, "private2",
        vpc_id= myvpc.id,
        depends_on= [myvpc],
        availability_zone = "us-east-1b",
        cidr_block= '10.0.4.0/24',
        map_public_ip_on_launch = False,
        tags={"Name": "private2"},
        )
        
# Elastic_Ip

        eip_ip = Eip(self, "eip_ip",
        tags= {"Name":"EIP"},
        )

# Nategateway

        Nat_gateway = NatGateway(self, "Nat_gateway",
        depends_on= [ig_dev],
        allocation_id= eip_ip.id,
        subnet_id= public1.id,
        tags= {"Name":"NAT"},
        )

        routetableprivate = RouteTable(self, "routetableprivate",
        depends_on=[Nat_gateway],
        vpc_id = myvpc.id,
        tags= {"Name":"PriRoute"},
        )
        Route(self, "privateroute",
        route_table_id= routetableprivate.id,
        destination_cidr_block = "0.0.0.0/0",
        nat_gateway_id = Nat_gateway.id,
        )

        routetableassociation_c = RouteTableAssociation(self,"routetableassociation_c",
        subnet_id = private1.id,
        route_table_id = routetableprivate.id,
        )
        routetableassociation_d = RouteTableAssociation(self,"routetableassociation_d",
        subnet_id = private2.id,
        route_table_id = routetableprivate.id,
        )

# DataBase, security group, ds subnetgroup

        db_securitygroup_ingress = SecurityGroupIngress(
        from_port= 3306,
        to_port= 3306,
        protocol= "tcp",
        cidr_blocks = ["10.0.0.0/16"],
        )

        db_securitygroup_egress = SecurityGroupEgress(
        from_port = 0,
        to_port= 0,
        protocol= "-1",
        cidr_blocks = ["0.0.0.0/0"],       
        )


        db_securitygroup = SecurityGroup(self, "db_securitygroup",
        name = "dbsecuritygroup",
        ingress = [db_securitygroup_ingress],
        egress = [db_securitygroup_egress],
        vpc_id= myvpc.id,
        tags= {"Name":"sgdev"}
        )
        
        dbsubnet = DbSubnetGroup(self, "dbsubnet",
        name = "dbsubnet",
        subnet_ids= [private1.id, private2.id],
        tags= {"Name":"sbdev"},
        )

        dbinstance = DbInstance(self, "dbinstance",
        depends_on= [dbsubnet],
        identifier = "aws-d-database-1",
        db_subnet_group_name = dbsubnet.id,
        allocated_storage    = 10,
        engine               = "mysql",
        engine_version       = "8.0.23",
        instance_class       = "db.t2.micro",
        name                 = "mydb",  
        username             = "dev",
        password             = "12345678",
        # deletion_protection= True,
        # skip_final_snapshot = False,
        publicly_accessible = False,
        vpc_security_group_ids= [db_securitygroup.id],
        tags={"Name": "harish100"},
        )


# Ec2SecurityGroup
        
        ingress1 =  SecurityGroupIngress(
        from_port   = 22,
        to_port     = 22,
        protocol    = "tcp",
        cidr_blocks = ["0.0.0.0/0"],
        )
        ingress2 =  SecurityGroupIngress(
        from_port   = 80,
        to_port     = 80,
        protocol    = "tcp",
        cidr_blocks = ["0.0.0.0/0"],
        )
        egress = SecurityGroupEgress(
        from_port        = 0,
        to_port          = 0,
        protocol         = "-1",
        cidr_blocks      = ["0.0.0.0/0"],
        )

        ec2_securitygroup = SecurityGroup(self, "ec2_securitygroup",
        tags= {"Name":"ec2-securitygroup"},
        ingress= [ingress1, ingress2],
        egress= [egress],
        vpc_id = myvpc.id,
        )


# Ec2Instance

        ec2_instance = Instance(self, "ec2_instance",
        key_name= "dev",
        depends_on=[Nat_gateway, dbinstance],
        ami= "ami-0c02fb55956c7d316",
        instance_type= "t2.micro",
        iam_instance_profile= "ec2role",
        vpc_security_group_ids = [ec2_securitygroup.id],
        subnet_id= public1.id,
        tags={"Name": "harish100"},
        user_data = '''#!/usr/bin/env bash
        sudo -i
        yum update -y
        yum install python3-pip git mysql -y
        rpm -Uvh https://s3.amazonaws.com/amazoncloudwatch-agent/amazon_linux/amd64/latest/amazon-cloudwatch-agent.rpm
        sudo aws s3 cp s3://cloudwatchogs/config.json /opt/aws/amazon-cloudwatch-agent/config.json
        sudo /opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl -a fetch-config -m ec2 -s -c file:/opt/aws/amazon-cloudwatch-agent/config.json
        sudo /bin/systemctl restart amazon-cloudwatch-agent.service
        sudo git clone "https://github.com/Devsharma27/oneflask.git"
        sudo pip3 install flask
        sudo yum -y install python python3-devel mysql-devel redhat-rpm-config gcc
        sudo pip3 install flask_mysqldb
        sudo pip3 install mysql-connector-python
        cd oneflask
        python3 app.py'''
        )
# EBS
        ebsvolume = EbsVolume(self, "ebsvolume",
        depends_on= [ec2_instance],
        availability_zone = "us-east-1a",
        encrypted = False,
        size = 10,
        tags = {"Name":"EBSvolume"},
        )

        ebsvolumeattachment = VolumeAttachment(self, "volume_attachment",
        depends_on=[ebsvolume],
        instance_id = ec2_instance.id,
        volume_id = ebsvolume.id,
        device_name = "/dev/sdh",
        )

# TargetGroup

        ec2targetgroup = AlbTargetGroup(self,"ec2targetgroup",
        name= "ec2targetgroup",
        depends_on= [ec2_instance],
        vpc_id = myvpc.id,
        port = 80,
        protocol = 'HTTP',
        )

        health_check: AlbTargetGroupHealthCheck(self, "health_check",
        healthy_threshold   = 2,
        unhealthy_threshold = 2,
        timeout             = 3,
        target              = "HTTP:8000/",
        interval            = 30,
        )

        attachment = AlbTargetGroupAttachment(self, "attachment",
        target_group_arn = ec2targetgroup.arn,
        target_id        = ec2_instance.id,
        port             = 80,
        )

# LBsecuritygroup

        lb_ingress = SecurityGroupIngress(
        from_port   = 80,
        to_port     = 80,
        protocol    = "tcp",
        cidr_blocks = ["0.0.0.0/0"],
        )
        lb_egress = SecurityGroupEgress(
        from_port        = 0,
        to_port          = 0,
        protocol         = "-1",
        cidr_blocks      = ["0.0.0.0/0"],
        )
        
        lb_securitygroup = SecurityGroup(self, "lb_securitygroup",
        ingress = [lb_ingress],
        egress = [lb_egress],
        tags= {"Name":"lb-securitygroup"},
        vpc_id = myvpc.id,
        )

# LoadBalancer

        elb = Alb(self, "elb",
        depends_on= [ec2_instance],
        internal = False,
        load_balancer_type = "application",
        security_groups = [lb_securitygroup.id],
        subnets = [public1.id, public2.id],
        tags={"Name": "harish100"},
        )

# Lb Listener

        default_action = AlbListenerDefaultAction(
        type = "forward",
        target_group_arn = ec2targetgroup.arn,
        )

        listener = AlbListener(self, "listener",
        depends_on= [ec2_instance],
        port=80,
        protocol = "HTTP",
        default_action = [default_action],
        load_balancer_arn= elb.arn,
        )

# SNSTopic

        sns = SnsTopic(self, "sns",
        name= "alarms-dev",
        display_name='testing',
        tags={"Name":"sns-topic"},
        )

        subscription = SnsTopicSubscription(self, "subscription",
        depends_on= [sns],
        endpoint= "dev.sharma8989@gmail.com",
        protocol= "email",
        topic_arn= sns.arn,
        )

        CPUAlarm = CloudwatchMetricAlarm(self, "CPUAlarm",
        alarm_name= "CPUAlamm",
        alarm_description = "alert user if CPU touches 5%",
        alarm_actions = [sns.arn],
        ok_actions= [sns.arn],
        metric_name = "CPUUtilization",
        namespace =  "AWS/EC2",
        statistic = "Average",
        period = 10,
        evaluation_periods = 1,
        threshold = 5,
        comparison_operator = "LessThanThreshold",
        dimensions ={ "InstanceId": ec2_instance.id},
        )
        
        MemoryAlarm = CloudwatchMetricAlarm(self, "MemoryAlarm",
        alarm_name= "MemoryAlarm",
        alarm_description= "alert user if CPU touches 5%",
        alarm_actions = [sns.arn],
        ok_actions= [sns.arn],
        metric_name = "mem_used_percent",
        namespace =  "CWAgent",
        statistic = "Average",
        period = 10,
        evaluation_periods = 1,
        threshold = 5,
        comparison_operator = "LessThanThreshold",
        dimensions ={ "InstanceId": ec2_instance.id},
        )

        metric = CloudwatchLogMetricFilterMetricTransformation(
        name = "metric",
        namespace= "logfilter",  
        value= "1",
        )
        logfilter = CloudwatchLogMetricFilter(self, "logfilter",
        log_group_name = "dev.log",
        name= "logfilter",
        pattern= "dev",
        metric_transformation = metric,
        )

        InfoAlarm = CloudwatchMetricAlarm(self, "InfoAlarm",
        alarm_name= "logfilter",
        alarm_actions = [sns.arn],
        ok_actions= [sns.arn],
        metric_name = "metric",
        namespace  = "logfilter",
        statistic = "Sum",
        period = 10,
        evaluation_periods = 1,
        threshold = 0,
        datapoints_to_alarm = 1,
        comparison_operator = "GreaterThanOrEqualToThreshold",
        )

        kmskey = KmsKey(self, "kmskey",
        customer_master_key_spec = "SYMMETRIC_DEFAULT",)
        # policy = 

        #         {
        #             "Id": "key-consolepolicy-3",
        #             "Version": "2012-10-17",
        #             "Statement": [
        #         {
        #                     "Sid": "Enable IAM User Permissions",
        #                     "Effect": "Allow",
        #                     "Principal": {
        #                         "AWS": "arn:aws:iam::128680359488:root"
        #                     },
        #                     "Action": "kms:*",
        #                     "Resource": "*"
        #                 },
        #                 {
        #                     "Sid": "Allow access for Key Administrators",
        #                     "Effect": "Allow",
        #                     "Principal": {
        #                         "AWS": "arn:aws:iam::128680359488:user/dev"
        #                     },
        #                     "Action": [
        #                         "kms:Create*",
        #                         "kms:Describe*",
        #                         "kms:Enable*",
        #                         "kms:List*",
        #                         "kms:Put*",
        #                         "kms:Update*",
        #                         "kms:Revoke*",
        #                         "kms:Disable*",
        #                         "kms:Get*",
        #                         "kms:Delete*",
        #                         "kms:TagResource",
        #                         "kms:UntagResource",
        #                         "kms:ScheduleKeyDeletion",
        #                         "kms:CancelKeyDeletion"
        #                     ],
        #                     "Resource": "*"
        #                 },
        #                 {
        #                     "Sid": "Allow use of the key",
        #                     "Effect": "Allow",
        #                     "Principal": {
        #                         "AWS": "arn:aws:iam::128680359488:user/dev"
        #                     },
        #                     "Action": [
        #                         "kms:Encrypt",
        #                         "kms:Decrypt",
        #                         "kms:ReEncrypt*",
        #                         "kms:GenerateDataKey*",
        #                         "kms:DescribeKey"
        #                     ],
        #                     "Resource": "*"
        #                 },
        #                 {
        #                     "Sid": "Allow attachment of persistent resources",
        #                     "Effect": "Allow",
        #                     "Principal": {
        #                         "AWS": "arn:aws:iam::128680359488:user/dev"
        #                     },
        #                     "Action": [
        #                         "kms:CreateGrant",
        #                         "kms:ListGrants",
        #                         "kms:RevokeGrant"
        #                     ],
        #                     "Resource": "*",
        #                     "Condition": {
        #                         "Bool": {
        #                             "kms:GrantIsForAWSResource": "true"
        #                         }
        #                     }
        #                 }
        #             ]
        #         }
        # )

        alias = KmsAlias(self, "alias",
        name = "alias/my-key-alias",
        target_key_id = kmskey.id,
        )

#S3Bucket
        
        encryption = S3BucketServerSideEncryptionConfigurationRuleApplyServerSideEncryptionByDefault(
        sse_algorithm = "aws:kms",
        kms_master_key_id = kmskey.id,
        )
        encryptionrule = S3BucketServerSideEncryptionConfigurationRule(
                apply_server_side_encryption_by_default = encryption,
        )
        s3rule = S3BucketServerSideEncryptionConfiguration(
                rule = encryptionrule,
        )
        bucket = S3Bucket(self, "MyFirstBucket",
        acl = "private",
        server_side_encryption_configuration = s3rule, 
        )        

        

        

app = App()
stack = MyStack(app, "python-vpc")

app.synth()
s
