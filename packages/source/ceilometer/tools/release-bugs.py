#!/usr/bin/env python
# -*- encoding: utf-8 -*-
#
# Copyright © 2012 Graham Binns for Canonical
#
# Author: Graham Binns <graham.binns@gmail.com>
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

"""Command line tool for releasing Ceilometer bugs."""

import argparse
import sys

try:
    from launchpadlib.launchpad import Launchpad
    from launchpadlib.uris import LPNET_SERVICE_ROOT as SERVICE_ROOT
except ImportError:
    print "Can't import launchpadlib."
    sys.exit(1)


PROJECT_NAME = "ceilometer"
MESSAGE_TEMPLATE = "Released with milestone {milestone_title}."
PRE_RELEASE_STATUS = "Fix Released"
RELEASE_PROMPT = (
    "Found {bug_count} '{pre_release_status}' bugs for milestone "
    "{milestone_title}. Mark them 'Fix Released'? [y/n]: "
    )


def main():
    parser = argparse.ArgumentParser(
        description="Release Ceilometer bugs for a milestone.")
    parser.add_argument(
        '--milestone', help="The name of the milestone to release for.",
        required=True)
    args = parser.parse_args()

    lp = Launchpad.login_with(
        "ceilometer-bug-release-script", SERVICE_ROOT)
    the_project = lp.projects[PROJECT_NAME]
    milestone = lp.load(
        "%s/+milestone/%s" % (the_project.self_link, args.milestone))
    bugs_for_milestone = the_project.searchTasks(
        status=PRE_RELEASE_STATUS, milestone=milestone)
    bug_count = len(bugs_for_milestone)
    if bug_count == 0:
        print "No bugs to release for milestone %s" % milestone.name
        sys.exit(0)
    mark_released = raw_input(RELEASE_PROMPT.format(
        bug_count=bug_count,
        pre_release_status=PRE_RELEASE_STATUS,
        milestone_title=milestone.name))
    if mark_released.lower() != "y":
        print "Not releasing bugs."
        sys.exit(0)
    for bug_task in bugs_for_milestone:
        # We re-load the bugtask to avoid having bug 369293 bite us.
        bug_task = lp.load(bug_task.self_link)
        sys.stdout.write("Updating %s..." % bug_task.bug.id)
        bug_task.status = "Fix Released"
        bug_task.lp_save()
        bug_task.bug.newMessage(
            MESSAGE_TEMPLATE.format(milestone_title=milestone.title))
        sys.stdout.write("DONE\n")


if __name__ == '__main__':
    main()
