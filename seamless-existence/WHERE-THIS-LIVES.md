# Note on location

This directory is a mirror of a standalone project.  It sits on the branch
`claude/seamless-parametrization-necessary-rqepce` of the website repository only
because the session that produced it lacked permission to create a new GitHub
repository (`create_repository` returned 403).  Nothing here belongs to the
website, and this branch should not be merged into `main` -- the contents would be
published as part of the site.

To lift it out into its own repository, preserving the full history of the
standalone project, use the bundle produced alongside it, or simply:

    git init seamless-existence && cd seamless-existence
    # copy the files from this directory, then
    git add -A && git commit -m "Initial import"
    git remote add origin git@github.com:<you>/seamless-existence.git
    git push -u origin main
