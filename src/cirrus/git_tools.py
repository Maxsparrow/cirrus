#!/usr/bin/env python
"""
_git_tools_

Utils for doing git and github related business

"""
import os
import itertools

import git
import arrow

from cirrus.logger import get_logger
from cirrus._2to3 import unicode_


LOGGER = get_logger()


class RepoInitializer(object):
    """
    Helper class to initialise a repo from scratch with
    a master and develop branch plus remote syncing with
    origin and tracking


    """
    def __init__(self, repo=None):
        self.repo = git.Repo(repo)

    def check_origin(self, origin_name='origin'):
        """verify that origin exists in this repo"""
        return origin_name in [x.name for x in self.repo.remotes]

    def branch_exists_locally(self, branch):
        """check if branch exists locally"""
        return branch in self.repo.heads

    def branch_exists_origin(self, branch, origin='origin'):
        """check if branch exists at the origin"""
        if not self.branch_exists_locally(branch):
            return False
        if not self.check_origin(origin):
            return False
        tb = self.repo.heads[branch].tracking_branch()
        if not tb:
            return False
        return True

    def verify_branch(self, branch_name, origin_name='origin', remote=True):
        """
        standardise a branch/origin setup ensuring that a commit exists
        in a new repo
        """
        if remote and self.check_origin(origin_name):
            LOGGER.info("Fetching from {}".format(origin_name))
            self.repo.remotes[origin_name].fetch()
        if not self.branch_exists_locally(branch_name):
            LOGGER.info("creating new branch {}".format(branch_name))
            self.repo.git.commit(allow_empty=True, message="initialise repo")
            self.repo.create_head(branch_name, 'HEAD')
        else:
            LOGGER.info("checking out existing branch {}".format(branch_name))
            self.repo.git.checkout(branch_name)
        local_branch = self.repo.heads[branch_name]
        if remote:
            if not self.branch_exists_origin(branch_name, origin_name):
                LOGGER.info(
                    "Pushing {} to {}".format(branch_name, origin_name)
                )
                rem = self.repo.remotes[origin_name]
                ret = rem.push(branch_name)
                # Check to make sure that we haven't errored out.
                for r in ret:
                    if r.flags >= r.ERROR:
                        LOGGER.error("Unable to push to remote")
                        raise RuntimeError(unicode_(r.summary))
            tracking_branch = local_branch.tracking_branch()
            if not tracking_branch:
                LOGGER.info(
                    "Setting tracking branch for {}".format(
                        branch_name
                    )
                )
                rref = self.repo.remotes[origin_name].refs[branch_name]
                local_branch.set_tracking_branch(rref)
        else:
            LOGGER.info(
                "No remote option used, may need to git push {} {}".format(
                    origin_name, branch_name
                )
            )

    def branch_status(self):
        for head in self.repo.heads:
            LOGGER.info("local branch={} commit={} tracking={}".format(
                head.name, head.commit, head.tracking_branch()
                )
            )

    def init_branch(self, branch, origin='origin', remote=True):
        LOGGER.info("Initialising Repo Branch {}".format(branch))
        self.verify_branch(branch, origin, remote)
        self.branch_status()


def checkout_and_pull(repo_dir, branch_from, pull=True, origin='origin'):
    """
    _checkout_and_pull_

    Checkout a branch (branch_from) from a git repo (repo_dir)
    and then pull updates from origin

    returns a reference to the pulled branch
    """
    repo = git.Repo(repo_dir)

    if str(repo.active_branch) != branch_from:
        git.Git().checkout(branch_from)

    # pull branch_from from remote
    if pull:
        remote_branch = "remotes/{origin}/{branch}".format(
            origin=origin,
            branch=branch_from
        )
        ref = "refs/heads/{branch}:refs/{remote_branch}".format(
            branch=branch_from, remote_branch=remote_branch
        )
        branches = [
            str(x.strip())
            for x in repo.git.branch(all=True).split()
            if x.strip()
        ]
        if remote_branch not in branches:
            LOGGER.info(
                "couldnt find remote for {} in {}, skipping pull...".format(
                    branch_from,
                    branches
                )
            )
            return
        if origin in [x.name for x in repo.remotes]:
            return repo.remotes.origin.pull(ref)


