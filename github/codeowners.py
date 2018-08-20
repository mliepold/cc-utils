# Copyright (c) 2018 SAP SE or an SAP affiliate company. All rights reserved. This file is licensed
# under the Apache Software License, v. 2 except as noted otherwise in the LICENSE file
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
from pathlib import Path
from github3 import GitHub
from github3.exceptions import NotFoundError

from github.util import GitHubRepositoryHelper

from util import check_type, existing_dir, not_none, warning

# pylint: disable=no-member


class CodeownersParser(object):
    '''
    Parses GitHub CODEOWNSERS files [0] from the documented default locations for a given
    (git) repository work tree into a stream of codeowners entries.

    [0] https://help.github.com/articles/about-codeowners/
    '''

    def __init__(self, repo_dir=None, github_repo_helper: GitHubRepositoryHelper=None):
        if not (repo_dir is None) ^ (github_repo_helper is None):
            raise ValueError('exaxctly one of repo_dir, git_repo must be None')

        if repo_dir:
            self.repo_dir = existing_dir(Path(repo_dir).absolute())
            if not self.repo_dir.joinpath('.git').is_dir():
                raise ValueError('not a git root directory: {r}'.format(self.repo_dir))
            self._retrieve_filecontents = self._retrieve_filecontents_from_dir

        if github_repo_helper:
            self._github_repo_helper = check_type(github_repo_helper, GitHubRepositoryHelper)
            self._retrieve_filecontents = self._retrieve_filecontents_from_repo

    def _retrieve_filecontents_from_dir(self, rel_path):
       path = self.repo_dir.joinpath(rel_path)
       if path.is_file():
           yield from path.read_text().split('\n')

    def _retrieve_filecontents_from_repo(self, rel_path):
        try:
            yield from self._github_repo_helper.retrieve_text_file_contents(
                    file_path=rel_path
            ).split('\n')
        except NotFoundError:
            pass # ignore absent files

    def _codeowners_lines(self):
        root_codeowners = 'CODEOWNERS'
        dot_gh_codeowners = '.github/CODEOWNERS'
        docs_codeownsers = 'docs/CODEOWNSERS'

        for codeowners in (root_codeowners, dot_gh_codeowners, docs_codeownsers):
            yield from self._retrieve_filecontents(codeowners)

    def parse_codeowners_entries(self):
        '''
        returns a generator yielding parsed entries from */CODEOWNERS
        each entry may be one of
         - a github user name (with a leading @ character)
         - a github team name (leading @ character and exactly one / character (org/name))
         - an email address
        '''
        for line in self._codeowners_lines():
            line = line.strip()
            if line.startswith('#'):
                continue
            # first token is path filter (e.g. '*') - we ignore this for now
            github_ids = line.split(' ')[1:]

            # filter out empty strings (the empty string evaluates to False)
            yield from filter(bool, github_ids)
# pylint: enable=no-member


def _first(iterable):
    try:
        return next(iterable)
    except StopIteration:
        return None


class CodeOwnerEntryResolver(object):
    '''
    Resolves GitHub CODEOWNERS entries [0] into email addresses.

    The github3.py api object needs to be pre-authenticated with the privilege to read
    organisation and team memberhip data.

    [0] https://help.github.com/articles/about-codeowners/
    '''

    def __init__(self, github_api: GitHub):
        self.github_api = not_none(github_api)

    def _determine_email_address(self, github_user_name: str):
        not_none(github_user_name)
        user = self.github_api.user(github_user_name)
        return user.email

    def _resolve_team_members(self, github_team_name: str):
        not_none(github_team_name)
        org_name, team_name = github_team_name.split('/') # always of form 'org/name'
        organisation = self.github_api.organisation(org_name)
        # unfortunately, we have to look-up the team (no api to retrieve it by name)
        team_or_none = _first(filter(lambda team: team.name == team_name, organisation.teams()))
        if not team_or_none:
            warning('failed to lookup team {t}'.format(t=team_name))
            return []
        for member in team_or_none:
            if member.email:
                yield member.email

    def resolve_email_addresses(self, codeowners_entries):
        '''
        returns a generator yielding the resolved email addresses for the given iterable of
        github codeowners entries.
        '''
        for codeowner_entry in codeowners_entries:
            if '@' not in codeowner_entry:
                warning('invalid codeowners-entry: {e}'.format(codeowner_entry))
                continue
            if not codeowner_entry.startswith('@'):
                yield codeowner_entry # plain email address
            elif '/' not in codeowner_entry:
                email_addr = self._determine_email_address(codeowner_entry[1:])
                if email_addr:
                    yield email_addr
                else:
                    continue
            else:
                yield from self._resolve_team_members(codeowner_entry[1:])
