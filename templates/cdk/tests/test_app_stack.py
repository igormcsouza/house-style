import aws_cdk as cdk
from aws_cdk.assertions import Match, Template

from stacks.app_stack import AppStack


def template() -> Template:
    return Template.from_stack(AppStack(cdk.App(), "Test"))


def test_bucket_is_private_encrypted_and_versioned():
    block_all = {
        "BlockPublicAcls": True,
        "BlockPublicPolicy": True,
        "IgnorePublicAcls": True,
        "RestrictPublicBuckets": True,
    }
    template().has_resource_properties(
        "AWS::S3::Bucket",
        {
            "PublicAccessBlockConfiguration": block_all,
            "BucketEncryption": Match.any_value(),
            "VersioningConfiguration": {"Status": "Enabled"},
        },
    )


def test_no_wildcard_iam_actions():
    for policy in template().find_resources("AWS::IAM::Policy").values():
        for stmt in policy["Properties"]["PolicyDocument"]["Statement"]:
            assert stmt["Action"] != "*"
