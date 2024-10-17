from aws_cdk import (
    Stack,
    aws_codebuild as codebuild,
    aws_codepipeline as codepipeline,
    aws_codepipeline_actions as codepipeline_actions,
    aws_s3 as s3,
    aws_kms as kms,
    aws_lambda as _lambda,
    CfnParameter,
    Duration,
    aws_ec2
)
from aws_cdk.aws_iam import Role
from constructs import Construct

class AutomatedTcmStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        s3_bucket_location = CfnParameter(self, "s3bucket_name", default="ato-dis-infra-build-pipeline-outputs-devtest")
        source_bucket = s3.Bucket.from_bucket_name(self, 'test-pipeline-src-bucket', s3_bucket_location.value_as_string)
        bucket_key_param = CfnParameter(self, "vssln.zip", default="vssln.zip")
        kms_alias = CfnParameter(self, "kms_alias", default="alias/KMS-DIS-DockerImageBuilder")
        existing_role_arn = CfnParameter(self, "lambda_role",
                                         default="arn:aws:iam::830486629506:role/ato-role-dis-testiac-lambda")
        existing_role = Role.from_role_arn(self, "ato-dis-stack_details_lambda", existing_role_arn.value_as_string,
                                           mutable=False)
        admin_role = CfnParameter(self, "admin_cb_role")
        admin_role_arn = Role.from_role_arn(self, "ato-dis-cp-role", admin_role.value_as_string, mutable=False)
        jinja = CfnParameter(self, "jinja", default="jinja.zip")
        matplotlib = CfnParameter(self, "matplotlib", default="matplotlib.zip")
        s3_bucket_location_reports = CfnParameter(self, "s3bucket_name_reports",
                                                  default="ato-dis-infra-build-pipeline-outputs-devtest")
        zip_code = CfnParameter(self, "lambdazip", default="approval.zip")
        subnet = CfnParameter(self, "subnet_list", default="['subnet-0fb54d79' , 'subnet-0c03b384cc7d98682']")
        vpcid = CfnParameter(self, 'vpc-6bcfd80e')
        canarysg = CfnParameter(self, 'sg-0932df5016b614b95')
        SGobj = [aws_ec2.SecurityGroup.from_security_group_id(self, 'sg', security_group_id=canarysg.value_as_string)]
        Vpcobj = aws_ec2.Vpc.from_vpc_attributes(self, 'vpc', availability_zones=['ap-southeast-2a', 'ap-southeast-2b'],
                                                 vpc_id=vpcid.value_as_string)
        """Subnetobj = aws_ec2.SubnetSelection(subnets=[aws_ec2.Subnet.from_subnet_id(self, "lambda-subnet0",
                                                                                   subnet.value_as_string.split()[0]),
                                                      aws_ec2.Subnet.from_subnet_id(self, "lambda-subnet1",
                                                                                   subnet.value_as_string.split()[1])])"""
        kms_bucket = s3.Bucket.from_bucket_attributes(self,
                                                      id="ato-dis-kms-bucket",
                                                      bucket_name=source_bucket.bucket_name,
                                                      encryption_key=kms.Alias.from_alias_name(self,
                                                                                               id='kms-key-s3bucket',
                                                                                               alias_name=kms_alias.value_as_string))
        # Layers
        self.jinja_layer = _lambda.LayerVersion(self, "DIS-jinjaLayer",
                                                code=_lambda.Code.from_bucket(bucket=kms_bucket,
                                                                              key=jinja.value_as_string),
                                                compatible_runtimes=[_lambda.Runtime.PYTHON_3_11,
                                                                     _lambda.Runtime.PYTHON_3_10,
                                                                     _lambda.Runtime.PYTHON_3_9,
                                                                     _lambda.Runtime.PYTHON_3_8])
        self.matplot_lib_layer = _lambda.LayerVersion(self, "DIS-matplotlibLayer",
                                                      code=_lambda.Code.from_bucket(bucket=kms_bucket,
                                                                                    key=matplotlib.value_as_string),
                                                      compatible_runtimes=[_lambda.Runtime.PYTHON_3_11,
                                                                           _lambda.Runtime.PYTHON_3_10,
                                                                           _lambda.Runtime.PYTHON_3_9,
                                                                           _lambda.Runtime.PYTHON_3_8])

        # Lambda
        TestFrameworkLambda_generate_html = _lambda.Function(self, "ato-dis-generate_report",
                                                             runtime=_lambda.Runtime.PYTHON_3_11,
                                                             handler="report_handler.handler",
                                                             code=_lambda.Code.from_bucket(bucket=kms_bucket,
                                                                                           key=zip_code.value_as_string),
                                                             environment={
                                                                 "s3_bucket": s3_bucket_location.value_as_string,
                                                                 "s3_bucket_reports": s3_bucket_location_reports.value_as_string,
                                                                 "config": "config.json",
                                                                 "ARTIFACTORY_SVC_USER": "udfh8",
                                                                 "ARTIFACTORY_SVC_USER_TOKEN": "cmVmdGtuOjAxOjE3NTAxMjY4NDY6S2M2RUZzTkx5TndsZUN1azR1cms0TlpIeU0x",
                                                                 "ARTIFACTORY_ENDPOINT": "https://artifactory.ctz.atocnet.gov.au",
                                                                 "ARTIFACTORY_REPO_STORAGE_PATH": "/artifactory/disolution-generic-release-local/AWS/Reports/"
                                                             },
                                                             timeout=Duration.minutes(10),
                                                             memory_size=10240,
                                                             role=existing_role,
                                                             layers=[self.jinja_layer, self.matplot_lib_layer],
                                                          #   vpc=Vpcobj,
                                                            # vpc_subnets=Subnetobj,
                                                          #   security_groups=SGobj,
                                                             )

        artifact = codepipeline.Artifact("buildspec_artifact")
        tcm = codepipeline.Artifact("automated-tcm")
        # codepipeline
        pipeline = codepipeline.Pipeline(self, 'dis-automated_tcm-mygovid',
                                         pipeline_name='dis-mygov-automated-tcm',
                                         role=admin_role_arn,
                                         artifact_bucket=kms_bucket,
                                         cross_account_keys=False,
                                         reuse_cross_region_support_stacks=False,
                                         enable_key_rotation=False,
                                         restart_execution_on_update=False,
                                         # pipeline_type=codepipeline.PipelineProps.V1
                                         )
        pipeline.add_stage(stage_name='Source', actions=[codepipeline_actions.S3SourceAction(
            action_name='S3Source',
            bucket=kms_bucket,
            bucket_key=bucket_key_param.value_as_string,
            output=artifact,
            role=admin_role_arn,
            trigger=codepipeline_actions.S3Trigger.POLL)])

        # init a cb project , we add the details here for the buildspec
        project = codebuild.PipelineProject(self, "DIS-automated-TCM",
                                            role=admin_role_arn,
                                            encryption_key=kms.Alias.from_alias_name(self,
                                                                     "codepipelinekmskeyalias",
                                                                     alias_name=kms_alias.value_as_string),
                                            project_name="dis-automated-tcm",
                                            build_spec=codebuild.BuildSpec.from_source_filename(filename="/mnt/49bb6cd3-a5bf-468d-b67a-f4dd29190808/GIT/automated_tcm/buildspec/buildspec.yml"))

        build_action = codepipeline_actions.CodeBuildAction(
            action_name="CodeBuild",
            project=project,
            input=artifact,
            outputs=[tcm],
            execute_batch_build=True,
            combine_batch_build_artifacts=True,
            type=codepipeline_actions.CodeBuildActionType.TEST
        )

        pipeline.add_stage(stage_name='build_test', actions=[build_action])
        pipeline.add_stage(stage_name='build_report', actions=[
            codepipeline_actions.LambdaInvokeAction(
                action_name="GenerateReport",
                lambda_=TestFrameworkLambda_generate_html,
                role=admin_role_arn,
                run_order=1,
            ),])