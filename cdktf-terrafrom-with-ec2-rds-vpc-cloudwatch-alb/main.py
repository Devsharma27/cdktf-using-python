#!/usr/bin/env python
from constructs import Construct
from cdktf import App, TerraformStack
from imports.aws import AwsProvider
from imports.aws.vpc import Route, RouteTable,RouteTableAssociation, Vpc, Subnet, InternetGateway, NatGateway, SecurityGroup, SecurityGroupIngress, SecurityGroupEgress
from imports.aws.ec2 import Instance, Eip, EbsVolume, VolumeAttachment
from imports.aws.sns import SnsTopic, SnsTopicSubscription
from imports.aws.s3 import S3Bucket, S3AccessPointPublicAccessBlockConfiguration
from imports.aws.elb import Alb, AlbTargetGroup, AlbTargetGroupHealthCheck, AlbTargetGroupAttachment, AlbListenerDefaultAction, AlbListener
from imports.aws.cloudwatch import CloudwatchMetricAlarm
from imports.aws.rds import DbInstance, DbSubnetGroup


class MyStack(TerraformStack):
    def __init__(self, scope: Construct, ns: str):
        super().__init__(scope, ns)

        AwsProvider(self, "AWS", region="us-east-1")

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
        deletion_protection= False,
        # skip_final_snapshot = False,
        publicly_accessible = False,
        vpc_security_group_ids= [db_securitygroup.id],
        tags = {"Name":"dbdev"},
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
        subnet_id= private1.id,
        tags={"Name": "ec2-instance"},
        # user_data = '''#!/usr/bin/env bash\nsudo -i\nyum update -y\nyum install python3-pip git mysql -y\nrpm -Uvh https://s3.amazonaws.com/amazoncloudwatch-agent/amazon_linux/amd64/latest/amazon-cloudwatch-agent.rpm\nsudo aws s3 cp s3://cloudwatchogs/config.json /opt/aws/amazon-cloudwatch-agent/config.json\nsudo /opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl -a fetch-config -m ec2 -s -c file:/opt/aws/amazon-cloudwatch-agent/config.json\nsudo /bin/systemctl restart amazon-cloudwatch-agent.service\nsudo git clone "https://github.com/Devsharma27/flaskapp.git"\nsudo pip3 install flask\nsudo yum -y install python python3-devel mysql-devel redhat-rpm-config gcc\nsudo pip3 install flask_mysqldb\nsudo pip3 install mysql-connector-python\ncd flaskapp\npython3 app.py\n'''
        # user_data='''#!/usr/bin/env bash\nsudo -i\nyum update -y\nyum install httpd.x86_64 -y\nsystemctl start httpd.service\nsystemctl start httpd.service'''
        user_data = '''#!/usr/bin/env bash\nsudo -i\nyum update -y\nyum install python3-pip git mysql -y\nrpm -Uvh https://s3.amazonaws.com/amazoncloudwatch-agent/amazon_linux/amd64/latest/amazon-cloudwatch-agent.rpm\nsudo aws s3 cp s3://cloudwatchogs/config.json /opt/aws/amazon-cloudwatch-agent/config.json\nsudo /opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl -a fetch-config -m ec2 -s -c file:/opt/aws/amazon-cloudwatch-agent/config.json\nsudo /bin/systemctl restart amazon-cloudwatch-agent.service\nsudo git clone "https://github.com/Devsharma27/oneflask.git"\nsudo pip3 install flask\nsudo yum -y install python python3-devel mysql-devel redhat-rpm-config gcc\nsudo pip3 install flask_mysqldb\nsudo pip3 install mysql-connector-python\ncd oneflask\npython3 app.py\n'''
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
        tags= {"Name":"elb-dev"},
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
        display_name='my-first-sns-topic',
        tags={"Name":"snstopic"},
        )
        subscription = SnsTopicSubscription(self, "subscription",
        endpoint= "dev.sharma8989@gmail.com",
        protocol= "email",
        topic_arn= sns.arn,
        )

# Cloudwatch Alram

        CPUAlarm = CloudwatchMetricAlarm(self, "CPUAlarm",
        alarm_name= "CPUAlram",
        alarm_description = "alert user if CPU touches 30%",
        # alarm_actions = [subscription.id],
        metric_name = "CPUUtilization",
        namespace =  "AWS/EC2",
        statistic = "Average",
        period = 900,
        evaluation_periods = 1,
        threshold = 30,
        comparison_operator = "GreaterThanOrEqualToThreshold",
        dimensions ={ "Name": "ec2_instance", 
            "Value": "ec2_instance"},
        )
        
        MemoryAlarm = CloudwatchMetricAlarm(self, "MemoryAlarm",
        alarm_name= "MemoryAlram",
        alarm_description= "alert user if CPU touches 30%",
        # alarm_actions= [subscription.id],
        metric_name = "mem_used_percent",
        namespace =  "CWAgent",
        statistic = "Average",
        period = 900,
        evaluation_periods = 1,
        threshold = 30,
        comparison_operator = "GreaterThanOrEqualToThreshold",
        dimensions ={"Name": "ec2_instance", 
            "Value": "ec2_instance"},
        )

#S3Bucket
 
        bucket = S3Bucket(self, "MyFirstBucket",
        )

app = App()
stack = MyStack(app, "python-vpc")

app.synth()
