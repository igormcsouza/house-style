import aws_cdk as cdk

from stacks.app_stack import AppStack

app = cdk.App()
env = cdk.Environment(account=app.node.try_get_context("account"), region=app.node.try_get_context("region"))
AppStack(app, "AppStack", env=env)
cdk.Tags.of(app).add("project", app.node.try_get_context("project") or "app")
app.synth()
