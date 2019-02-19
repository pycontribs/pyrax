Contributing to pyrax
=====================

Please create all pull requests against the 'master' branch.

For ease of testing, please ensure that the ``tox`` module is installed.

We follow PEP8 standards with the exception of line length of 84 characters.

When indenting continuation lines, the standard is 2 levels (i.e., 8
spaces). Please do not use "visual indentation", as it is fraught with
its own issues with consistency.

There are several other places where pyrax differs from the "pure" PEP8
suggestions. Please remember that PEP8 is a guideline, not an absolute
dictum. Here is the command I use to run the pep8 tool:

::

    tox -e pep8

Any pull requests to address style differences between the above command
and your interpretation of PEP8 will be rejected.

All changes other than simple typos should be accompanied by unit tests.
All changes must pass all unit tests. You can run the tests by running:

::

    tox

For consistency's sake, use double quotes to delimit strings unless the
strings contain double quote characters.

Pull Request Guidelines:

-  All pull requests should be a single commit, so that the changes can
   be observed and evaluated together. Here's the best way to make that
   happen:

   -  Pull from this repo's 'master' branch to your local repo. All
      pull requests *must* be against the 'master' branch.
   -  Create a local branch for making your changes:

      -  git checkout -b mychangebranch upstream/master

   -  Do all your testing, fixing, etc., in that branch. Make as many
      commits as you need as you work.
   -  When you've completed your changes, and have added your unit tests
      and made sure that everything's working great, merge it back into
      master using the '--squash' option so that it appears as a single
      commit.

      -  git checkout master
      -  git merge --squash mychangebranch
      -  git commit -am "Adds super powers to pyrax."
      -  git push origin master

   -  Now you have your changes in a single commit against your
      'master' branch on GitHub, and can create the pull request.
