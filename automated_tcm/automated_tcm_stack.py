from aws_cdk import (
    Stack,
    aws_codebuild as codebuild,
    aws_codepipeline as codepipeline,
    aws_codepipeline_actions as pipeline_actions,
    aws_s3 as s3,
    aws_kms as kms,
    CfnParameter,
)
from aws_cdk.aws_iam import Role
from constructs import Construct

class AutomatedTcmStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        s3_bucket_location = CfnParameter(self, "s3bucket_name", default="ato-dis-infra-build-pipeline-outputs-devtest")
        source_bucket = s3.Bucket.from_bucket_name(self, 'test-pipeline-src-bucket', s3_bucket_location.value_as_string)
        zip_code = CfnParameter(self, "lambdazip", default="approval.zip")
        kms_alias = CfnParameter(self, "kms_alias", default="alias/KMS-DIS-DockerImageBuilder")

        admin_role = CfnParameter(self, "admin_cb_role",
                                  default="arn:aws:iam::830486629506:role/ato-role-dis-codesuite-admin")

        admin_role_arn = Role.from_role_arn(self, "ato-dis-cp-role", admin_role.value_as_string, mutable=False)

        kms_bucket = s3.Bucket.from_bucket_attributes(self,
                                                      id="ato-dis-kms-bucket",
                                                      bucket_name=source_bucket.bucket_name,
                                                      encryption_key=kms.Alias.from_alias_name(self,
                                                                                               id='kms-key-s3bucket',
                                                                                               alias_name=kms_alias.value_as_string))

        pipeline = codepipeline.Pipeline(self, 'dis-ram-pipe-testiac',
                                         pipeline_name='dis-ram-pipe-testiac',
                                         role=admin_role_arn,
                                         artifact_bucket=kms_bucket,
                                         cross_account_keys=False,
                                         reuse_cross_region_support_stacks=False,
                                         enable_key_rotation=False,
                                         restart_execution_on_update=False,
                                         # pipeline_type=codepipeline.PipelineProps.V1
                                         )

        # we pull git repo from ADO mygovid to run unit tests
        codebuild.PipelineProject(self, "DIS-automated-tcm",
                          build_spec=codebuild.BuildSpec.from_object({
                              "version": "0.2",
                              "phases": {
                                  "build": {
                                      "commands": ["echo \"Hello, CodeBuild!\""
                                                   ]
                                  }
                              }
                          })
                          )
