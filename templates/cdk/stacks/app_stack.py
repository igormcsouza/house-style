import aws_cdk as cdk
from aws_cdk import aws_s3 as s3
from constructs import Construct


class AppStack(cdk.Stack):
    """Starter stack: one private, encrypted, versioned bucket. Add resources here; keep IAM least-privilege."""

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        self.bucket = s3.Bucket(
            self,
            "Data",
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            encryption=s3.BucketEncryption.S3_MANAGED,
            enforce_ssl=True,
            versioned=True,
            removal_policy=cdk.RemovalPolicy.RETAIN,
        )
