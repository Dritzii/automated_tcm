from aws_cdk import (
    Stack,
    aws_codebuild as codebuild,
    aws_codepipeline as codepipeline,
    aws_codepipeline_actions as codepipeline_actions,
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
        BucketKeyParam = CfnParameter(self, "lambdazip", default="approval.zip")
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
        artifact = codepipeline.Artifact("buildspec_artifact")
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
            bucket_key=BucketKeyParam.value_as_string,
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
                                            build_spec=codebuild.BuildSpec.from_source_filename(filename=""))

        build_action = codepipeline_actions.CodeBuildAction(
            action_name="CodeBuild",
            project=project,
            input=artifact,
            #outputs=[codepipeline.Artifact("automated-tcm")],
            execute_batch_build=True,
            combine_batch_build_artifacts=True,
            type=codepipeline_actions.CodeBuildActionType.TEST
        )

        pipeline.add_stage(stage_name='build', actions=[build_action])