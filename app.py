#!/usr/bin/env python3
import os

import aws_cdk as cdk

from automated_tcm.automated_tcm_stack import AutomatedTcmStack


app = cdk.App()
AutomatedTcmStack(app, "AutomatedTcmStack",
                  synthesizer=cdk.DefaultStackSynthesizer(generate_bootstrap_version_rule=False)
    )

app.synth()