def branch(repo_dir, branchname, branch_from):
    """
    _git_branch_

    Create a new branch off of branch_from, from repo, named
    branchname
    """
    repo = git.Repo(repo_dir)

    if branchname in repo.heads:
        msg = "Branch: {0} already exists.".format(branchname)
        LOGGER.info("{0} Checking it out...".format(msg))
        branch_ref = getattr(repo.heads, branchname)
        branch_ref.checkout()
    else:
        g = git.Git(repo_dir)
        g.checkout(branch_from, b=branchname)

    if not str(repo.active_branch) == branchname:
        msg = (
            "Error: Not able to checkout expected branch"
            "You are here -> {0}, "
            "you expected to be here -> {1}"
            ).format(repo.active_branch, branchname)
        LOGGER.error(msg)
        raise RuntimeError(msg)


def remote_branch_exists(repo_dir, branchname):
    """
    _remote_branch_exists_

    Check to see if the named branch exists on the
    origin remote. returns True/False

    """
    match = branchname
    if not match.startswith('origin/'):
        match = "origin/{}".format(str(branchname))
    repo = git.Repo(repo_dir)
    resp = repo.git.branch('-r')
    remote_branches = [y for y in resp.split() if y.startswith('origin/')]
    return match in remote_branches


def has_unstaged_changes(repo_dir):
    """
    _has_unstaged_changes_

    Are there changes to tracked files in the repo?
    Return True if so, False if it is clean
    """
    repo = git.Repo(repo_dir)
    output = repo.git.status(
        '--untracked-files=no',  '--porcelain'
    ).split()
    if output:
        return True
    return False


def current_branch(repo_dir):
    repo = git.Repo(repo_dir)
    return str(repo.active_branch)


def update_to_branch(branch, config, origin='origin'):
    """
    checkout specified branch, updating to pull in latest remotes

    """
    LOGGER.info(
        "selfupdate running, will switch to branch {0}".format(
            branch
        )
    )
    repo_dir = os.getcwd()

    LOGGER.info("fetching remotes...")
    r = git.Repo(repo_dir)
    r.remotes[origin].fetch()

    g = git.Git()
    LOGGER.info("checking out {0}...".format(branch))
    g.checkout('{0}/{1}'.format(origin, branch), b=branch)

    branch_ref = r.heads[branch]
    branch_ref.checkout()
    return


def update_to_tag(tag, config, origin='origin'):
    """
    checkout specified tag, pulling remote tags first
    """
    LOGGER.info(
        "selfupdate running, will switch to tag {0}".format(
            tag
        )
    )
    repo_dir = os.getcwd()

    LOGGER.info("fetching remote tags...")
    r = git.Repo(repo_dir)
    r.remotes[origin].fetch(tags=True)

    ref = r.tags[tag]
    LOGGER.info("checking out {0}...".format(tag))
    g = git.Git()
    g.checkout(ref)
    return


def commit_files_optional_push(repo_dir, commit_msg, push=True, *filenames):
    """
    commit files to the repo, push remote if required.

    """
    repo = git.Repo(repo_dir)
    repo.index.add(filenames)
    for f in filenames:
        if os.access(f, os.X_OK):
            LOGGER.info("Setting Executable bit on {}".format(f))
            repo.git.update_index(f, chmod='+x')
    # commits with message
    repo.index.commit(commit_msg)
    # push branch to origin
    if push:
        return repo.remotes.origin.push(repo.head)


def commit_files(repo_dir, commit_msg, *filenames):
    """
    _commit_files_

    Add the list of filenames and commit them with the message provided
    to the current branch in the repo specified.
    Pushes changes to remote branch after commit

    """
    return commit_files_optional_push(
        repo_dir, commit_msg, True, *filenames
    )


def push(repo_dir):
    """
    _push_

    Push local branch to remote
    """
    repo = git.Repo(repo_dir)
    ret = repo.remotes.origin.push(repo.head)
    # Check to make sure that we haven't errored out.
    for r in ret:
        if r.flags >= r.ERROR:
            raise RuntimeError(unicode_(r.summary))
    return ret


def tag_release(repo_dir, tag, master='master', push=True):
    """
    _tag_release_

    Checkout master, tag it and push tags

    Optionally, do not push the tag if push is False

    """
    checkout_and_pull(repo_dir, master, pull=push)
    repo = git.Repo(repo_dir)
    exists = any(existing_tag.name == tag for existing_tag in repo.tags)
    if exists:
        # tag already exists
        msg = (
            "Attempting to create tag {0} on "
            "{1} but tag exists already"
        ).format(tag, master)
        raise RuntimeError(msg)
    repo.create_tag(tag)
    if push:
        repo.remotes.origin.push(repo.head, tags=True)


