# Copyright (c) 2019-2020 SAP SE or an SAP affiliate company. All rights reserved. This file is
# licensed under the Apache Software License, v. 2 except as noted otherwise in the LICENSE file
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from ensure import ensure_annotations

import functools

import ci.util

from .api import ConcourseApiFactory
from model.concourse import ConcourseConfig, ConcourseUAMConfig, ConcourseUAM


'''
An implementation of the (undocumented [0]) RESTful HTTP API offered by concourse
[1]. It was reverse-engineered based on [2], as well using Chrome developer tools and
POST-Man [3].

Usage:
------

Users will probably want to create an instance of ConcourseApiVX, passing a
ConcourseConfig object to the `from_cfg` factory function.

Other types defined in this module are not intended to be instantiated by users.

[0] https://github.com/concourse/concourse/issues/1122
[1] https://concourse.ci
[2] https://github.com/concourse/concourse/blob/master/atc/routes.go
[3] https://www.getpostman.com/
'''


@functools.lru_cache()
@ensure_annotations
def from_cfg(
    concourse_cfg: ConcourseConfig,
    team_name: str,
    concourse_uam_cfg: ConcourseUAMConfig=None,
    verify_ssl=True,
    concourse_api_version=None,
):
    # XXX rm last dependency towards cfg-factory
    cfg_factory = ci.util.ctx().cfg_factory()
    base_url = concourse_cfg.ingress_url(cfg_factory)

    if not concourse_uam_cfg:
        concourse_uam_cfg = cfg_factory.concourse_uam(concourse_cfg.concourse_uam_cfg())
        import sys
        print('warning: omitting concourse_uam_cfg is deprecated!', file=sys.stderr)

    concourse_team = concourse_uam_cfg.team(team_name)
    team_name = concourse_team.teamname()
    username = concourse_team.username()
    password = concourse_team.password()

    concourse_api = ConcourseApiFactory.create_api(
        base_url=base_url,
        team_name=team_name,
        verify_ssl=verify_ssl,
        concourse_api_version=concourse_api_version,
    )

    concourse_api.login(
        username=username,
        passwd=password,
    )
    return concourse_api


@functools.lru_cache()
@ensure_annotations
def from_local_cc_user(
    base_url: str,
    local_cc_user: ConcourseUAM,
    verify_ssl=True,
    concourse_api_version=None,
):
    team_name = local_cc_user.name()
    username = local_cc_user.username()
    password = local_cc_user.password()

    concourse_api = ConcourseApiFactory.create_api(
        base_url=base_url,
        team_name=team_name,
        verify_ssl=verify_ssl,
        concourse_api_version=concourse_api_version,
    )

    concourse_api.login(
        username=username,
        passwd=password,
    )
    return concourse_api
