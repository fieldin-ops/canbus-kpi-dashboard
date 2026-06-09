#!/bin/bash
export PATH="/usr/local/bin:/usr/bin:/bin:/Users/mac/Downloads/google-cloud-sdk/bin:/tmp/gh/gh_2.74.0_macOS_arm64/bin"
export CLOUDSDK_CORE_ACCOUNT="tyizhak@fieldintech.com"
export CLOUDSDK_CORE_PROJECT="poodle-359607"

/tmp/gh/gh_2.74.0_macOS_arm64/bin/gh auth setup-git 2>/dev/null

/usr/local/bin/python3 /Users/mac/Projects/canbus-kpi-dashboard/collect.py