def get_active_branch(repo_dir):
    """
    _active_branch_

    Returns active branch for a give directory
    """
    repo = git.Repo(repo_dir)
    return repo.active_branch


def merge(repo_dir, source, destination):
    """
    _merge_

    Merge source branch into destination branch

    :returns: sha of the last commit from the merged branch

    """
    repo = git.Repo(repo_dir)
    repo.git.checkout(source)

    ref = "refs/heads/{0}:refs/remotes/origin/{0}".format(source)
    repo.remotes.origin.pull(ref)
    repo.git.merge(destination)
    latest = repo.head.ref.commit.hexsha
    return latest


def get_diff_files(repo_dir):
    """
    _get_diff_files_

    Returns a list of paths to files that have been changed on
    the working directory
    """
    repo = git.Repo(repo_dir)
    changes = repo.index.diff(None)
    diffs = []
    for diff in changes:
        diffs.append(diff.a_blob.path)

    return diffs


def get_tags_with_sha(repo_dir):
    """
    _get_tags_with_sha_

    Get list of tags for a repo and return a map of
    tag:sha

    """
    repo = git.Repo(repo_dir)
    return {tag.name: tag.commit.hexsha for tag in repo.tags}


def get_tags(repo_dir):
    """
    _get_tags_

    returns a list of tags for the given repo, ordered as
    newest first

    """
    repo = git.Repo(repo_dir)
    tags_with_date = {
        tag.name: tag.commit.committed_date
        for tag in repo.tags
    }
    return sorted(tags_with_date, key=tags_with_date.get, reverse=True)


def get_commit_msgs(repo_dir, since_sha):
    """
    _get_commit_msgs_

    Get commit message data for the repo provided since the
    since_sha value of a commit or tag.

    """
    repo = git.Repo(repo_dir)
    rev_range = '..'.join([since_sha, repo.head.commit.hexsha])
    result = []
    for commit in repo.iter_commits(rev_range):
        row = {
            'committer': commit.committer.name,
            'message': commit.message,
            'date': str(arrow.get(commit.committed_date))
        }
        result.append(row)
    return result


def format_commit_messages(rows):
    """
    _format_commit_messages_

    Consume the data produced by get_commit_msgs and
    generate a set of release notes, broken down by author

    Output looks like:

    - Commit History:
    -- Author: USERAME
    --- DATETIME: COMMIT MESSAGE

    """
    result = [u" - Commit History:"]

    for author, commits in itertools.groupby(rows, lambda x: x['committer']):
        result.append(u" -- Author: {0}".format(author))
        sorted_commits = sorted(
            [c for c in commits],
            key=lambda x: x['date'],
            reverse=True
        )
        result.extend(
            u' --- {0}: {1}'.format(commit['date'], commit['message'])
            for commit in sorted_commits
        )

    return '\n'.join(result)


def markdown_format(rows):
    """
    _format_commit_messages_

    Consume the data produced by get_commit_msgs and
    generate a set of release notes, broken down by author

    Output looks like:

    Commit History
    ==============

    Author: USERNAME
    ----------------------

    DATETIME: COMMIT MESSAGE

    """
    result = ['Commit History\n==============']

    for author, commits in itertools.groupby(rows, lambda x: x['committer']):
        result.append(
            '\nAuthor: {0}\n--------'.format(author) + '-' * len(author))
        sorted_commits = sorted(
            [c for c in commits],
            key=lambda x: x['date'],
            reverse=True)
        result.extend('\n{0}: {1}'.format(
            commit['date'],
            commit['message']) for commit in sorted_commits)

    return '\n'.join(result)


FORMATTERS = {
    'plaintext': format_commit_messages,
    'markdown': markdown_format,
    }


def build_release_notes(repo_dir, since_tag, formatter):
    """
    Given a repo_dir and tag, generate release notes for all
    commits since that tag

    """
    tags = get_tags_with_sha(repo_dir)
    if since_tag not in tags:
        msg = "Could not find tag {0} in {1}".format(since_tag, repo_dir)
        raise RuntimeError(msg)

    sha = tags[since_tag]
    msgs = get_commit_msgs(repo_dir, sha)
    try:
        rel_notes = FORMATTERS[formatter](msgs)
    except Exception as ex:
        LOGGER.exception(ex)
        raise RuntimeError(
            ('Invalid release notes formatting: {0} Update cirrus.conf'
             ' entry to use either: plaintext, markdown'.format(formatter)))
    return rel_notes
